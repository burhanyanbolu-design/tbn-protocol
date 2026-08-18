# EOG Addressing Specification

Date: 2026-08-17  
Status: **VERIFIED SPECIFICATION / CLASSICAL STORAGE SCHEME**

Derived from the charts Burhan supplied (`2x2`, `3x3`, `6x6`, `8x8`) and verified exactly across 19 configurations including non-square grids and wider overlaps.

## Invariant: the box is always square

**`R = W` is a mandatory rule of EOG, not a configuration option.** Build 18 rows and you build 18 columns. Non-square boxes are out of specification.

Consequences of the invariant:

- the stride is unambiguous. Since rows equals columns, "total rows minus one" and "total columns minus one" are the same number, so either reading gives the correct stride;
- the scheme has exactly **one** parameter, `n`;
- capacity is fixed by `n` and cannot be tuned independently.

Implementations should therefore take `n` alone and reject any attempt to set rows and columns separately. The general `(R, W, k)` algebra later in this document is retained as mathematical background, and to make clear *why* the stride is what it is; it does not describe permitted configurations.

### Why the box must be square

The invariant exists so that **the diagonal is the shortest route**. Verified by BFS on the identified graph with all eight moves available:

| box | pure diagonal | pure vertical | true shortest | diagonal optimal |
|---|---:|---:|---:|---|
| `3x3` | 2 | 3 | 2 | **yes** |
| `4x4` | 3 | 4 | 3 | **yes** |
| `6x6` | 5 | 6 | 5 | **yes** |
| `8x8` | 7 | 8 | 7 | **yes** |
| `12x12` | 11 | 12 | 11 | **yes** |
| `3x8` | 7 | **3** | 3 | no |
| `2x10` | 9 | **2** | 2 | no |
| `4x12` | 11 | **4** | 4 | no |
| `12x4` | 11 | 12 | **9** | no |
| `10x2` | 9 | 10 | **5** | no |

In a square box the diagonal crosses in `n - 1` steps against `n` for the vertical route, and nothing beats it at any size tested. In a non-square box the diagonal runs out on the short side, so it must be finished with straight steps, and a vertical or mixed route wins instead. A wide `3x8` box needs only `3` vertical steps where the diagonal takes `7`.

The reason is that a diagonal step advances both axes at once, so it can only reach the far corner unaided when both axes have the same extent. That happens exactly when `R = W`. Squareness is therefore a functional requirement of the addressing scheme, not a stylistic choice.

## Canonical form: square box, one parameter

With the square invariant and a one-cell overlap the whole scheme reduces to a single parameter `n`:

```
R = W = n,  k = 1,  stride = n - 1

L(r,c)   = (n-1)*r + c
capacity = n*n - n + 1          distinct labels, 0 .. n*n-n
offsets  = +-1, +-(n-2), +-(n-1), +-n
distance = n                    corner to corner
diagonal = 0, n, 2n, ... n(n-1)
```

The stride is **total rows minus one**, which in an `18 x 18` box is `17`. Note the precision: in the general case the stride is `W - k`, governed by the **column** count. It equals "rows minus one" only because the box is square. A non-square box must use `W - k`.

To size a box for `N` items, take the smallest `n` with `n*n - n + 1 >= N`, i.e.

`n = ceil((1 + sqrt(4N - 3)) / 2)`

Capacity therefore comes in fixed jumps, so a box usually has spare cells:

| `n` | stride | capacity | distance | diagonal step |
|---:|---:|---:|---:|---:|
| 2 | 1 | 3 | 2 | 2 |
| 3 | 2 | 7 | 3 | 3 |
| 4 | 3 | 13 | 4 | 4 |
| 5 | 4 | 21 | 5 | 5 |
| 6 | 5 | **31** | 6 | 6 |
| 8 | 7 | **57** | 8 | 8 |
| 10 | 9 | 91 | 10 | 10 |
| 12 | 11 | 133 | 12 | 12 |
| 18 | 17 | **307** | 18 | 18 |

