"""ICV Lab dashboard generator.

Scans engagements/, validates each verdict.json against the minimal ICV schema,
and writes dashboard.json plus a dependency-free dashboard.html.

Standard library only. Read-only with respect to engagement data: it never
edits, moves or deletes a verdict. Fails closed on malformed input rather than
silently rendering an optimistic dashboard.

Usage:
    python icv_dashboard.py [--root DIR] [--out DIR] [--strict]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import pathlib
import sys

SCHEMA = 'icv-verdict/1.0'
REQUIRED = ('schema_version', 'engagement_id', 'client', 'claim', 'verdict', 'checks')
CHECK_RESULTS = {'PASS', 'FAIL', 'PARTIAL', 'NOT_RUN'}
VERDICTS = {'FALSIFIED', 'SUPPORTED', 'INCONCLUSIVE', 'OPEN'}
BADGE = {'PASS': 'ok', 'FAIL': 'bad', 'PARTIAL': 'warn', 'NOT_RUN': 'idle'}


class VerdictError(ValueError):
    """Raised when a verdict file is not usable."""


def load_verdict(path: pathlib.Path) -> dict:
    try:
        raw = path.read_text(encoding='utf-8')
    except OSError as exc:
        raise VerdictError('unreadable: %s' % exc) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VerdictError('invalid JSON: %s' % exc) from exc
    if not isinstance(data, dict):
        raise VerdictError('top level must be an object')
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        raise VerdictError('missing required fields: %s' % ', '.join(missing))
    if data['schema_version'] != SCHEMA:
        raise VerdictError('unsupported schema_version %r, expected %r'
                           % (data['schema_version'], SCHEMA))
    if data['verdict'] not in VERDICTS:
        raise VerdictError('verdict %r not in %s' % (data['verdict'], sorted(VERDICTS)))
    checks = data['checks']
    if not isinstance(checks, dict) or not checks:
        raise VerdictError('checks must be a non-empty object')
    for name, body in checks.items():
        if not isinstance(body, dict) or 'result' not in body:
            raise VerdictError('check %r must be an object with a result' % name)
        if body['result'] not in CHECK_RESULTS:
            raise VerdictError('check %r has result %r not in %s'
                               % (name, body['result'], sorted(CHECK_RESULTS)))
    return data


def scan(root: pathlib.Path) -> tuple[list[dict], list[tuple[str, str]]]:
    rows, errors = [], []
    if not root.is_dir():
        return rows, [(str(root), 'engagements directory not found')]
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        vf = d / 'verdict.json'
        if not vf.is_file():
            errors.append((d.name, 'no verdict.json'))
            continue
        try:
            rows.append(load_verdict(vf))
        except VerdictError as exc:
            errors.append((d.name, str(exc)))
    return rows, errors


def summarize(rows: list[dict]) -> dict:
    tally: dict[str, int] = {}
    checks_failed = 0
    for r in rows:
        tally[r['verdict']] = tally.get(r['verdict'], 0) + 1
        checks_failed += sum(1 for c in r['checks'].values() if c['result'] == 'FAIL')
    return {
        'engagements': len(rows),
        'by_verdict': tally,
        'total_failed_checks': checks_failed,
        'generated_utc': _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
    }


CSS = """
body{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:32px;
background:#0f1115;color:#e6e6e6}
h1{font-size:22px;margin:0 0 4px}
.sub{color:#8b95a5;margin-bottom:24px;font-size:13px}
.card{background:#171a21;border:1px solid #242833;border-radius:10px;padding:18px;
margin-bottom:16px}
.hdr{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
flex-wrap:wrap}
.eid{font-family:ui-monospace,Consolas,monospace;color:#8b95a5;font-size:12px}
.claim{margin:10px 0 14px;color:#c7cdd6}
.v{font-weight:600;padding:3px 10px;border-radius:20px;font-size:12px;
letter-spacing:.3px}
.FALSIFIED{background:#3b1d1d;color:#ff8f8f;border:1px solid #5c2b2b}
.SUPPORTED{background:#16301f;color:#7fe0a0;border:1px solid #24512f}
.INCONCLUSIVE{background:#332a12;color:#f0cf7a;border:1px solid #57471c}
.OPEN{background:#1b2432;color:#93b4d8;border:1px solid #2b3a4d}
table{border-collapse:collapse;width:100%;margin-top:6px}
td{padding:7px 8px;border-top:1px solid #242833;vertical-align:top;font-size:13px}
td.n{width:210px;color:#9aa4b2}
td.r{width:78px}
.b{font-size:11px;font-weight:600;padding:2px 8px;border-radius:4px}
.ok{background:#16301f;color:#7fe0a0}
.bad{background:#3b1d1d;color:#ff8f8f}
.warn{background:#332a12;color:#f0cf7a}
.idle{background:#22262f;color:#8b95a5}
.err{background:#2a1a1a;border:1px solid #4a2626;color:#ffb3b3}
.note{color:#8b95a5;font-size:12px;margin-top:10px;border-top:1px solid #242833;
padding-top:10px}
"""


def render_html(rows: list[dict], errors: list[tuple[str, str]], summary: dict) -> str:
    e = html.escape
    out = ['<!doctype html><meta charset="utf-8">',
           '<title>ICV Lab</title><style>', CSS, '</style>',
           '<h1>ICV Lab &mdash; Independent Claim Verification</h1>']
    counts = ', '.join('%s %d' % (k.lower(), v) for k, v in sorted(summary['by_verdict'].items()))
    out.append('<div class="sub">%d engagement(s)%s &middot; %d failed check(s) '
               '&middot; generated %s</div>'
               % (summary['engagements'], ' &middot; ' + e(counts) if counts else '',
                  summary['total_failed_checks'], e(summary['generated_utc'])))

    for r in rows:
        out.append('<div class="card"><div class="hdr"><div>')
        out.append('<div class="eid">%s</div>' % e(r['engagement_id']))
        out.append('<div><strong>%s</strong></div></div>' % e(r['client']))
        out.append('<span class="v %s">%s</span></div>' % (e(r['verdict']), e(r['verdict'])))
        out.append('<div class="claim">%s</div>' % e(r['claim']))
        if r.get('verdict_plain'):
            out.append('<div class="claim"><em>%s</em></div>' % e(r['verdict_plain']))
        out.append('<table>')
        for name, body in r['checks'].items():
            label = name.replace('_', ' ')
            out.append('<tr><td class="n">%s</td><td class="r">'
                       '<span class="b %s">%s</span></td><td>%s</td></tr>'
                       % (e(label), BADGE[body['result']], e(body['result']),
                          e(body.get('detail', ''))))
        out.append('</table>')
        if r.get('boundary'):
            out.append('<div class="note">%s</div>' % e(r['boundary']))
        out.append('</div>')

    for name, msg in errors:
        out.append('<div class="card err"><strong>%s</strong> &mdash; %s</div>'
                   % (e(name), e(msg)))
    if not rows and not errors:
        out.append('<div class="card">No engagements found.</div>')
    return '\n'.join(out)


def main(argv: list[str] | None = None) -> int:
    here = pathlib.Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description='Generate the ICV Lab dashboard.')
    ap.add_argument('--root', default=str(here / 'engagements'))
    ap.add_argument('--out', default=str(here))
    ap.add_argument('--strict', action='store_true',
                    help='exit non-zero if any engagement failed to load')
    args = ap.parse_args(argv)

    rows, errors = scan(pathlib.Path(args.root))
    summary = summarize(rows)
    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    payload = {'summary': summary, 'engagements': rows,
               'errors': [{'engagement': n, 'error': m} for n, m in errors]}
    (outdir / 'dashboard.json').write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
        encoding='utf-8')
    (outdir / 'dashboard.html').write_text(
        render_html(rows, errors, summary) + '\n', encoding='utf-8')

    print('engagements : %d' % summary['engagements'])
    for k, v in sorted(summary['by_verdict'].items()):
        print('  %-13s %d' % (k, v))
    print('failed checks: %d' % summary['total_failed_checks'])
    for n, m in errors:
        print('  ERROR %s: %s' % (n, m), file=sys.stderr)
    print('wrote %s and %s' % (outdir / 'dashboard.json', outdir / 'dashboard.html'))
    return 1 if (errors and args.strict) else 0


if __name__ == '__main__':
    raise SystemExit(main())
