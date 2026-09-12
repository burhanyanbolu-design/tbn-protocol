# Drafts — Addendum VI withdrawal, 11 September 2026

Copy-paste ready. Character counts verified against LinkedIn limits
(comment: 1,250 / post: 3,000 / DM: 8,000).

---

## 1. LinkedIn — REPLY under your own pruning comment

Post as a **reply to your own comment** in that thread (the one showing
"104 configurations out of 1,048,576"), so the correction sits directly
under the wrong number.

```
Correction to my comment above — that result was wrong. I'm withdrawing it.

I reported pruned contraction hitting 1.5e-4 accuracy on 0.01% of configurations. I measured absolute error only. The amplitudes are themselves ~1e-4, so an output of roughly zero registered as a small error.

The figure reproduces exactly: 1.459e-4 at width 20. But max|exact| there is 1.4685e-4. Relative error is 99.4%. It wasn't approximating the answer, it was deleting it.

"Error improves with width" falls too — absolute error was tracking the shrinking amplitude scale, not accuracy.

There's also no usable operating point: where pruning is faithful it removes nothing; where it removes anything meaningful, relative error is ~100%.

I found it while testing the same idea on real heavy-hex topology, which returned exact zeros and made the pattern obvious.

Worth noting the direction: this addendum argued against my own hardness claim, so withdrawing it restores that position rather than weakening it.

Audit script and corrected record in v3: https://doi.org/10.5281/zenodo.22352839

Lesson: quote accuracy relative to the scale of what you're computing.
```

---

## 2. Message to Sophie Choe — DM reply

**This one is necessary, not optional.** She asked "Do you have a manuscript?"
in DM and was pointed at the Zenodo DOI. The concept DOI resolves to the
LATEST version, which is currently v2 — so she was sent a link to a record
containing the now-withdrawn claim. She needs to hear it from you.

Context to keep straight:
- Her comments: (a) qubit direction is a dead end because binary doesn't
  exist in the quantum world, citing Braunstein & van Loock's continuous-
  variable review (arXiv:quant-ph/0410100); (b) qubit simulators still have
  merit because they expand the classical algorithm space.
- She cited the canonical CV reference, so she knows this literature. Engage
  it properly rather than just agreeing.
- **Keep Area Four out of this**, per standing instruction. Area Four is also
  not on Zenodo, so there is no citable link for it anyway.

```
Hi Sophie,

Following up on your manuscript question, and leading with a correction.

The record is on Zenodo under concept DOI 10.5281/zenodo.22352839, which now resolves to v3. I've just published that version, and you should know why: it withdraws an addendum I published on the 9th. If you followed the link before tonight, you'd have landed on a claim I've since retracted.

What went wrong. I reported a pruning shortcut reaching ~1e-4 accuracy while keeping 0.01% of configurations. I had measured absolute error only. The amplitudes are themselves around 1e-4, so an output of roughly zero registered as a small error. The figure reproduces exactly — 1.459e-4 at width 20 — but the largest amplitude there is 1.4685e-4. Relative error 99.4%. It was deleting the answer, not approximating it. The "accuracy improves with width" claim went the same way: absolute error was tracking the shrinking amplitude scale.

I found it while testing the same idea on real heavy-hex topology, which returned exact zeros and made the pattern obvious. v3 includes a read-only audit script that reproduces the correction against the original unmodified code, so you can check it rather than take my word.

The exact results are unaffected — they involve no pruning — and the withdrawn addendum argued against my own hardness claim, so retracting it restores that position rather than weakening it. But I'd rather you had this from me than found it yourself.

On your dead-end argument. I think you're right about the direction, and my own results point the same way: the gate-model route needs roughly 70 qubits at 0.06% error, which is a hardware specification rather than a research programme. Where I'd push back slightly is the framing — two-level systems are physically real, so qubits aren't purely an imposed abstraction. The stronger version of your point, which I do accept, is that forcing quantum systems into discrete gate models discards structure they natively have. That's the CV case, and Braunstein & van Loock make it well.

Your other comment is the one I keep coming back to: that qubit simulators earn their place by expanding the classical algorithm space. That's the most accurate description of this work anyone has offered, including me. What survived here is a classical contraction technique, and today's result is a classical-simulation finding.

Which leads to the one thing I'd genuinely value your view on. I have deliberately not claimed novelty for the frontier-contraction approach, because I haven't done a proper prior-art search and it looks close to standard variable elimination. If you know that literature, I'd rather be told it's known than claim otherwise and be corrected later.

Burhan
```

