import numpy as np
import hoomd
import hoomd.md
from .simulation import Simulation
from . import log
from . import utils
from .yaml_keys import SimType
from .snapshot import create_snapshot


def mdrun(sim: Simulation, gpu: int, overwrite: bool=True) -> None:

    # Write logs
    sim.try_minting()
    Parser.write(sim, sim.project_file)
    log.log_current_file(sim.project_file, gpu)


    # Init context
    np.random.seed(sim.seed)
    hoomd.context.initialize(f"--gpu={gpu}")


    # Create starting snapshot
    snapshot = create_snapshot(sim)


    # Init system
    hoomd_sys = hoomd.init.read_snapshot(snapshot)


    # Create rigid bodies
    rigid = hoomd.md.constrain.rigid()
    for rbdata in sim.rigidbodies:
        rb = rbdata["rb"]
        center_label = rb.get_center().label
        aux = rb.get_non_center()
        types = [p.label for p in aux]
        positions = [p.position for p in aux]
        charges = [p.q for p in aux]
        rigid.set_param(center_label, types=types,
                        positions=positions, charges=charges)
    rigid.create_bodies()


    # Interactions
    nl = hoomd.md.nlist.cell()
    lj = hoomd.md.pair.lj(r_cut=6, nlist=nl)

    for i in sim.interactions:
        lj.pair_coeff.set(i.p1_label, i.p2_label,
                          epsilon=i.epsilon, sigma=i.sigma, alpha=i.alpha)


    # PPPM
    pppm = hoomd.md.charge.pppm(hoomd.group.charged(), nlist=nl)
    pppm.set_params(Nx=64, Ny=64, Nz=64, order=4, rcut=6, alpha=0)



    # Integrator
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


    # Logging
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


    # Run simulation
    hoomd.run(sim.duration)