The bolded rows are the charts supplied and verified: `6x6` holding 31 labels, `8x8` holding 57, and `18x18` holding 307. For 18 required labels the rule gives `n = 5`, capacity 21, with 3 spare.

The remainder of this document gives the general `(R, W, k)` form, of which the square box is the case `R = W` and `k = 1`.

## Parameters

| symbol | meaning |
|---|---|
| `R` | number of rows |
| `W` | number of columns |
| `k` | overlap width in cells at each row boundary, `1 <= k < W` |
| `stride` | `W - k` |

Burhan's charts all use `k = 1`, giving `stride = W - 1`. That single choice is what creates the overlap: ordinary row-major indexing uses `stride = W`, so rows do not share cells.

## Forward map

`L(r, c) = (W - k) * r + c`, for `0 <= r < R`, `0 <= c < W`.

## Validity and boundary conditions

Verified by exhaustive check of all `R, W` from `1` to `4` at `k = 1`:

| condition | result | reason |
|---|---|---|
| `W = k` | **invalid** | `stride = 0`, so every cell collapses to label `0` |
| `R = 1` | **no overlap** | a single row has no row boundary, so the scheme reduces to plain indexing |
| `R = 2, W = 2` | **minimum viable** | 4 cells, 3 labels, exactly 1 overlap |
| `W = k + 1` | **direction-degenerate** | `stride = 1`, so right `+1` and down `+1` are indistinguishable |
| `W >= k + 2` | **fully distinct** | `stride >= 2`, so right and down differ |

So the minimum box that exhibits any overlap is `2 x 2`, four cells. That is the smallest structure in which the scheme exists at all, even though only two cells are needed to make a single move.

At `2 x 2` the labels are `0, 1` over `1, 2`. Label `1` lives at both `(0,1)` and `(1,0)`, and after identification the graph is the path `0 - 1 - 2` with corner-to-corner distance `2`. But because `stride = 1`, moving right and moving down both add `1`, so the two directions cannot be told apart arithmetically. The same degeneracy holds for every `W = 2` box, including `3 x 2` and `4 x 2`.

Distinguishing horizontal from vertical movement therefore requires `W >= 3` at `k = 1`. The smallest fully non-degenerate boxes are `2 x 3` and `3 x 3`.

Implementations should reject `W <= k` outright, and should treat `R = 1` and `W = k + 1` as degenerate special cases rather than silently accepting them.

## Move offsets

| move | offset | reverse |
|---|---:|---:|
| right | `+1` | `-1` |
| down | `+(W - k)` | `-(W - k)` |
| diagonal down-right | `+(W - k + 1)` | `-(W - k + 1)` |

The diagonal is the sum of the other two, and every move is exactly invertible. The offsets **change with box size**, which is the rule Burhan identified: adding rows or columns requires recomputing them.

For square grids with `k = 1`, `stride = n - 1`, so right is `+1`, down is `+(n-1)` and diagonal is `+n`. The diagonal sequence is `L(r,r) = n*r`, giving `0, n, 2n, ...` up to `n(n-1)`.

## Eight-neighbour offsets

Verified against the `6x6` grid with centre `17` at `(3,2)`, reproducing the neighbourhood `11 12 13 / 16 17 18 / 21 22 23` exactly:

| move | offset | general form | value at `stride = 5` |
|---|---:|---|---:|
| left / right | `-1` / `+1` | `+-1` | `+-1` |
| up / down | `-5` / `+5` | `+-stride` | `+-5` |
| main diagonal, up-left / down-right | `-6` / `+6` | `+-(stride + 1) = +-W` | `+-6` |
| anti-diagonal, up-right / down-left | `-4` / `+4` | `+-(stride - 1)` | `+-4` |

Two step sizes must not be confused, and this is the distinction Burhan identified:

- the **vertical** step is `stride = W - k = 5`, the logical row advance;
- the **main diagonal** step is `stride + 1 = W = 6`, which is the **physical column count**.

