"""EOG box calculator.

Given a required number of labels N, enumerate every valid (R, W, k) box that
holds exactly N labels, flag degenerate shapes, draw the chart, and compute the
corner-to-corner shortest distance both by closed form and by BFS.

Design equation (see data/eog-addressing-specification-2026-08-17.md):
    stride s = W - k
    N       = s * R + k
    L(r,c)  = s * r + c

Standard library only.

Usage:
    python eog_box.py --labels 18
    python eog_box.py --labels 31 --show 6 6 1
"""
from __future__ import annotations

import argparse
from collections import deque


def boxes_for(n_labels: int, max_k: int = 4):
    """All (R, W, k) with exactly n_labels labels."""
    out = []
    for k in range(1, max_k + 1):
        rem = n_labels - k
        if rem < 1:
            continue
        for s in range(1, rem + 1):
            if rem % s:
                continue
            R = rem // s
            if R < 2:
                continue
            W = s + k
            if W <= k:
                continue
            out.append((R, W, k, s))
    return out


def status_of(s: int, R: int) -> str:
    if s == 1:
        return 'degenerate: anti-diagonal is a no-op, right == down'
    if s == 2:
        return 'degenerate: anti-diagonal == horizontal'
    return 'full: all four step sizes distinct'


def squareness(R: int, W: int) -> float:
    return abs(R - W)


def label(s: int, r: int, c: int) -> int:
    return s * r + c


def chart(R: int, W: int, k: int) -> list[list[int]]:
    s = W - k
    return [[label(s, r, c) for c in range(W)] for r in range(R)]


def corner_distance_bfs(R: int, W: int, k: int):
    """BFS on the identified graph from label 0 to the maximum label."""
    parent = {(r, c): (r, c) for r in range(R) for c in range(W)}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    s = W - k
    groups = {}
    for r in range(R):
        for c in range(W):
            groups.setdefault(label(s, r, c), []).append((r, c))
    for cells in groups.values():
        first = cells[0]
        for other in cells[1:]:
            a, b = find(first), find(other)
            if a != b:
                parent[a] = b

    adj = {}
    for r in range(R):
        for c in range(W):
            u = find((r, c))
            adj.setdefault(u, set())
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if nr < R and nc < W:
                    v = find((nr, nc))
                    if v != u:
                        adj[u].add(v)
                        adj.setdefault(v, set()).add(u)

    start = find((0, 0))
    goal = find(groups[max(groups)][0])
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


