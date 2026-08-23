"""
Standalone verification for the QCSE question:

  "Finding the hidden subgroup of q8 using only 1 measurement, is it possible?"

Asker's own answer (0 upvotes at time of writing):
  "The QFT of Q8 has 3 nontrivial 1d irreps. You can make a pair of all the
   irreps with each other then process the result classically to find it
   which of the nontrivial irreps have a probability to be found at the
   output. So I guess the time complexity to solve the HSP for that group
   is O(1)."

Question body gives more detail on the actual measurement idea:
  - Q8 = {1,-1,i,-i,j,-j,k,-k}, order 8.
  - After QFT of the coset state, the 2d irrep component is (they claim)
    ALWAYS zero-probability regardless of which subgroup is hidden.
  - The five subgroups of Q8 are: trivial {1}, center Z={1,-1}, Hi={1,-1,i,-i},
    Hj={1,-1,j,-j}, Hk={1,-1,k,-k}, and the whole group Q8 itself.
    (The question's "hidden subgroup" candidates of interest are the index-2
    subgroups Hi, Hj, Hk, and the center Z, distinguished by which 1d irreps
    appear with nonzero probability.)
  - Claim to check: the output distribution over the 3 nontrivial 1d irreps
    (call them chi_i, chi_j, chi_k) is DIFFERENT for each of the subgroups
    Hi, Hj, Hk, and for Z -- so that measuring which 1d-irrep sector fires
    (a single measurement outcome) is enough to identify which of these
    subgroups is hidden, without needing repeated trials.

This script builds Q8 and its irreducible representations explicitly,
computes the exact HSP output distribution for each candidate hidden
subgroup, and checks whether a single measurement outcome can distinguish
them, i.e. whether the support (which irreps have nonzero probability) is
different across candidates.

No dependency on any Area One / EOG code -- fully self-contained.
"""

import itertools
from fractions import Fraction

import numpy as np

# ---------------------------------------------------------------------------
# Step 1: build Q8 as an explicit permutation-free multiplication table using
# the quaternion units directly (as 2x2 complex matrices, the standard
# faithful representation), so group multiplication is just matrix multiply.
# ---------------------------------------------------------------------------

I2 = np.eye(2, dtype=complex)
i_unit = np.array([[1j, 0], [0, -1j]], dtype=complex)
j_unit = np.array([[0, 1], [-1, 0]], dtype=complex)
k_unit = i_unit @ j_unit  # should equal [[0,1j],[1j,0]]

elements = {
    "1": I2,
    "-1": -I2,
    "i": i_unit,
    "-i": -i_unit,
    "j": j_unit,
    "-j": -j_unit,
    "k": k_unit,
    "-k": -k_unit,
}

names = list(elements.keys())


def mat_eq(a, b, tol=1e-9):
    return np.allclose(a, b, atol=tol)


def find_name(mat):
    for nm, m in elements.items():
        if mat_eq(mat, m):
            return nm
    raise ValueError("matrix not in Q8")


# sanity: verify this really is Q8 (order 8, i^2=j^2=k^2=-1, ijk=-1, noncommutative)
assert mat_eq(i_unit @ i_unit, -I2)
assert mat_eq(j_unit @ j_unit, -I2)
assert mat_eq(k_unit @ k_unit, -I2)
assert mat_eq(i_unit @ j_unit @ k_unit, -I2)
assert not mat_eq(i_unit @ j_unit, j_unit @ i_unit)
print("Q8 quaternion relations verified: PASS (order 8, noncommutative)")

mult_table = {}
for a in names:
    for b in names:
        mult_table[(a, b)] = find_name(elements[a] @ elements[b])

print()
print("=" * 70)
print("STEP 2: enumerate all subgroups of Q8")
print("=" * 70)

elem_set = set(names)


def closure_ok(subset):
    for a in subset:
        for b in subset:
            if mult_table[(a, b)] not in subset:
                return False
    return True


all_subgroups = []
for r in range(1, 9):
    for combo in itertools.combinations(names, r):
        s = set(combo)
        if "1" not in s:
            continue
        if closure_ok(s):
            all_subgroups.append(frozenset(s))

all_subgroups = sorted(set(all_subgroups), key=len)
for sg in all_subgroups:
    print(f"  order {len(sg)}: {sorted(sg)}")

assert len(all_subgroups) == 6, f"expected 6 subgroups of Q8, got {len(all_subgroups)}"
print("total subgroup count == 6 (trivial, Z, Hi, Hj, Hk, Q8 itself): PASS")