One correction for the record: the **anti-diagonal** step is `stride - 1 = 4`, not `5`. The pair `13` and `21` differ by `8`, which is two anti-diagonal steps of `4`.

For `k = 2` on the same width the set becomes `+-1`, `+-4` vertical, `+-5` main diagonal, `+-3` anti-diagonal.

## Translation invariance

The offsets do not depend on where you are in the box. Verified exhaustively on the `6x6` grid: **220 in-box moves across all 36 cells, zero offset violations.**

| move | offset | available at |
|---|---:|---:|
| left, right, up, down | `+-1`, `+-stride` | 30 of 36 cells |
| all four diagonals | `+-(stride+-1)` | 25 of 36 cells |

Only **availability** changes at the edges, never the arithmetic. `up` is unavailable in row `0`, `down` in the last row, `left` in column `0`, `right` in the last column, and the diagonals along the corresponding edges.

This is translation invariance: one fixed local rule applies at every point, and the numbers never change with position. It is the same property that makes regular lattices analytically tractable in physics, where it underlies band structure and momentum-space solutions. Note that it is a generic feature of any regular strided indexing, not something unique to the overlap; the overlap is what makes the seam behaviour distinctive.

## The label sequence is always a path

Verified on the identified graph: all `30` consecutive label pairs from `0..30` are adjacent, with **zero** exceptions.

Consecutive labels are adjacent even across a seam. For `19 -> 20`, adjacency runs through the shared cell, since `20` lives at both `(3,5)` and `(4,0)`. So the label line `0 - 1 - 2 - ... - max` is a genuine path in the graph at every point, which is why `+-1` is always a legal sequence move.

## Step-size degeneracy hierarchy

The four step magnitudes are `1`, `stride-1`, `stride`, `stride+1`. They stay distinct only once the box is wide enough:

| width | stride | offsets `1 / stride-1 / stride / stride+1` | status |
|---|---:|---|---|
| `W = k` | 0 | — | invalid, all labels collapse |
| `W = k+1` | 1 | `1 / 0 / 1 / 2` | anti-diagonal offset is **0**, so that move does not change the label at all; right and down coincide |
| `W = k+2` | 2 | `1 / 1 / 2 / 3` | anti-diagonal **coincides with horizontal** |
| `W >= k+3` | `>= 3` | `1 / 2 / 3 / 4 ...` | all four magnitudes distinct |

So `W >= k + 3` is required for the full eight-neighbour structure to be arithmetically unambiguous. At `k = 1` that means `W >= 4`.

## Label arithmetic is not grid-bounded movement

Because labels form a contiguous run from `0` to the maximum, `+-1` always moves one place along the underlying sequence. It does **not** stay inside one row.

Verified: at `(3,0)` the label is `15`, and `-1` gives `14`, which lives at `(2,4)` in the previous row.

Implementations must therefore decide explicitly which they mean:

- **sequence movement** — plain label arithmetic, always valid for `0 <= L <= max`, freely crossing row boundaries;
- **grid-bounded movement** — must check `0 <= r < R` and `0 <= c < W` after applying an offset, and reject moves that leave the box.

Conflating the two produces off-by-one errors precisely at the row edges, which is where the overlap already needs care.

## Counts

- distinct labels: `(W - k) * (R - 1) + W`
- highest label: `(W - k) * (R - 1) + (W - 1)`
- grid cells: `R * W`
- cells collapsed by overlap: `(R - 1) * k`

Labels always form a gap-free run from `0` to the maximum. For square grids with `k = 1` the label count is `n^2 - n + 1`.

## Overlap identity

The last `k` cells of row `r` are the same items as the first `k` cells of row `r + 1`:

`L(r, W - k + i) = L(r + 1, i)` for `0 <= i < k`.

## Verified cases

Square, `k = 1`:

| grid | stride | labels | collapsed | right | down | diagonal | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2x2` | 1 | 3 | 1 | +1 | +1 | +2 | 2 |
| `3x3` | 2 | 7 | 2 | +1 | +2 | +3 | 6 |
| `4x4` | 3 | 13 | 3 | +1 | +3 | +4 | 12 |
| `6x6` | 5 | 31 | 5 | +1 | +5 | +6 | 30 |
| `8x8` | 7 | 57 | 7 | +1 | +7 | +8 | 56 |
| `10x10` | 9 | 91 | 9 | +1 | +9 | +10 | 90 |

Non-square, `k = 1`: `3x5` gives 13 labels; `5x3` gives 11; `4x7` gives 25; `7x4` gives 22; `6x9` gives 49; `12x6` gives 61. All match the formula.

Wider overlaps: `6x6 k=2` gives 26 labels and 10 collapsed; `6x6 k=3` gives 21 and 15; `8x8 k=2` gives 50 and 14; `8x8 k=3` gives 43 and 21; `10x10 k=2` gives 82 and 18. All match.

## Inverse map, with a canonical rule that removes the ambiguity

**The inverse is not unique at overlaps.** An overlap label has two valid homes. In `8x8`, label `7` is both `(0,7)` and `(1,0)`.

For `k = 1` there is a clean canonical resolution, verified for every label:

```
r, c = divmod(L, stride)          # valid for L < stride * R
if L == stride * R:  r, c = R-1, W-1   # the single final label
```

Verified on the `6x6` grid: this rule resolves all labels `0..30` to a valid cell, and **the columns it uses are only `0..stride-1`**, never the last column.

That gives the implementation rule:

- **canonical storage lives in columns `0 .. stride-1`**, which hold every label exactly once;
- **the last column is always an alias**, a read-only view of the next row's first cell;
- the single highest label is the sole special case, living at `(R-1, W-1)`;
- address computation is one division and one remainder, so `O(1)`.

Writing only to canonical cells and treating the last column as a view eliminates the duplicate-write and stale-read hazard at the seams. If instead the overlap is intended as **two physical slots holding the same value**, that is deliberate redundancy and write consistency must be enforced explicitly. What must not happen is allowing both silently.

## Seam structure

For `k = 1`, verified on `6x6`:

- **each row after the first contributes only `stride` new labels, not `W`.** Row 0 gives `0..5`, then each later row adds 5. This is precisely why the stride is `W - 1`: the last cell of a row is not new.
- **first column** holds `0, 5, 10, 15, 20, 25`; **last column** holds `5, 10, 15, 20, 25, 30`. Both are multiples of the stride, the last column being the first shifted one row.
- **overlap labels are exactly the interior multiples of the stride**, here `5, 10, 15, 20, 25`, numbering `R - 1`. The two extreme labels `0` and the maximum appear only once.
- moving down anywhere, including along the seam column, is `+stride`. Stepping down the seam column therefore enumerates the row anchors.

## Structural properties, measured

- **Locality is preserved.** Items adjacent in the sequence stay adjacent in the grid view, and rows join only to the next row.
- **Diameter is `Theta(n)`.** Measured corner-to-corner distance is exactly `n` on square grids with `k = 1`, against `2(n - 1)` with no overlap. So the overlap gives roughly a factor-of-two improvement, but distance still grows linearly.
- **Long-range alternatives reach constant distance.** Pairings that join distant rows achieve distance `2` regardless of grid size. See `data/area-one-corrected-model-locality-falsification-2026-08-17.md`.

These are two sides of one design decision. A structure cannot be maximally local and also have constant diameter. EOG chooses locality.

## Suitable and unsuitable uses

**Suited to:** sequential and range scans, sliding windows over a 1D sequence, cache-friendly traversal, tiled or paged views of an ordered dataset, and seam cells that legitimately belong to two windows.

**Not suited to:** minimising traversal distance, small-world or shortcut-based routing, and quantum-walk search advantage, which was measured and falsified.

## Boundary

This is a verified classical addressing specification. It asserts no quantum property, no advantage and no novelty relative to existing indexing schemes. Row-major addressing with a stride is standard; the specified element here is `stride = W - k` producing deliberate overlap. No staging, commit or push occurred.
