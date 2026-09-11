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

The record is on Zenodo under concept DOI 10.5281/zenodo.22352839. I'm publishing v3 tonight, and you should know why: it withdraws an addendum I published on the 9th, which means the version you'd have landed on from that link contains a claim I've now retracted.

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

**Upload the whole `demo/eqccm/zenodo_package/` directory.**

Version description:

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

## 4. Checklist

- [ ] Push `tbn-protocol` (record + scripts + package)
- [ ] Push + deploy `hardinai.co.uk` (blog post correction)
- [ ] Zenodo v3 — new version under the same concept DOI
- [ ] LinkedIn reply under own comment (draft 1)
- [ ] DM Sophie (draft 2) — necessary: she was sent the DOI
- [x] Dikran — NOT sent, confirmed 11 Sept. No correction needed.
      **Do not reuse the "Addendum VI vindicates your critique" line** if you
      reply to him later. It no longer does — that line was built on the
      withdrawn numbers. The honest version now: his critique stands on its
      own merits (a circuit engineered against one algorithm's weak spot is a
      narrower claim than beating all classical approaches), and the pruning
      evidence neither supports nor undermines it.