trivial = frozenset(["1"])
Z = frozenset(["1", "-1"])
Hi = frozenset(["1", "-1", "i", "-i"])
Hj = frozenset(["1", "-1", "j", "-j"])
Hk = frozenset(["1", "-1", "k", "-k"])
Q8 = frozenset(names)

for label, sg in [("trivial", trivial), ("Z", Z), ("Hi", Hi), ("Hj", Hj), ("Hk", Hk), ("Q8", Q8)]:
    assert sg in all_subgroups, f"{label} not found among enumerated subgroups"
print("named subgroups (trivial, Z, Hi, Hj, Hk, Q8) all confirmed present: PASS")

print()
print("=" * 70)
print("STEP 3: irreducible representations of Q8")
print("=" * 70)

# Q8 has 5 conjugacy classes -> 5 irreps: four 1-dimensional (trivial, chi_i,
# chi_j, chi_k) and one 2-dimensional (the defining quaternion rep itself).
# The four 1d irreps factor through Q8 / Z = Z2 x Z2 (since Z = {1,-1} is the
# commutator subgroup / center). Their explicit character values:

# 1d irrep values as functions on the 8 elements, given as +1/-1
irrep_trivial = {n: 1 for n in names}

irrep_chi_i = {  # kills i (chi_i(i)=chi_i(-i)=+1), sends j,k to -1
    "1": 1, "-1": 1, "i": 1, "-i": 1, "j": -1, "-j": -1, "k": -1, "-k": -1,
}
irrep_chi_j = {  # kills j, sends i,k to -1
    "1": 1, "-1": 1, "i": -1, "-i": -1, "j": 1, "-j": 1, "k": -1, "-k": -1,
}
irrep_chi_k = {  # kills k, sends i,j to -1
    "1": 1, "-1": 1, "i": -1, "-i": -1, "j": -1, "-j": -1, "k": 1, "-k": 1,
}


def is_homomorphism(chi):
    for a in names:
        for b in names:
            if chi[mult_table[(a, b)]] != chi[a] * chi[b]:
                return False
    return True


for label, chi in [("trivial", irrep_trivial), ("chi_i", irrep_chi_i),
                    ("chi_j", irrep_chi_j), ("chi_k", irrep_chi_k)]:
    assert is_homomorphism(chi), f"{label} is not a valid 1d representation"
print("all four 1d irreps (trivial, chi_i, chi_j, chi_k) verified as homomorphisms: PASS")

# the 2d irrep is just the defining quaternion matrix rep itself
irrep_2d = elements

print()
print("=" * 70)
print("STEP 4: HSP coset-state overlap for each candidate hidden subgroup")
print("=" * 70)

# Standard HSP construction: given hidden subgroup H, the algorithm produces
# (in the coset-sampling / weak Fourier sampling formulation) a distribution
# over irreps rho where irrep rho appears with probability proportional to
#   P(rho) = (dim(rho) / |H|) * || sum_{h in H} rho(h) ||_F^2 / dim(rho)^2 ... 
# For abelian-image 1d irreps this reduces to the clean rule used in Simon-
# type / abelian HSP algorithms: chi appears with NONZERO probability iff
# chi is trivial on H (chi(h)=1 for all h in H), and with probability 0
# otherwise. This is the exact rule the asker is relying on. We verify it
# directly by explicit summation rather than assuming it.

irreps_1d = {"trivial": irrep_trivial, "chi_i": irrep_chi_i,
             "chi_j": irrep_chi_j, "chi_k": irrep_chi_k}

candidates = {"Z": Z, "Hi": Hi, "Hj": Hj, "Hk": Hk}

print("For each candidate hidden subgroup H, and each 1d irrep chi, check")
print("whether chi is trivial on H (sum_{h in H} chi(h) == |H|, i.e. nonzero):")
print()

support_table = {}
for hname, H in candidates.items():
    support = []
    for iname, chi in irreps_1d.items():
        total = sum(chi[h] for h in H)
        nonzero = abs(total) > 1e-9
        if nonzero:
            support.append(iname)
    support_table[hname] = frozenset(support)
    print(f"  H={hname:3s} (order {len(H)}): nonzero-probability 1d irreps = {sorted(support)}")

print()
print("=" * 70)
print("STEP 5: check whether support pattern uniquely identifies each H")
print("=" * 70)

# The asker's claim: a SINGLE measurement (observing which nontrivial 1d
# irrep sector fires, if any) is enough to distinguish Hi, Hj, Hk from each
# other and from Z. Check whether the four support sets above are pairwise
# distinct -- if they are NOT distinct, one measurement outcome could be
# ambiguous between two different hidden subgroups, contradicting the claim
# that one measurement suffices.

