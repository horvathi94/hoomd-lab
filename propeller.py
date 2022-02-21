import numpy as np
import hoomd
import hoomd.md
import utils
import datetime

# Script parameters:
PROJECT_NAME = "propeller"
GPU = 1
SEED = 42
RUNTIME = 1e5
DT = 0.05
KT = 0.01
PERIOD = 1e3
OVERWRITE_LOGS = False


# Particle data
particles = {
    "A": {"q":  6, "m": 1, "2r": 1},
    "B": {"q":  0, "m": 1, "2r": 1},
    "C": {"q": -1, "m": 1, "2r": 1},
    "D": {"q":  0, "m": 1, "2r": 1},
}

N_A = 7
N_D = 21
N = N_A + N_D



# Init context
np.random.seed(SEED)
hoomd.context.initialize(f"--gpu={GPU}")


# Create snapshot
box = hoomd.data.boxdim(Lx=50, Ly=50, Lz=50)
snapshot = hoomd.data.make_snapshot(N=N, box=box)
center_particles = ["A"]*N_A + ["D"]*N_D


# --- Add particles:
type_list = list(particles.keys())
snapshot.particles.types = type_list
for i in range(snapshot.particles.N):
    label = center_particles[i]
    snapshot.particles.typeid[i] = type_list.index(label)
    snapshot.particles.charge[i] = particles[label]["q"]
    snapshot.particles.orientation[i] = [1,0,0,0]
    snapshot.particles.diameter[i] = particles[label]["2r"]
utils.randomly_place_particles(snapshot, dmin=2.)


# Init system
hoomd_sys = hoomd.init.read_snapshot(snapshot)
rigid = hoomd.md.constrain.rigid()

# --- Rigid bodies
rigid.set_param("A", types=["B", "B"],
                positions=[[0, 0, -1], [0, 0, 1]],
                charges=[particles["B"]["q"], particles["B"]["q"]])
rigid.set_param("D", types=["C", "C"],
                positions=[[-1.5, 0, 0], [1.5, 0, 0]],
                charges=[particles["C"]["q"], particles["C"]["q"]])
rigid.create_bodies()


# --- Interactions
nl = hoomd.md.nlist.cell()
lj = hoomd.md.pair.lj(r_cut=6, nlist=nl)
lj.pair_coeff.set(["A", "B"], ["A", "B"], epsilon=10, sigma=1, alpha=0)
lj.pair_coeff.set(["A", "B"], ["C", "D"], epsilon=10, sigma=1, alpha=0)
lj.pair_coeff.set(["C", "D"], ["C", "D"], epsilon=10, sigma=1, alpha=0)


# --- PPPM
pppm = hoomd.md.charge.pppm(hoomd.group.charged(), nlist=nl)
pppm.set_params(Nx=64, Ny=64, Nz=64, order=4, rcut=6, alpha=0)


# --- Integrator
hoomd.md.integrate.mode_standard(dt=DT)
rigid_group = hoomd.group.rigid_center()
integrator = hoomd.md.integrate.langevin(group=rigid_group, kT=KT, seed=SEED)


# --- Logging
now = datetime.datetime.now().strftime("%Y%m%d_%H%M%s")
quantities = ["potential_energy", "translational_kinetic_energy",
              "rotational_kinetic_energy"]
fname = f"{PROJECT_NAME}_{now}"
hoomd.analyze.log(filename=f"./simulations/{fname}.log",
                  quantities=quantities,
                  period=PERIOD,
                  overwrite=OVERWRITE_LOGS)
hoomd.dump.gsd(f"./simulations/{fname}.gsd",
               period=PERIOD,
               group=hoomd.group.all(),
               overwrite=OVERWRITE_LOGS)


# --- Run
hoomd.run(RUNTIME)
