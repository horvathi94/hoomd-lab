import numpy as np
import hoomd
import hoomd.md
import gsd.hoomd
import datetime
from . import utils
from .simulation import Simulation
from .parser import Parser
from . import log


def is_center(label: str, center_particles: list) -> bool:
    for p in center_particles:
        if p.label == label: return True
    return False


def run(sim: Simulation, gpu: int, overwrite: bool=False) -> None:

    Parser.write(sim, sim.project_file)
    log.log_current_file(sim.project_file, gpu)

    # Init context
    np.random.seed(sim.seed)
    hoomd.context.initialize(f"--gpu={gpu}")


    # Read previous structure
    trajectory = gsd.hoomd.open(sim.trajectory_file)
    last_index = len(trajectory) - 1
    struct0 = trajectory.read_frame(last_index)

    N = struct0.particles.N
    Lx, Ly, Lz, *_ = struct0.configuration.box
    center_particles = sim.unique_center_particles()


    N = 0
    for i in range(struct0.particles.N):
        label = struct0.particles.types[struct0.particles.typeid[i]]
        if is_center(label, center_particles): N += 1


    # Create snapshot
    box = hoomd.data.boxdim(Lx=sim.box.Lx, Ly=sim.box.Ly, Lz=sim.box.Lz)
    snapshot = hoomd.data.make_snapshot(N=N, box=box)

    snapshot.particles.types = struct0.particles.types
    for i in range(struct0.particles.N):
        label = struct0.particles.types[struct0.particles.typeid[i]]
        if not is_center(label, center_particles): continue
        snapshot.particles.typeid[i] = struct0.particles.typeid[i]
        snapshot.particles.position[i] = struct0.particles.position[i]
        snapshot.particles.charge[i] = struct0.particles.charge[i]
        snapshot.particles.diameter[i] = struct0.particles.diameter[i]
        snapshot.particles.orientation[i] = struct0.particles.orientation[i]
        snapshot.particles.moment_inertia[i] = \
            struct0.particles.moment_inertia[i]


    # Init system
    hoomd_sys = hoomd.init.read_snapshot(snapshot)
    rigid = hoomd.md.constrain.rigid()

    # --- Rigid bodies

    for rbdata in sim.rigidbodies:
        rb = rbdata["rb"]
        center_label = rb.get_center().label
        aux = rb.get_non_center()
        types = [p.label for p in aux]
        positions = [p.position for p in aux]
        charges = [p.q for p in aux]
        rigid.set_param(center_label, types=types,
                        positions=positions,
                        charges=charges)

    rigid.create_bodies()


    # --- Interactions
    nl = hoomd.md.nlist.cell()
    lj = hoomd.md.pair.lj(r_cut=6, nlist=nl)

    for i in sim.interactions:
        lj.pair_coeff.set(i.p1_label, i.p2_label,
                          epsilon=i.epsilon, sigma=i.sigma, alpha=i.alpha)


    # --- PPPM
    pppm = hoomd.md.charge.pppm(hoomd.group.charged(), nlist=nl)
    pppm.set_params(Nx=64, Ny=64, Nz=64, order=4, rcut=6, alpha=0)


    # --- Integrator
    hoomd.md.integrate.mode_standard(dt=sim.dt)
    rigid_group = hoomd.group.rigid_center()
    integrator = hoomd.md.integrate.langevin(group=rigid_group,
                                             kT=sim.kT, seed=sim.seed)


    # --- Logging
    quantities = ["potential_energy", "translational_kinetic_energy",
                  "rotational_kinetic_energy"]
    hoomd.analyze.log(filename=sim.log_file,
                      quantities=quantities,
                      period=sim.period,
                      overwrite=overwrite)
    hoomd.dump.gsd(sim.trajectory_file,
                   period=sim.period,
                   group=hoomd.group.all(),
                   overwrite=overwrite)

    # --- Run
    hoomd.run(sim.duration)
