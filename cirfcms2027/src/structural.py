"""Tier 1: structural diagnosability analysis.

Answers what is possible *in principle*, from the shape of the model alone,
with noise playing no part. Binary answers only. Tier 2 (quantitative) then asks
what is achievable at realistic noise, and the gap between the two is the
paper's result.

Method (Krysander & Frisk, and the structural-analysis FDI literature)
---------------------------------------------------------------------
Write the process as equations over three sets: knowns Z (commanded inputs and
measurements), unknowns X (internal states we never observe), and faults F.

* A subset of equations E has **structural redundancy**
  phi(E) = |E| - (size of a maximum matching between E and the unknowns in E).
  phi > 0 means E contains more equations than unknowns to absorb them, so a
  residual can be formed.
* A **Minimal Structurally Overdetermined (MSO)** set is a minimal subset with
  phi = 1. Each MSO set yields one residual.
* Fault f is **detectable** iff some MSO set contains an equation in which f
  appears.
* Fault f_i is **isolable from** f_j iff some MSO set contains an equation
  carrying f_i and no equation carrying f_j. Equivalently, f_i stays detectable
  in the model with all of f_j's equations removed.

The model here has 11 equations and 8 unknowns, so enumerating all 2^11 subsets
is exact and instant. No need for the clever algorithms the literature uses for
large systems.

Modelling choices are deliberate and are what the result depends on, so they are
documented equation by equation below. Changing them changes the answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

__all__ = ["Equation", "StructuralModel", "LPBF_MODEL", "report"]


@dataclass(frozen=True)
class Equation:
    name: str
    unknowns: frozenset[str]
    faults: frozenset[str] = field(default_factory=frozenset)
    note: str = ""


def eq(name: str, unknowns: str, faults: str = "", note: str = "") -> Equation:
    return Equation(
        name=name,
        unknowns=frozenset(u.strip() for u in unknowns.split(",") if u.strip()),
        faults=frozenset(f.strip() for f in faults.split(",") if f.strip()),
        note=note,
    )


# ---------------------------------------------------------------------------
# The LPBF structural model.
#
# Unknowns (never measured):
#   P_abs   absorbed power at the surface
#   v_act   actual scan speed (commanded speed is known)
#   k_eff   effective conductivity beneath the track
#   T0_loc  local preheat temperature
#   W, D, L melt pool width, depth, length
#   Tp      peak melt pool temperature
#
# Faults:
#   f_P     commanded-vs-delivered laser power deviation
#   f_v     commanded-vs-actual scan speed deviation
#   f_layer thin powder layer from recoater short-feed
#   f_gas   degraded shielding gas flow
#   f_geo   geometry-driven heat accumulation
# ---------------------------------------------------------------------------
LPBF_EQUATIONS = [
    eq("e1_absorbed_power", "P_abs", "f_P, f_layer, f_gas",
       "Delivered power times absorptivity times plume attenuation. f_layer "
       "enters because a thin layer changes absorptivity; f_gas because plume "
       "and spatter attenuate the beam."),
    eq("e2_actual_speed", "v_act", "f_v",
       "Galvo tracking error between commanded and actual speed."),
    eq("e3_effective_conductivity", "k_eff", "f_layer",
       "Powder beneath the track conducts ~100x worse than solid, so layer "
       "thickness sets the effective conductivity."),
    eq("e4_local_preheat", "T0_loc", "f_geo",
       "Thin or overhanging features accumulate heat, raising local preheat."),
    eq("e5_width", "W, P_abs, v_act, k_eff, T0_loc", "",
       "Eagar-Tsai liquidus isotherm, transverse extent."),
    eq("e6_depth", "D, P_abs, v_act, k_eff, T0_loc", "",
       "Eagar-Tsai liquidus isotherm, penetration."),
    eq("e7_length", "L, P_abs, v_act, k_eff, T0_loc", "",
       "Eagar-Tsai liquidus isotherm, longitudinal extent."),
    eq("e8_peak_temperature", "Tp, P_abs, v_act, k_eff, T0_loc", "f_gas",
       "Peak temperature. f_gas enters a second time through surface convection, "
       "which is independent of its attenuation effect in e1."),
    eq("e9_photodiode", "W, D, Tp", "",
       "MEASUREMENT. Band-integrated radiance over the pool."),
    eq("e10_camera", "W, L", "",
       "MEASUREMENT. Melt pool area above the liquidus."),
    eq("e11_pyrometer", "Tp", "",
       "MEASUREMENT. Two-colour ratio, emissivity independent."),
]

FAULTS = ["f_P", "f_v", "f_layer", "f_gas", "f_geo"]


def _max_matching(equations: tuple[Equation, ...]) -> int:
    """Maximum bipartite matching between equations and the unknowns they contain.

    Simple augmenting-path search. The model is tiny, so clarity beats
    Hopcroft-Karp here.
    """
    adjacency = [sorted(e.unknowns) for e in equations]
    matched: dict[str, int] = {}

    def try_assign(i: int, seen: set[str]) -> bool:
        for u in adjacency[i]:
            if u in seen:
                continue
            seen.add(u)
            if u not in matched or try_assign(matched[u], seen):
                matched[u] = i
                return True
        return False

    size = 0
    for i in range(len(equations)):
        if try_assign(i, set()):
            size += 1
    return size


def redundancy(equations: tuple[Equation, ...]) -> int:
    """phi(E) = |E| - max_matching(E). Positive means a residual can be formed."""
    return len(equations) - _max_matching(equations)


@dataclass
class StructuralModel:
    equations: list[Equation]
    faults: list[str]

    def mso_sets(self) -> list[tuple[Equation, ...]]:
        """All minimal subsets with redundancy exactly 1.

        Exhaustive over subset sizes, keeping only those with no
        already-accepted MSO set as a subset (that is what makes them minimal).
        """
        found: list[frozenset[str]] = []
        out: list[tuple[Equation, ...]] = []
        n = len(self.equations)
        for size in range(2, n + 1):
            for combo in combinations(self.equations, size):
                names = frozenset(e.name for e in combo)
                if any(prev <= names for prev in found):
                    continue
                if redundancy(combo) == 1:
                    found.append(names)
                    out.append(combo)
        return out

    def _carries(self, fault: str) -> set[str]:
        return {e.name for e in self.equations if fault in e.faults}

    def detectability(self, msos: list[tuple[Equation, ...]]) -> dict[str, bool]:
        """A fault is detectable iff some MSO set contains one of its equations."""
        result = {}
        for f in self.faults:
            carrying = self._carries(f)
            result[f] = any(carrying & {e.name for e in m} for m in msos)
        return result

    def isolability(self, msos: list[tuple[Equation, ...]]) -> dict[tuple[str, str], bool]:
        """f_i isolable from f_j iff some MSO carries f_i and not f_j.

        Asymmetric by construction: f_i may be isolable from f_j without the
        reverse holding, which is a real and often overlooked asymmetry.
        """
        result = {}
        for fi in self.faults:
            ci = self._carries(fi)
            for fj in self.faults:
                if fi == fj:
                    result[(fi, fj)] = True
                    continue
                cj = self._carries(fj)
                result[(fi, fj)] = any(
                    (ci & {e.name for e in m}) and not (cj & {e.name for e in m})
                    for m in msos
                )
        return result


LPBF_MODEL = StructuralModel(equations=LPBF_EQUATIONS, faults=FAULTS)


def report(model: StructuralModel = LPBF_MODEL) -> None:
    unknowns = sorted({u for e in model.equations for u in e.unknowns})
    print(f"equations {len(model.equations)}   unknowns {len(unknowns)}   "
          f"faults {len(model.faults)}")
    print(f"overall structural redundancy: {redundancy(tuple(model.equations))}")
    print()

    msos = model.mso_sets()
    print(f"MSO sets found: {len(msos)}")
    for m in msos:
        carried = sorted({f for e in m for f in e.faults})
        print(f"   {{{', '.join(e.name.split('_', 1)[0] for e in m)}}}"
              f"   -> sensitive to: {', '.join(carried) if carried else '(none)'}")
    print()

    det = model.detectability(msos)
    print("DETECTABILITY")
    for f, ok in det.items():
        print(f"   {f:9s} {'detectable' if ok else 'NOT detectable'}")
    print()

    iso = model.isolability(msos)
    print("ISOLABILITY  (row isolable FROM column; read across)")
    head = "".join(f"{f:>10s}" for f in model.faults)
    print(f"   {'':9s}{head}")
    for fi in model.faults:
        cells = "".join(f"{('yes' if iso[(fi, fj)] else 'NO'):>10s}" for fj in model.faults)
        print(f"   {fi:9s}{cells}")
    print()

    blocked = [(a, b) for (a, b), ok in iso.items() if not ok and a != b]
    if blocked:
        print("Structurally non-isolable pairs:")
        for a, b in blocked:
            print(f"   {a} cannot be isolated from {b}")
    else:
        print("Every fault pair is structurally isolable.")
        print("This is the expected and important result: structure permits what")
        print("noise may forbid. Tier 2 decides which pairs survive in practice,")
        print("and the gap between the two tiers is the paper's contribution.")


if __name__ == "__main__":
    report()


# ---------------------------------------------------------------------------
# Sensitivity of the structural result to the modelling choices.
#
# The isolability matrix is a consequence of which faults appear in which
# equations, and nothing else. That makes the equation set the single most
# attackable part of Tier 1, so it has to be probed rather than asserted.
#
# Each variant below weakens one physically arguable assumption and reports how
# the answer moves.
# ---------------------------------------------------------------------------

def _variant(name: str, drop: list[tuple[str, str]], description: str) -> None:
    """Rebuild the model with (fault, equation) couplings removed, then report."""
    eqs = []
    for e in LPBF_EQUATIONS:
        removed = {f for f, en in drop if en == e.name}
        eqs.append(Equation(e.name, e.unknowns, e.faults - removed, e.note))
    model = StructuralModel(equations=eqs, faults=FAULTS)
    msos = model.mso_sets()
    iso = model.isolability(msos)
    det = model.detectability(msos)
    blocked = sorted((a, b) for (a, b), ok in iso.items() if not ok and a != b)
    undetectable = sorted(f for f, ok in det.items() if not ok)

    print(f"\n--- {name} ---")
    print(f"    {description}")
    print(f"    MSO sets: {len(msos)}")
    if undetectable:
        print(f"    NOT DETECTABLE: {', '.join(undetectable)}")
    if blocked:
        print("    non-isolable (row from column):")
        for a, b in blocked:
            print(f"      {a} -/-> {b}")
    else:
        print("    every pair isolable")


def sensitivity() -> None:
    print("=" * 70)
    print("SENSITIVITY OF TIER 1 TO MODELLING CHOICES")
    print("=" * 70)

    _variant(
        "baseline",
        [],
        "As specified: f_layer acts on absorptivity and conductivity; f_gas acts "
        "on attenuation and surface convection.",
    )
    _variant(
        "V1: gas flow has no convection effect",
        [("f_gas", "e8_peak_temperature")],
        "Surface convection is weak in LPBF relative to conduction, so f_gas "
        "arguably acts only through beam attenuation. This is the most likely "
        "objection to the baseline.",
    )
    _variant(
        "V2: thin layer has no absorptivity effect",
        [("f_layer", "e1_absorbed_power")],
        "If layer thickness changes only the conduction path and not how much "
        "light is coupled in.",
    )
    _variant(
        "V3: both second routes removed",
        [("f_gas", "e8_peak_temperature"), ("f_layer", "e1_absorbed_power")],
        "Worst case for isolability: every fault acting through a single channel.",
    )
    print()
    print("Reading: a fault is isolable from another only if it has a route to the")
    print("measurements that the other does not share. f_P acts solely through")
    print("absorbed power, so it has no private route - which is why it is the")
    print("fault that loses isolability first under every variant.")
