"""ICV runner: test a submitted structural claim against matched controls.

The core service, and the thing we did to ourselves: take a claim, build
deliberately-wrong-but-matched variants, and see where the real one ranks.

Submission format (JSON):
{
  "submission_id": "acme-001",
  "claimant": "Acme Research",
  "claim": "our wiring reaches the target faster than alternatives",
  "graph":     {"edges": [[0,1],[1,2], ...]},
  "endpoints": {"start": 0, "goal": 30},
  "metric": "endpoint_distance" | "quotient_cells",
  "objective": "minimise" | "maximise",
  "claimed_value": 6,
  "success_rule": {"type": "rank_at_most", "value": 10},
  "controls": 200
}

Standard library only. Read-only with respect to the submission.

Usage:
    python icv_runner.py submissions/example-eog-claim.json
    python icv_runner.py submissions/example-eog-claim.json --write-verdict
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
from collections import deque

REQUIRED = ('submission_id', 'claimant', 'claim', 'graph', 'endpoints',
            'metric', 'objective', 'claimed_value', 'success_rule')
METRICS = ('endpoint_distance', 'quotient_cells')


class SubmissionError(ValueError):
    """Submission is not testable as supplied."""


# ---------------------------------------------------------------- intake

def load(path: pathlib.Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        sub = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SubmissionError('not valid UTF-8 JSON: %s' % exc) from exc
    missing = [k for k in REQUIRED if k not in sub]
    if missing:
        raise SubmissionError('missing fields: %s' % ', '.join(missing))
    if sub['metric'] not in METRICS:
        raise SubmissionError('metric %r not supported; use one of %s'
                              % (sub['metric'], list(METRICS)))
    if sub['objective'] not in ('minimise', 'maximise'):
        raise SubmissionError('objective must be minimise or maximise')
    edges = sub['graph'].get('edges')
    if not edges:
        raise SubmissionError('graph.edges is empty or absent')
    return sub, digest


def to_adj(edges) -> dict:
    adj = {}
    for e in edges:
        if len(e) != 2:
            raise SubmissionError('edge %r is not a pair' % (e,))
        a, b = e
        if a == b:
            raise SubmissionError('self-loop at %r' % (a,))
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return adj


# ---------------------------------------------------------------- metrics

def endpoint_distance(adj, start, goal):
    if start not in adj or goal not in adj:
        return None
    if start == goal:
        return 0
    seen, q = {start}, deque([(start, 0)])
    while q:
        x, d = q.popleft()
        for y in adj[x]:
            if y == goal:
                return d + 1
            if y not in seen:
                seen.add(y)
                q.append((y, d + 1))
    return None


def quotient_cells(adj, seeds):
    """Endpoint-seeded exact equitable refinement; returns stable cell count."""
    colour = {v: 0 for v in adj}
    for i, s in enumerate(seeds, start=1):
        if s in colour:
            colour[s] = i
    while True:
        sig = {}
        for v in adj:
            counts = {}
            for w in adj[v]:
                counts[colour[w]] = counts.get(colour[w], 0) + 1
            sig[v] = (colour[v], tuple(sorted(counts.items())))
        groups = {}
        for v, s in sig.items():
            groups.setdefault(s, []).append(v)
        if len(groups) == len(set(colour.values())):
            return len(groups)          # partition stable
        new = {}
        for i, key in enumerate(sorted(groups, key=str)):
            for v in groups[key]:
                new[v] = i
        colour = new


def measure(adj, sub):
    if sub['metric'] == 'endpoint_distance':
        return endpoint_distance(adj, sub['endpoints']['start'],
                                 sub['endpoints']['goal'])
    return quotient_cells(adj, [sub['endpoints']['start'], sub['endpoints']['goal']])


# ---------------------------------------------------------------- controls

def rewire(edges, rng, swaps):
    """Degree-preserving double-edge swaps: a matched control, same degrees."""
    e = [tuple(x) for x in edges]
    eset = {frozenset(x) for x in e}
    done = 0
    for _ in range(swaps * 20):
        if done >= swaps:
            break
        i, j = rng.randrange(len(e)), rng.randrange(len(e))
        if i == j:
            continue
        (a, b), (c, d) = e[i], e[j]
        if len({a, b, c, d}) < 4:
            continue
        n1, n2 = frozenset((a, d)), frozenset((c, b))
        if n1 in eset or n2 in eset:
            continue
        eset.discard(frozenset(e[i]))
        eset.discard(frozenset(e[j]))
        e[i], e[j] = (a, d), (c, b)
        eset.add(n1)
        eset.add(n2)
        done += 1
    return e, done


# ---------------------------------------------------------------- report

def run(sub: dict, digest: str, seed: int = 20260817) -> dict:
    adj = to_adj(sub['graph']['edges'])
    observed = measure(adj, sub)
    if observed is None:
        raise SubmissionError('metric could not be computed; endpoints may be '
                              'absent or unreachable')

    claimed = sub['claimed_value']
    claim_ok = (observed == claimed)

    rng = random.Random(seed)
    n_ctl = int(sub.get('controls', 200))
    n_swaps = max(1, len(sub['graph']['edges']) // 2)
    values, degenerate = [], 0
    for _ in range(n_ctl):
        cedges, done = rewire(sub['graph']['edges'], rng, n_swaps)
        if done == 0:
            degenerate += 1
            continue
        cadj = to_adj(cedges)
        v = measure(cadj, sub)
        if v is not None:
            values.append(v)

    minimise = sub['objective'] == 'minimise'
    beat = sum(1 for v in values if (v < observed) if minimise) if minimise \
        else sum(1 for v in values if v > observed)
    ties = sum(1 for v in values if v == observed)
    worse = len(values) - beat - ties
    rank = beat + 1
    total = len(values) + 1

    # distinctiveness: rank alone misleads when ties dominate the field
    mob = beat + ties
    mob_pct = (mob / len(values)) if values else 1.0
    if mob_pct >= 0.50:
        dist_res = 'FAIL'
    elif mob_pct >= 0.20:
        dist_res = 'PARTIAL'
    else:
        dist_res = 'PASS'
    saturated = (beat == 0 and ties > 0 and mob_pct >= 0.20)

    rule = sub['success_rule']
    if rule.get('type') == 'rank_at_most':
        passed = rank <= int(rule['value'])
        rule_text = 'rank <= %s' % rule['value']
    else:
        passed = None
        rule_text = 'unsupported rule %r' % rule.get('type')

    srt = sorted(values)
    spread = ('controls ranged %s to %s, median %s'
              % (srt[0], srt[-1], srt[len(srt) // 2])) if srt else 'no controls measured'

    checks = {
        'intake_wellformed': {
            'result': 'PASS',
            'detail': 'valid UTF-8 JSON, all required fields present, %d edges, '
                      'sha256 %s' % (len(sub['graph']['edges']), digest[:16]),
        },
        'claim_reproduced': {
            'result': 'PASS' if claim_ok else 'FAIL',
            'detail': 'claimed %s = %s; independently measured %s'
                      % (sub['metric'], claimed, observed),
        },
        'matched_controls': {
            'result': 'PASS' if len(values) >= max(10, n_ctl // 2) else 'PARTIAL',
            'detail': '%d degree-preserving control variants built and measured'
                      ' (%d rewiring attempts produced no valid swap). %s'
                      % (len(values), degenerate, spread),
        },
        'control_ranking': {
            'result': 'PASS' if passed else ('FAIL' if passed is False else 'NOT_RUN'),
            'detail': 'rank %d of %d (%d better, %d tied, %d worse); rule: %s'
                      % (rank, total, beat, ties, worse, rule_text),
        },
        'distinctiveness': {
            'result': dist_res,
            'detail': '%d%% of controls matched or beat this result%s'
                      % (round(mob_pct * 100),
                         ('. The specific arrangement is NOT what produces the value; '
                          'most rewirings achieve it too'
                          + (', and no control can beat it because the value is already '
                             'at the achievable limit, so rank is uninformative here'
                             if saturated else '') + '.')
                         if dist_res == 'FAIL' else
                         ('. A substantial share of the field matches it, so the '
                          'arrangement is only weakly responsible.')
                         if dist_res == 'PARTIAL' else
                         '. The arrangement, not the graph in general, produces the result.'),
        },
    }

    if not claim_ok:
        verdict = 'FALSIFIED'
    elif passed is False:
        verdict = 'FALSIFIED'
    elif passed is None:
        verdict = 'INCONCLUSIVE'
    elif dist_res == 'FAIL':
        verdict = 'NOT_DISTINCTIVE'
    else:
        verdict = 'SUPPORTED'

    if verdict == 'NOT_DISTINCTIVE':
        plain = ('Rank %d of %d, but %d%% of controls matched or beat it. '
                 'Passing the rank rule here means little.'
                 % (rank, total, round(mob_pct * 100)))
    elif verdict == 'FALSIFIED' and not claim_ok:
        plain = ('The claimed value did not reproduce: claimed %s, measured %s.'
                 % (claimed, observed))
    else:
        plain = ('Ranked %d of %d against matched controls; %d%% matched or beat it.'
                 % (rank, total, round(mob_pct * 100)))

    return {
        'schema_version': 'icv-verdict/1.0',
        'engagement_id': sub['submission_id'],
        'client': sub['claimant'],
        'claim': sub['claim'],
        'verdict': verdict,
        'verdict_plain': plain,
        'checks': checks,
        'submission_sha256': digest,
        'boundary': 'Structural ranking against degree-preserving controls only. '
                    'Establishes no advantage, novelty or fitness for purpose.',
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Test a submitted structural claim.')
    ap.add_argument('submission')
    ap.add_argument('--write-verdict', action='store_true',
                    help='save verdict.json into engagements/<id>/')
    ap.add_argument('--seed', type=int, default=20260817)
    args = ap.parse_args(argv)

    path = pathlib.Path(args.submission)
    try:
        sub, digest = load(path)
        report = run(sub, digest, args.seed)
    except SubmissionError as exc:
        print('NOT TESTABLE: %s' % exc)
        return 2

    print('submission : %s' % report['engagement_id'])
    print('claimant   : %s' % report['client'])
    print('claim      : %s' % report['claim'])
    print('sha256     : %s' % digest)
    print()
    for name, body in report['checks'].items():
        print('  [%-7s] %-22s %s' % (body['result'], name, body['detail']))
    print()
    print('VERDICT: %s  -  %s' % (report['verdict'], report['verdict_plain']))

    if args.write_verdict:
        out = pathlib.Path(__file__).resolve().parent / 'engagements' / report['engagement_id']
        out.mkdir(parents=True, exist_ok=True)
        (out / 'verdict.json').write_text(
            json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print('wrote %s' % (out / 'verdict.json'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
