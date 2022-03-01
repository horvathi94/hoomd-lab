import numpy as np
import hoomd
import hoomd.md
import datetime
from . import utils
from .simulation import Simulation
from .parser import Parser
from . import log


def run(sim: Simulation, gpu: int, overwrite: bool=True) -> None:

    sim.mint()
    Parser.write(sim, sim.project_file)
    log.log_current_file(sim.project_file, gpu)


    # Init context
    np.random.seed(sim.seed)
    hoomd.context.initialize(f"--gpu={gpu}")


    # Create snapshot
    box = hoomd.data.boxdim(Lx=sim.box.Lx, Ly=sim.box.Ly, Lz=sim.box.Lz)
#    snapshot = hoomd.data.make_snapshot(N=sim.count_center_particles(),
#                                        box=box)
    snapshot = hoomd.data.make_snapshot(N=sim.N, box=box)
    snapshot.particles.types = sim.types_list


    # --- Add particles:
    for i, rb in enumerate(sim.list_rigidbodies()):
        p = rb.get_center()
        snapshot.particles.typeid[i] = sim.types_list.index(p.label)
        snapshot.particles.charge[i] = p.q
        snapshot.particles.orientation[i] = utils.random_quaternion()
        snapshot.particles.diameter[i] = p.diam
        snapshot.particles.moment_inertia[i] = rb.moment_of_inertia
        utils.place_particle(snapshot, i,
                             fixed_position=rb.fixed_position, dmin=4.)


    # --- Add solvent:
    for j, sol in enumerate(sim.list_solvents()):
        indx = i + j + 1
        snapshot.particles.typeid[indx] = sim.types_list.index(sol.label)
        snapshot.particles.charge[i] = sol.q
        snapshot.particles.orientation[i] = utils.random_quaternion()
        snapshot.particles.diameter[i] = sol.diam
        snapshot.particles.moment_inertia[i] = [1, 1, 1]
        utils.place_particle(snapshot, indx, dmin=4.)


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
    sim_group = rigid_group
    if sim.has_solvent():
        for sol in sim.solvents:
            solvent_group = hoomd.group.type(sol["sol"].label)
            sim_group = hoomd.group.union(name="rigid_and_solvent",
                                          a=sim_group, b=solvent_group)
    integrator = hoomd.md.integrate.langevin(group=sim_group,
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
