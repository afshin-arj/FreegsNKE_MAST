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

# Second inverse solve: limited plasma 
# first we specify some alterantive constraints
Rmid = 1.4   # outboard midplane radius
Rin = 0.24   # inboard midplane radius

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

# let's seek an up-down symmetric equilibrium by imposing the current in P6 is zero
#eq.tokamak['P6'].current = 0
#eq.tokamak['P6'].control = False # fixes the current

# let's assume we're also seeking an equilibrium with no solenoid current
eq.tokamak['Solenoid'].current = 0
eq.tokamak['Solenoid'].control = False # fixes the current

# pass the magnetic constraints to a new constrain object
constrain = freegs4e.control.constrain(xpoints=xpoints,
                                         isoflux=isoflux,
                                         gamma=1e-7,
                                        )

# modify the total plasma current
profiles.Ip = 7e5

# modify the pressure on the magnetic axis
profiles.paxis = 6e3

# carry out the inverse solve (which finds the coil currents)
GSStaticSolver.solve(eq=eq, 
                     profiles=profiles, 
                     constrain=constrain, 
                     target_relative_tolerance=1e-3)

# # one can also carry out a forward solve to obtain a "more converged" equilibrium
# GSStaticSolver.solve(eq=eq, 
#                      profiles=profiles, 
#                      constrain=None, 
#                      target_relative_tolerance=1e-9)


# save the currents for later use
inverse_current_values = eq.tokamak.getCurrents()

# save coil currents to file
simple_limited_currents_PaxisIp_path = os.path.join(pickle_out_dir, "simple_limited_currents_PaxisIp.pk")
with open(simple_limited_currents_PaxisIp_path, 'wb') as f:
    pickle.dump(obj=inverse_current_values, file=f)


# --- Define output directory for output plots ---
current_dir = os.path.dirname(os.path.abspath(__file__))
plot_out_dir = os.path.join(current_dir, "MAST", "plots", "limiter")

# Create the directory if it doesn't exist
os.makedirs(plot_out_dir, exist_ok=True)

# plot the resulting equilbria 
fig1, ax1 = plt.subplots(1, 1, figsize=(4, 8), dpi=80)
ax1.grid(True, which='both')
eq.plot(axis=ax1, show=False)
eq.tokamak.plot(axis=ax1, show=False)
constrain.plot(axis=ax1,show=False)
ax1.set_xlim(0.1, 2.15)
ax1.set_ylim(-2.25, 2.25)
ax1.set_xlabel("R (m)")
ax1.set_ylabel("Z (m)")
ax1.legend()
plt.tight_layout()
# Save the figure
fig_path = os.path.join(plot_out_dir, "equilibrium_limiter_1.png")
fig1.savefig(fig_path, dpi=300)
# plt.show()

# we first raise the solenoid current to some intermediate value
# Note that `eq.tokamak['Solenoid'].control = False` is still set from above so we don't need it again
eq.tokamak['Solenoid'].current = 10000

# carry out a first inverse solve
GSStaticSolver.solve(eq=eq, 
                     profiles=profiles, 
                     constrain=constrain, 
                     target_relative_tolerance=1e-3,
                     picard=True,
                     verbose=False
)

# raise the solenoid current further
eq.tokamak['Solenoid'].current = 40000

# carry out another inverse solve
GSStaticSolver.solve(eq=eq, 
                     profiles=profiles, 
                     constrain=constrain, 
                     target_relative_tolerance=1e-3,
                     picard=True,
                     verbose=False
                     )

# # can do a forward solve here if you wish
# GSStaticSolver.solve(eq=eq, 
#                      profiles=profiles, 
#                      constrain=None, 
#                      target_relative_tolerance=1e-9)

# plot the resulting equilbria 
fig1, ax1 = plt.subplots(1, 1, figsize=(4, 8), dpi=80)
ax1.grid(True, which='both')
eq.plot(axis=ax1, show=False)
eq.tokamak.plot(axis=ax1, show=False)
constrain.plot(axis=ax1,show=False)
ax1.set_xlim(0.1, 2.15)
ax1.set_ylim(-2.25, 2.25)
ax1.set_xlabel("R (m)")
ax1.set_ylabel("Z (m)")
ax1.legend()
plt.tight_layout()
# Save the figure
fig_path = os.path.join(plot_out_dir, "equilibrium_limiter_2.png")
fig1.savefig(fig_path, dpi=300)
# plt.show()