---

## 3. Zenodo v3 — upload notes

Concept DOI (always share this one): `10.5281/zenodo.22352839`
v2 version DOI (now superseded): `10.5281/zenodo.22682956`

### Steps

1. Go to the record → **New version** (preserves the concept DOI)
2. **Remove** the old file `EQCCM-feasibility-study-v2-2026-09-09.zip`
3. **Upload** `demo/eqccm/EQCCM-feasibility-study-v3-2026-09-11.zip` (88 KB, 16 files)
4. **Replace the whole Description field** with section 3b below —
   important, because the current description *asserts the withdrawn claim*
   in its final paragraph and says "six times (seven as of v2)"
5. Publication date → 2026-09-11
6. Leave the **title unchanged** ("...the six things we got wrong") so
   existing citations and links stay coherent. The six refers to the original
   study; the addendum count lives in the description.
7. Publish

### 3b. FULL REPLACEMENT for the Description field

Zenodo accepts HTML here. Paste this in place of the entire existing text.

```html
<p>A feasibility study testing whether quantum circuits can be constructed where exact classical simulation cost grows much faster than the physical circuit depth needed to run them, using output-aware tensor-network contraction validated against two real IBM Quantum hardware jobs (dadm3mjdd5gc73d7gvjg, dadm9qdnj4cs73ae2teg; 40,960 shots total).</p>

<p>The honest conclusion is no &mdash; not on any hardware available today. Reaching that conclusion required correcting the study's own conclusions eight times as of v3, including withdrawing an entire addendum two days after publishing it. Those corrections, and the measurements behind them, are the primary contribution.</p>

<p>Key measured results: classical contraction cost scales as 2^w with measured exponent 1.984; effective two-qubit error on IBM's Heron architecture is gate-local at 0.845%, reproducible across two independent jobs; memory is not a binding constraint once slicing is applied (1.00-3.18x FLOP penalty); connectivity degree, not planarity, is the dominant topological lever; standard error suppression (dynamical decoupling + twirling) made fidelity worse on this circuit class; qubit count sets a hard ceiling on achievable classical hardness (2^n).</p>

<p>This is a feasibility study, not an advantage claim: no quantum advantage, no novel algorithm (frontier contraction is textbook variable elimination), and no verified large-width result are claimed. Full reproducibility scripts included.</p>

<p><strong>Version 3 (11 September 2026) WITHDRAWS Addendum VI.</strong> The v2 addendum claimed amplitude-magnitude pruning reached ~1e-4 accuracy while retaining 0.01% of frontier configurations (104 of 1,048,576 at w=20), roughly 14,000x faster than exact contraction, with accuracy improving as width grew. That result was an artefact of reporting absolute error only. The pruned computation returned essentially no signal, and because the true amplitudes are themselves ~1e-4, an output of near-zero registered as a small absolute error. The headline figure reproduces exactly (1.459e-4), but max|exact| at that point is 1.4685e-4 &mdash; a relative error of 99.4%. The "error improves monotonically with width" finding falls with it: absolute error was tracking the shrinking amplitude scale, not approximation quality. Decisively, no threshold both saves work and stays correct &mdash; where pruning is faithful it retains the full frontier and removes nothing; where it removes anything meaningful the relative error is ~100%. The two regions do not overlap.</p>

<p>Also withdrawn: the v2 consequence for the classical hardness argument. Approximate classical cost is NOT shown to be below 2^w by this evidence. Note the direction of the correction &mdash; Addendum VI argued <em>against</em> this study's own hardness claim, so withdrawing it restores the 2^w position rather than weakening it.</p>

<p>Version 3 adds Addendum VII with the full correction, a read-only audit script that reproduces it against the unmodified original code, and an independent null result from running the same test on the real 156-qubit ibm_fez heavy-hex coupling map (pruning does not compound there; single-qubit rotations regenerate the dropped configurations, and at usable thresholds it is slower than not pruning). All exact results are unaffected &mdash; banded_scaling.py involves no pruning, and the 2^w scaling with exponent 1.984 stands. Addendum VI is preserved unedited so the withdrawn claim remains reproducible and the correction independently checkable. Scope limit stated plainly: only the naive global-magnitude cutoff was tested; SVD/bond-dimension truncation is far stronger and remains untested, so the honest claim is "the naive shortcut fails", not "no shortcut exists". No additional quantum time used; programme total remains 2 jobs, 40,960 shots.</p>
```

