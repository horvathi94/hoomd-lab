import numpy as np
import hoomd
import hoomd.md
import utils
import datetime
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
    snapshot = hoomd.data.make_snapshot(N=sim.count_center_particles(),
                                        box=box)

    types_list = [p.label for p in sim.list_unique_particles()]
    snapshot.particles.types = types_list


    # --- Add particles:
    for i, rb in enumerate(sim.list_rigidbodies()):
        p = rb.get_center()
        snapshot.particles.typeid[i] = types_list.index(p.label)
        snapshot.particles.charge[i] = p.q
        snapshot.particles.orientation[i] = [1,0,0,0]
        snapshot.particles.diameter[i] = p.diam
        snapshot.particles.moment_inertia[i] = rb.moment_of_inertia
        utils.place_particle(snapshot, i,
                             fixed_position=rb.fixed_position, dmin=4.)
#    utils.randomly_place_particles(snapshot, dmin=2.)



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