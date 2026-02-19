#!/usr/bin/env python3
# Generated FreeGSNKE static forward replay solve
#
# Author: © 2026 Afshin Arjhangmehr

from pathlib import Path
import pickle
import numpy as np
import matplotlib.pyplot as plt

from freegsnke import build_machine
from freegsnke import equilibrium_update
from freegsnke.jtor_update import ConstrainPaxisIp
from freegsnke import GSstaticsolver

HERE = Path(__file__).resolve().parent
MACHINE = Path({machine_dir!r})
DUMP = HERE / "inverse_dump.pkl"
ACTIVE_CIRCUITS = ["P2_inner","P2_outer","P3","P4","P5","P6","Solenoid"]

def set_active_currents(tokamak, dump):
    cur = dump.get("coil_currents", {})
    for cname, coil in getattr(tokamak, "coils", []):
        if cname in ACTIVE_CIRCUITS and cname in cur and hasattr(coil, "current"):
            coil.current = float(cur[cname])

def main():
    with open(DUMP, "rb") as f:
        dump = pickle.load(f)

    tokamak = build_machine.tokamak(
        active_coils_path=str(MACHINE / "active_coils.pickle"),
        passive_coils_path=str(MACHINE / "passive_coils.pickle"),
        limiter_path=str(MACHINE / "limiter.pickle"),
        wall_path=str(MACHINE / "wall.pickle"),
    )
    set_active_currents(tokamak, dump)

    eq = equilibrium_update.Equilibrium(
        tokamak=tokamak,
        Rmin=0.1, Rmax=2.0,
        Zmin=-2.2, Zmax=2.2,
        nx=65, ny=129,
    )

    pk = dump["profile_kwargs"]
    profiles = ConstrainPaxisIp(
        eq=eq,
        paxis=float(pk["paxis"]),
        Ip=float(pk["Ip"]),
        fvac=float(dump["fvac"]),
        alpha_m=float(pk["alpha_m"]),
        alpha_n=float(pk["alpha_n"]),
    )

    solver = GSstaticsolver.NKGSsolver(eq)
    solver.solve(eq=eq, profiles=profiles, constrain=None, target_relative_tolerance=1e-6, verbose=True)

    fig, ax = plt.subplots(1,1, figsize=(6,10), dpi=140)
    tokamak.plot(axis=ax, show=False)
    eq.plot(axis=ax, show=False)
    ax.set_aspect("equal"); ax.grid(alpha=0.3)
    t0 = dump.get("t0"); Ip = dump.get("Ip")
    if t0 is not None and Ip is not None:
        ax.set_title(f"Forward replay (t0={t0:.3f}s, Ip={Ip/1e6:.3f}MA)")
    else:
        ax.set_title("Forward replay")
    fig.tight_layout()
    fig.savefig(HERE/"forward_equilibrium.png", dpi=250, bbox_inches="tight")
    print("Saved forward_equilibrium.png")

if __name__ == "__main__":
    main()
