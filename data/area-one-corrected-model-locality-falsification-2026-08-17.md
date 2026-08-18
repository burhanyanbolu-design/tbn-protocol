# Area One: The Corrected EOG Model Is Also Falsified, and We Now Know Why

Date: 2026-08-17  
Status: **CORRECTED MODEL FALSIFIED AT EVERY TESTED SIZE / MECHANISM IDENTIFIED**

## What was tested

After discovering that a shared label means cell **identity** rather than an extra edge, the corrected model was built: an `n x n` grid with stride `n-1`, no wraparound, and the `n-1` overlaps merged as single nodes. Burhan supplied and confirmed both the `6x6` and `8x8` charts.

The mandatory first test from `data/area-one-modelling-error-shared-label-identity-2026-08-17.md` was run: for every pairing, merge `(r, n-1)` with `(f(r), 0)` and measure the corner-to-corner graph distance. Exhaustive over all `(n-1)!` pairings for `n <= 8`; 2000 sampled pairings for larger `n`.

Development-only structural measurement. No dynamics, no held-out access, no tuning. Script was temporary and deleted.

## Confirmed label structure

For an `n x n` grid with stride `n-1`: `L(r,c) = (n-1)r + c`.

- overlaps: `L(r, n-1) = (n-1)(r+1) = L(r+1, 0)`, so consecutive rows share exactly one label;
- moves: right `+1`, down `+(n-1)`, diagonal `+n`, each exactly reversible;
- diagonal: `L(r,r) = n*r`, so `0, n, 2n, ...` up to `n(n-1)`;
- distinct labels: `n*n - n + 1`, since the `n-1` overlaps collapse `n-1` cells.

`6x6` gives labels `0..30`, diagonal step `6`, `31` labels. `8x8` gives labels `0..56`, diagonal step `8`, `57` labels. Both match the supplied charts exactly.

## Result

| grid | labels | plain `2(n-1)` | genuine | best control | median control | controls strictly shorter |
|---|---:|---:|---:|---:|---:|---|
| `6x6` | 31 | 10 | **6** | 2 | 3 | **119 / 119** |
| `7x7` | 43 | 12 | **7** | 2 | 4 | **719 / 719** |
| `8x8` | 57 | 14 | **8** | 2 | 4 | **5039 / 5039** |
| `10x10` | 91 | 18 | **10** | 2 | 4 | **2000 / 2000** |
| `12x12` | 133 | 22 | **12** | 2 | 4 | **2000 / 2000** |
| `16x16` | 241 | 30 | **16** | 2 | 5 | **2000 / 2000** |
| `20x20` | 381 | 38 | **20** | 2 | 5 | **2000 / 2000** |

**One hundred percent of control pairings beat the genuine pairing at every size tested**, exhaustively for `n <= 8`, including all `5039` pairings at `8x8`. Not one control tied or lost.

## The mechanism, which is now clear

Two exact regularities explain everything:

- **genuine distance is exactly `n`** at every size;
- **best control distance is constant at `2`**, and median control distance stays near `4` to `5`, independent of grid size.

So the genuine pairing does help relative to no overlap at all: it reduces `2(n-1)` to `n`, roughly a factor of two. That gain is real.

But it stays `Theta(n)`, while long-range pairings achieve `O(1)`. The gap therefore **widens without limit**: at `6x6` it is `6` against `2`, and at `20x20` it is `20` against `2`, a tenfold difference and growing.

The reason is that EOG's overlap is deliberately **local**: it joins consecutive rows only. Local joins preserve neighbourhood structure and cannot collapse the diameter. A control that merges row `0`'s end with row `n-1`'s start creates a direct wormhole between the corners, which is precisely the small-world effect that crushes distance to a constant.

## Interpretation, stated fairly

This is not "EOG is badly designed." It is that EOG is optimised for the **opposite** property to the one a quantum walk rewards.

- EOG preserves **sequential locality**: items adjacent in the underlying sequence stay adjacent in the grid view. That is genuinely valuable for cache behaviour, range scans, sliding windows and streaming access.
- Locality and small diameter are in direct tension. A structure cannot be maximally local and simultaneously have constant diameter.
- Walk-based search rewards small diameter. EOG deliberately gives that up.

So the locality that makes EOG useful as a data structure is the same property that makes it the worst available pairing for walk traversal. Those are two faces of one design decision, not a defect.

## Consequences for the research line

The mandatory first test said stop if the genuine pairing is not distinguished favourably. It is distinguished, but in the wrong direction, at every size, exhaustively at three sizes.

- The corrected model is **falsified** for transport or search advantage. No further conditions need testing: N1 non-isomorphism, N2 and N4 are moot for a mechanism that is last in the ordering.
- Both models now agree. The torus surrogate ranked the genuine pairing 95 of 101. The corrected identified model ranks it last of all pairings at every size. The original conclusion survives the correction and is strengthened, not weakened.
- The earlier caution about wording is now unnecessary. It is fair to say the EOG pairing confers no traversal advantage in either model, because the corrected model was tested directly.
- The `sqrt`-like diagonal crossing is generic to folding a line into two dimensions and confers nothing specific to EOG's pairing.

## Where this genuinely points

Toward EOG as a **locality-preserving classical index**, which is what the measurement says it is. Sequential locality with one-cell overlap at row boundaries is a real, coherent property with real uses: range queries, sliding windows, cache-friendly scans, and the Elastic Hippocampus memory work.

It does not point toward quantum walk advantage, and no further quantum-walk candidate is justified by this evidence.

## Boundary

Exact graph-distance measurement only. No dynamics, transport probability, quantum claim or advantage is asserted or implied. Candidate 1 is not revived. The frozen protocol and the `-0.02` floor are unchanged. No source or test file was added; no staging, commit or push occurred.