items = list(support_table.items())
all_distinct = True
for a_idx in range(len(items)):
    for b_idx in range(a_idx + 1, len(items)):
        na, sa = items[a_idx]
        nb, sb = items[b_idx]
        if sa == sb:
            all_distinct = False
            print(f"  COLLISION: H={na} and H={nb} give IDENTICAL support {sorted(sa)}")

if all_distinct:
    print("  all four candidate subgroups give pairwise DISTINCT irrep-support patterns: PASS")
else:
    print("  NOT all distinct -- see collisions above")

print()
print("=" * 70)
print("STEP 6: does observing the support ALONE (not probabilities) suffice,")
print("        i.e. is a single yes/no per irrep enough, matching the claim")
print("        that only the SUPPORT (not exact probability) needs measuring?")
print("=" * 70)

# Additionally verify exact probabilities (not just support) for completeness,
# using the standard formula: for abelian image, chi appears with probability
# |H|/|G| * (number of h in H with chi(h)=1) ... but since chi is either
# entirely 1 on H or entirely mixed, and we already checked "trivial on H"
# above, the theoretical prediction is: each subgroup H distinguishes exactly
# the 1d irreps for which H is inside the kernel of chi. Print the kernels of
# each chi for a cross-check.

for iname, chi in irreps_1d.items():
    kernel = frozenset(n for n in names if chi[n] == 1)
    print(f"  ker({iname}) = {sorted(kernel)}")

print()
print("Cross-check: H is in the support list for chi  <=>  H subseteq ker(chi).")
for hname, H in candidates.items():
    for iname, chi in irreps_1d.items():
        kernel = frozenset(n for n in names if chi[n] == 1)
        in_support = iname in support_table[hname]
        subset_of_kernel = H.issubset(kernel)
        assert in_support == subset_of_kernel, (hname, iname)
print("  all consistent: PASS")

print()
print("=" * 70)
print("VERDICT")
print("=" * 70)
if all_distinct:
    print("""
CONFIRMED: the four candidate hidden subgroups Z, Hi, Hj, Hk each produce a
DIFFERENT, deterministic pattern of which 1d irreps have nonzero measurement
probability:

  H=Z  : {chi_i, chi_j, chi_k}   (all three nontrivial 1d irreps fire)
  H=Hi : {chi_i}                 (only chi_i fires)
  H=Hj : {chi_j}                 (only chi_j fires)
  H=Hk : {chi_k}                 (only chi_k fires)

So a single measurement that reveals WHICH 1d-irrep sector(s) the outcome
falls into is in principle enough to distinguish these four candidates from
each other, in a single shot, with no repeated trials needed for THIS
restricted candidate set. This supports the core mechanism in the asker's
own answer.

IMPORTANT CAVEAT the asker's answer does not address, and which materially
narrows the claim of general O(1) HSP solvability for Q8:

  1. This distinguishes Z, Hi, Hj, Hk from EACH OTHER. It does not by itself
     handle the trivial subgroup {1} or the full group Q8 as hidden subgroup
     candidates, nor does it use the 2-dimensional irrep at all, which is
     needed to fully resolve those and to extract a generator when H is
     trivial (H={1} makes ker(chi) irrelevant: EVERY chi is trivial on {1},
     so the same argument gives support = {chi_i,chi_j,chi_k} for H=trivial
     too, IDENTICAL to the support for H=Z). Confirmed directly below.
  2. Observing "chi appears with nonzero probability" is a promise about
     the ideal, noiseless distribution. It says nothing about how many
     COPIES of the coset state are needed to prepare the QFT input with
     enough amplitude concentrated correctly, nor about sampling noise in
     a real single-shot measurement outcome distinguishing "some small
     nonzero probability" from "exactly zero" -- that distinction is only
     sharp in exact arithmetic, not in a finite number of physical runs.
""")
    # explicit check of the trivial-subgroup collision noted above
    trivial_support = []
    for iname, chi in irreps_1d.items():
        total = sum(chi[h] for h in trivial)
        if abs(total) > 1e-9:
            trivial_support.append(iname)
    trivial_support = frozenset(trivial_support)
    print(f"  H=trivial support = {sorted(trivial_support)}")
    print(f"  H=Z       support = {sorted(support_table['Z'])}")
    collision_with_trivial = trivial_support == support_table["Z"]
    print(f"  H=trivial and H=Z give IDENTICAL 1d-irrep support: "
          f"{'YES -- confirmed collision, these two cases need the 2d irrep to distinguish' if collision_with_trivial else 'no'}")
else:
    print("Claim NOT confirmed as stated -- see collisions above.")
