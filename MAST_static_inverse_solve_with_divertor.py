import os
import matplotlib.pyplot as plt
import freegs4e
import numpy as np
import freegs4e
import pickle



# --- Define output directory for pickle files ---
current_dir = os.path.dirname(os.path.abspath(__file__))
pickle_out_dir = os.path.join(current_dir, "MAST", "pickle")

# The static free-boundary Grad-Shafranov problem
# Set paths to configuration pickle files.
# (Make sure these paths match where your pickle files are located.)
os.environ["ACTIVE_COILS_PATH"] = os.path.join(pickle_out_dir, "active_coils.pickle")
os.environ["PASSIVE_COILS_PATH"] = os.path.join(pickle_out_dir, "passive_coils.pickle")
os.environ["WALL_PATH"] = os.path.join(pickle_out_dir, "wall.pickle")
os.environ["LIMITER_PATH"] = os.path.join(pickle_out_dir, "limiter.pickle")
# os.environ["PROBE_PATH"] = "../machine_configs/example/magnetic_probes.pickle"


# Now the machine can actually be built:
from freegsnke import build_machine
tokamak = build_machine.tokamak()

from freegsnke import equilibrium_update

eq = equilibrium_update.Equilibrium(
    tokamak=tokamak,       # provide tokamak object
    Rmin=0.01, Rmax=2.2,   # radial range
    Zmin=-2.5, Zmax=2.5,   # vertical range
    nx=257,                # number of grid points in the radial direction (needs to be of the form (2**n + 1) with n being an integer)
    ny=513,                # number of grid points in the vertical direction (needs to be of the form (2**n + 1) with n being an integer)
    # psi=plasma_psi
)

# initialise the profiles
from freegsnke.jtor_update import ConstrainPaxisIp
profiles = ConstrainPaxisIp(
    eq=eq,        # equilibrium object
    paxis=8e3,    # profile object
    Ip=7e5,       # plasma current
    fvac=0.4,     # fvac = rB_{tor}
    alpha_m=1.9,  # profile function parameter
    alpha_n=1.4   # profile function parameter
)

from freegsnke import GSstaticsolver
GSStaticSolver = GSstaticsolver.NKGSsolver(eq)  

# set X-point locations
Rx = 0.58
Zx = 1.24
xpoints = [(Rx, -Zx),   
           (Rx,  Zx)]

# set any desired isoflux constraints with format (R1, Z1, R2, Z2), where (R1, Z1) and (R2, Z2) are 
# desired to be on the same flux contour.
Rmid = 1.4    # outboard midplane radius
Rin = 0.24    # inboard midplane radius
isoflux = [(Rx,Zx, Rx,-Zx),     # link X-points
           (Rmid, 0, Rin, 0.0), # link inner and outer midplane points
           (Rmid, 0, Rx, Zx),   # link outer midplane point and X-point

        # additional isoflux constraints
           (Rmid,0, 1.2,.59),
           (Rmid,0, 1.2,-.59),
           (Rx, Zx, .85, 1.03),
           (Rx, Zx, .75, 1.12),
           (Rx, Zx, 0.45,  1.07),
           (Rx, Zx, Rin, 0.2),
           (Rx, Zx, Rin, 0.1),
           (Rx,-Zx, Rin, -0.1),
           (Rx,-Zx, Rin, -0.2),
           (Rx,-Zx, .85, -1.03),
           (Rx,-Zx, .75, -1.12),
           (Rx,-Zx, 0.45, -1.07),
           ]
           
# instantiate the constrain object
constrain = freegs4e.control.constrain(xpoints=xpoints,
                                         isoflux=isoflux,
                                       # psivals=psivals, # not used
                                         gamma=1e-8       # regularisation factor
                                         )

eq.tokamak['Solenoid'].current = 5000
eq.tokamak['Solenoid'].control = False  # ensures the current in the Solenoid is fixed

GSStaticSolver.solve(eq=eq, 
                     profiles=profiles, 
                     constrain=constrain, 
                     target_relative_tolerance=1e-7,
                     verbose=True, # print output
                     picard=False, # tells solver to use Newton-Krylov iterations (instead of Picard)
                     )

inverse_current_values = eq.tokamak.getCurrents()

# save coil currents to file
simple_diverted_currents_PaxisIp_path = os.path.join(pickle_out_dir, "simple_diverted_currents_PaxisIp.pk")
with open(simple_diverted_currents_PaxisIp_path, 'wb') as f:
    pickle.dump(obj=inverse_current_values, file=f)

# --- Define output directory for output plots ---
current_dir = os.path.dirname(os.path.abspath(__file__))
plot_out_dir = os.path.join(current_dir, "MAST", "plots", "divertor")

# Create the directory if it doesn't exist
os.makedirs(plot_out_dir, exist_ok=True)

# Plot the results
fig1, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 8), dpi=80)

# First plot
ax1.grid(zorder=0, alpha=0.75)
ax1.set_aspect('equal')
eq.tokamak.plot(axis=ax1, show=False)  
ax1.fill(tokamak.wall.R, tokamak.wall.Z, color='k', linewidth=1.2, facecolor='w', zorder=0, label="Limiter")  
ax1.set_xlim(0.0, 2.15)
ax1.set_ylim(-2.5, 2.5)
ax1.set_xlabel("R (m)")
ax1.set_ylabel("Z (m)")
ax1.legend()
ax1.set_title("Tokamak Structure")

# Save first figure
fig1.savefig(os.path.join(plot_out_dir, "figure1.png"), dpi=300)

# Second plot
ax2.grid(zorder=0, alpha=0.75)
ax2.set_aspect('equal')
eq.tokamak.plot(axis=ax2, show=False)  
ax2.fill(tokamak.wall.R, tokamak.wall.Z, color='k', linewidth=1.2, facecolor='w', zorder=0, label="Limiter")  
eq.plot(axis=ax2, show=False)  
ax2.set_xlim(0.0, 2.15)
ax2.set_ylim(-2.5, 2.5)
ax2.set_xlabel("R (m)")
ax2.set_ylabel("Z (m)")
ax2.legend()
ax2.set_title("Equilibrium in Tokamak")

# Save second figure
fig1.savefig(os.path.join(plot_out_dir, "figure2.png"), dpi=300)

# Third plot
ax3.grid(zorder=0, alpha=0.75)
ax3.set_aspect('equal')
eq.tokamak.plot(axis=ax3, show=False)  
ax3.fill(tokamak.wall.R, tokamak.wall.Z, color='k', linewidth=1.2, facecolor='w', zorder=0, label="Limiter")  
eq.plot(axis=ax3, show=False)  
constrain.plot(axis=ax3, show=False)  
ax3.set_xlim(0.0, 2.15)
ax3.set_ylim(-2.5, 2.5)
ax3.set_xlabel("R (m)")
ax3.set_ylabel("Z (m)")
ax3.legend()
ax3.set_title("Equilibrium with Constraints")
plt.tight_layout()
# Save third figure
fig1.savefig(os.path.join(plot_out_dir, "figure3.png"), dpi=300)
# plt.show()