def corner_distance_formula(R: int, W: int, k: int) -> int:
    """Fewest +-1 and +-stride steps to cross the whole label range."""
    s = W - k
    D = (s * R + k) - 1                       # highest label
    best = D                                  # all single steps
    for q in range(0, D // s + 2):
        best = min(best, q + abs(D - q * s))
    return best


def square_side_for(n_labels: int) -> int:
    """Smallest n with an n x n, k=1 box holding at least n_labels.

    Capacity of a square box is n*n - n + 1, so
        n >= (1 + sqrt(4*N - 3)) / 2
    """
    n = 2
    while n * n - n + 1 < n_labels:
        n += 1
    return n


def square_report(n_labels: int) -> int:
    """Canonical EOG: equal rows and columns, k = 1."""
    n = square_side_for(n_labels)
    s = n - 1
    cap = n * n - n + 1
    print('CANONICAL EOG: equal rows and columns, k = 1')
    print()
    print('  labels required : %d  (0..%d)' % (n_labels, n_labels - 1))
    print('  box             : %d x %d' % (n, n))
    print('  stride          : %d   (= n - 1)' % s)
    print('  capacity        : %d   (= n*n - n + 1)' % cap)
    print('  spare capacity  : %d' % (cap - n_labels))
    print('  cells           : %d   overlaps: %d' % (n * n, n - 1))
    print('  offsets         : horizontal +-1 | anti-diagonal +-%d | '
          'vertical +-%d | main diagonal +-%d' % (s - 1, s, s + 1))
    print('  corner distance : %d   (BFS verified: %s)'
          % (corner_distance_formula(n, n, 1), corner_distance_bfs(n, n, 1)))
    print('  diagonal        : %s' % ' '.join(str(n * r) for r in range(n)))
    print()
    width = len(str(cap - 1))
    print('  ' + ' ' * 5 + ''.join(chr(65 + c).rjust(width + 1) for c in range(n)))
    print('  ' + ' ' * 5 + '-' * ((width + 1) * n))
    for r in range(n):
        cells = ''.join(str(s * r + c).rjust(width + 1) for c in range(n))
        mark = ''
        if s * r > n_labels - 1:
            mark = '   <- beyond required range'
        print('  r%-3d|%s%s' % (r, cells, mark))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='EOG box calculator.')
    ap.add_argument('--labels', type=int, required=True,
                    help='required number of labels, e.g. 18 for 0..17')
    ap.add_argument('--max-k', type=int, default=4)
    ap.add_argument('--show', nargs=3, type=int, metavar=('R', 'W', 'K'),
                    help='draw the chart for a specific box')
    ap.add_argument('--square', action='store_true',
                    help='canonical mode: equal rows and columns, k=1')
    ap.add_argument('--table', type=int, metavar='MAX_N',
                    help='print the capacity table for square boxes up to MAX_N')
    args = ap.parse_args(argv)

    if args.table:
        print('%-5s %-8s %-10s %-10s %-s' %
              ('n', 'stride', 'capacity', 'distance', 'diagonal step'))
        print('-' * 52)
        for m in range(2, args.table + 1):
            print('%-5d %-8d %-10d %-10d %-d'
                  % (m, m - 1, m * m - m + 1, m, m))
        return 0

    if args.square:
        return square_report(args.labels)

    n = args.labels
    cands = boxes_for(n, args.max_k)
    print('labels required : %d  (0..%d)' % (n, n - 1))
    print('design equation : N = (W - k) * R + k')
    print()
    if not cands:
        print('no valid box holds exactly %d labels for k <= %d' % (n, args.max_k))
        return 1

    print('%-4s %-4s %-4s %-7s %-7s %-9s %-9s %-s' %
          ('R', 'W', 'k', 'stride', 'cells', 'dist(cf)', 'dist(bfs)', 'status'))
    print('-' * 96)
    cands.sort(key=lambda t: (squareness(t[0], t[1]), -t[3]))
    for R, W, k, s in cands:
        d_cf = corner_distance_formula(R, W, k)
        d_bfs = corner_distance_bfs(R, W, k)
        flag = '' if d_cf == d_bfs else '  <-- MISMATCH'
        print('%-4d %-4d %-4d %-7d %-7d %-9d %-9s %-s%s' %
              (R, W, k, s, R * W, d_cf, d_bfs, status_of(s, R), flag))

    full = [t for t in cands if t[3] >= 3]
    print()
    if full:
        R, W, k, s = full[0]
        print('recommended (most square, non-degenerate): R=%d W=%d k=%d stride=%d'
              % (R, W, k, s))
    else:
        print('NOTE: no non-degenerate box holds exactly %d labels.' % n)
        print('      Every option has stride < 3, so some step sizes collide.')
        sq = [m * m - m + 1 for m in range(2, 12)]
        near = [v for v in sq if v >= n][:1]
        print('      Square k=1 boxes hold N = R*R - R + 1: %s' % sq)
        if near:
            m = next(m for m in range(2, 12) if m * m - m + 1 == near[0])
            print('      Next square box up is %dx%d holding %d labels, '
                  'leaving %d spare.' % (m, m, near[0], near[0] - n))

    target = tuple(args.show) if args.show else (full[0][:3] if full else cands[0][:3])
    R, W, k = target
    s = W - k
    print()
    print('chart for R=%d W=%d k=%d (stride %d)' % (R, W, k, s))
    width = len(str(s * R + k - 1))
    for row in chart(R, W, k):
        print('   ' + ' '.join(str(v).rjust(width) for v in row))
    print()
    print('offsets: horizontal +-1 | anti-diagonal +-%d | vertical +-%d | '
          'main diagonal +-%d' % (max(s - 1, 0), s, s + 1))
    print('corner-to-corner distance: %d  (BFS verified: %s)'
          % (corner_distance_formula(R, W, k), corner_distance_bfs(R, W, k)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