### 3c. Optional "version notes" / changelog field, if you use one

```
v3 — WITHDRAWS Addendum VI.

The Addendum VI accuracy result (v2, 9 Sept 2026) is withdrawn. It was an
artefact of reporting absolute error only: the pruned computation returned
essentially no signal, and because the true amplitudes are ~1e-4, an output
of near-zero registered as a small absolute error. The headline w=20 figure
reproduces exactly (1.459e-4 on 104 of 1,048,576 configurations), but
max|exact| at that point is 1.4685e-4 — a relative error of 99.4%.

Also withdrawn: "error improves monotonically with width" (absolute error was
tracking the shrinking amplitude scale, not approximation quality), and the
consequence drawn for the classical hardness argument.

Decisively, no threshold both saves work and stays correct: where pruning is
faithful it retains the full frontier; where it removes anything meaningful
the relative error is ~100%.

Adds Addendum VII with the full correction, a read-only audit script that
reproduces it against the unmodified original code, and an independent null
result for the same test on the real ibm_fez heavy-hex topology.

All exact results are unaffected — banded_scaling.py involves no pruning.
The 2^w scaling and measured exponent 1.984 stand. Note the direction:
Addendum VI argued against the study's own hardness claim, so withdrawing it
restores that position.

Addendum VI is preserved unedited so the withdrawn claim remains reproducible
and the correction independently checkable.
```

---

## 4. Checklist — ALL COMPLETE 11/12 Sept 2026

- [x] Push `tbn-protocol` — commits b5ee5e4, 367741e, d3a2ecc
- [x] Push + deploy `hardinai.co.uk` — commit 8d69ee7, GitHub Pages,
      verified live (correction box + 99.4% + 1.4685e-4 serving; old
      "still produced an answer accurate" line gone)
- [x] Zenodo v3 published — version DOI 10.5281/zenodo.22716258,
      concept DOI 10.5281/zenodo.22352839 now resolves to it.
      Verified via API: single v3 zip (90,504 bytes), description contains
      the withdrawal, no longer contains "improves monotonically as width
      grows". Publication date saved as 2026-09-12 (published after
      midnight UTC) — cosmetic, metadata still editable.
- [x] LinkedIn reply posted under own comment (draft 1)
- [x] DM Sophie sent (draft 2)
- [x] Dikran — NOT sent, confirmed 11 Sept. No correction needed.
      **Do not reuse the "Addendum VI vindicates your critique" line** if you
      reply to him later. It no longer does — that line was built on the
      withdrawn numbers. The honest version now: his critique stands on its
      own merits (a circuit engineered against one algorithm's weak spot is a
      narrower claim than beating all classical approaches), and the pruning
      evidence neither supports nor undermines it.
