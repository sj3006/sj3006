"""A digital twin, parameterised by everything that can be wrong with it.

The forward model of the earlier papers hard-codes its parameters through module
constants and defaults. A twin experiment needs them as values, so that two
twins differing in one quantity can be compared. `Twin` gathers every quantity
the model depends on into one frozen record and reproduces the model exactly at
its defaults, which `verify.py` checks against `diagnosability.jacobian`.

The fields fall into the three classes of `ROADMAP.md`:

    prediction only   keyhole_c                     depth correction; the sensors
                                                    read the surface and never see it
    diagnosis only    couplings, sigmas,            act only when a fault is nonzero,
                      scattering_k, n_grid          or only through whitening, or
                                                    only in the sensor model
    shared            absorptivity, k, cp,          change both a healthy build and
                      power, speed                  how faults move it

`Twin.prediction_class()` returns that partition programmatically, so the claim
that validation cannot see a diagnosis-only field is a property of the code
rather than of the prose: changing such a field leaves `healthy()` bit-identical.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import noise                                                      # noqa: E402
from calibrate import WEAVER_POINTS                               # noqa: E402
from eagar_tsai import (IN718, IN718_ABSORPTIVITY, IN718_KEYHOLE_C,  # noqa: E402
                        Beam, Material, keyhole_depth, melt_pool_dimensions,
                        sigma_from_spot_diameter)
from faults import FAULT_NAMES, FaultCouplings, FaultState, apply_faults  # noqa: E402
from sensors import SENSOR_NAMES, SensorConfig, sensor_readings  # noqa: E402

__all__ = ["Twin", "TRUTH", "FIELD_CLASS", "STEP"]

#: Central-difference step, as in `diagnosability.jacobian`.
STEP = 0.002

#: Which class each field belongs to; see the module docstring.
FIELD_CLASS = {
    "keyhole_c": "prediction",
    "couplings": "diagnosis",
    "sigmas": "diagnosis",
    "scattering_k": "diagnosis",
    "n_grid": "diagnosis",
    "absorptivity": "shared",
    "k": "shared",
    "cp": "shared",
    "power": "shared",
    "speed": "shared",
}


@dataclass(frozen=True)
class Twin:
    """One forward model, fully specified."""

    name: str = "truth"
    absorptivity: float = IN718_ABSORPTIVITY
    k: float = IN718.k
    cp: float = IN718.cp
    keyhole_c: float = IN718_KEYHOLE_C
    power: float = 285.0
    speed: float = 0.960
    couplings: FaultCouplings = field(default_factory=FaultCouplings)
    sigmas: tuple = tuple(float(s) for s in noise.SIGMAS)
    scattering_k: float = 0.0
    #: Sensor-model quadrature grid. 121 reproduces the earlier papers exactly;
    #: the study uses a finer grid (see LABNOTEBOOK entry 3). Healthy-build
    #: predictions do not depend on it, so it is diagnosis-only.
    n_grid: int = 121

    # ------------------------------------------------------------------ model
    def material(self) -> Material:
        return replace(IN718, k=float(self.k), cp=float(self.cp),
                       name=f"twin {self.name}")

    def beam_material(self, fault: FaultState = FaultState()):
        """The beam and material this twin produces under a fault."""
        beam, material = apply_faults(fault, self.couplings, power=self.power,
                                      speed=self.speed, material=self.material(),
                                      absorptivity=self.absorptivity)
        if self.scattering_k:
            beam = Beam(beam.power, beam.speed,
                        beam.sigma * float(np.exp(self.scattering_k * fault.gas)),
                        beam.absorptivity)
        return beam, material

    def readings(self, fault: FaultState = FaultState()) -> np.ndarray:
        """The three baseline sensor readings, in `SENSOR_NAMES` order."""
        beam, material = self.beam_material(fault)
        r = sensor_readings(beam, material, SensorConfig(n_grid=int(self.n_grid)))
        return np.array([r[s] for s in SENSOR_NAMES], dtype=float)

    def jacobian(self, step: float = STEP) -> np.ndarray:
        """Relative-sensitivity Jacobian, sensors by faults."""
        y0 = self.readings()
        cols = []
        for n in FAULT_NAMES:
            hi = self.readings(FaultState(**{n: step}))
            lo = self.readings(FaultState(**{n: -step}))
            cols.append((hi - lo) / (2.0 * step) / y0)
        return np.column_stack(cols)

    def whitened(self, J: np.ndarray | None = None,
                 sigmas=None) -> np.ndarray:
        """`J / sigma`, with this twin's noise model unless another is given."""
        J = self.jacobian() if J is None else J
        s = np.asarray(self.sigmas if sigmas is None else sigmas, float)
        return J / s[:, None]

    # ------------------------------------------------------------- validation
    def predict_point(self, point) -> dict[str, float]:
        """Width and corrected depth at one AM-Bench condition, healthy build.

        This is exactly what calibration and validation compare with
        measurement. Fault couplings, noise model and scattering cannot enter:
        no fault is present.
        """
        mat = self.material()
        beam = Beam(point.power, point.speed,
                    sigma_from_spot_diameter(point.spot_diameter),
                    self.absorptivity)
        g = melt_pool_dimensions(beam, mat)
        return {"width": float(g["width"]),
                "depth": float(g["depth"] + self.keyhole_c * keyhole_depth(beam, mat)),
                "depth_conduction": float(g["depth"]),
                "keyhole": float(keyhole_depth(beam, mat))}

    def production_point(self):
        """The operating point this twin believes the machine runs at.

        Validation against the AM-Bench data alone cannot catch a wrong belief
        about the production operating point, because those conditions are set
        by the experiment rather than by the twin. A twin in service would also
        be checked against cross-sections taken at the point it is deployed at,
        so that point is part of what `healthy` predicts.
        """
        return type(WEAVER_POINTS[0])(self.power, self.speed, 67e-6,
                                      label="production point")

    def healthy(self, points=WEAVER_POINTS) -> np.ndarray:
        """Predicted width and depth at every validation point, flattened.

        The seven AM-Bench conditions followed by the production point.
        """
        out = []
        for p in list(points) + [self.production_point()]:
            d = self.predict_point(p)
            out += [d["width"], d["depth"]]
        return np.asarray(out, float)

    def amb_errors(self, points=WEAVER_POINTS) -> dict[str, float]:
        """Mean absolute percentage error against the AM-Bench measurements."""
        we, de = [], []
        for p in points:
            d = self.predict_point(p)
            we.append(abs(d["width"] - p.width) / p.width)
            de.append(abs(d["depth"] - p.depth) / p.depth)
        return {"width_mape": 100.0 * float(np.mean(we)),
                "depth_mape": 100.0 * float(np.mean(de)),
                "mape": 100.0 * float(np.mean(we + de))}

    # --------------------------------------------------------------- helpers
    def but(self, name: str, **changes) -> "Twin":
        """This twin with some fields changed and a new name."""
        return replace(self, name=name, **changes)

    @staticmethod
    def prediction_class() -> dict[str, str]:
        return dict(FIELD_CLASS)


TRUTH = Twin()
