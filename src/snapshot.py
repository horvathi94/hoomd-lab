import hoomd
import gsd.hoomd
from .simulation import Simulation
from . import utils


def fresh_snapshot(sim: Simulation) -> "snapshot":
    box = hoomd.data.boxdim(Lx=sim.box.Lx, Ly=sim.box.Ly, Lz=sim.box.Lz)
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

    return snapshot



def is_center(label: str, center_particles: list) -> bool:
    for p in center_particles:
        if p.label == label: return True
    return False


def continue_snapshot(sim: Simulation) -> "snapshot":

    trajectory_file = None
    if sim.is_fork():
        trajectory_file = sim.base_trajectory
    elif sim.is_continue():
        trajectory_file = sim.trajectory_file

    if trajectory_file is None:
        raise Exception("Trajectory file was not specified.")

    trajectory = gsd.hoomd.open(trajectory_file)
    struct0 = trajectory.read_frame(sim.start_from)

    N = struct0.particles.N
    Lx, Ly, Lz, *_ = struct0.configuration.box
    center_particles = sim.unique_center_particles()

    N = 0
    for i in range(struct0.particles.N):
        label = struct0.particles.types[struct0.particles.typeid[i]]
        if is_center(label, center_particles): N += 1

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

    return snapshot



def create_snapshot(sim: Simulation) -> "snapshot":

    if sim.is_run():
        return fresh_snapshot(sim)
    if sim.is_continue():
        return continue_snapshot(sim)
    if sim.is_fork():
        return continue_snapshot(sim)
    raise Exception("Error encountered selecting sim type.")
