"""
Useful scripts for initializing.
"""

import numpy as np
import hoomd
import datetime


def randomly_place_particles(snap: "Snapshot", dmin: float=0., maxiter: int=1e2) -> None:
    """Randomly place particles into the snapshot."""

    for i in range(snap.particles.N):

        is_colliding = True
        iteration = 0

        # Generate coordinates untill one is ok
        while is_colliding:

            is_colliding = False
            x = np.random.randint(low=-snap.box.Lx/2., high=snap.box.Lz/2.)
            y = np.random.randint(low=-snap.box.Ly/2., high=snap.box.Ly/2.)
            z = np.random.randint(low=-snap.box.Lz/2., high=snap.box.Lz/2.)
            coords = np.array([x, y, z])

            for j in range(i):
                placed = np.asarray(snap.particles.position[j])
                if np.linalg.norm(coords-placed) <= dmin:
                    is_colliding = True
                    break

            iteration += 1
            if iteration >= maxiter:
                raise Exception("Max. number of iterations reached.")

        snap.particles.position[i] = coords



def place_particle(snap: "Snapshot", placed_particles: int,
                   fixed_position: np.array=None,
                   dmin: float=0., maxiter: int=1e2) -> None:
    """Place a particle into the Snapshot.
    Give random coordinates if None given."""

    is_colliding = True
    iteration = 0

    while is_colliding:

        is_colliding = False
        is_fixed = False

        if fixed_position is not None:
            position = np.asarray(fixed_position)
            is_fixed = True
        else:
            x = np.random.randint(low=-snap.box.Lx/2., high=snap.box.Lz/2.)
            y = np.random.randint(low=-snap.box.Ly/2., high=snap.box.Ly/2.)
            z = np.random.randint(low=-snap.box.Lz/2., high=snap.box.Lz/2.)
            position = np.array([x, y, z])

        for i in range(placed_particles):
            placed = np.asarray(snap.particles.position[i])
            if np.linalg.norm(position - placed) <= dmin:
                if is_fixed:
                    raise Exception("Fixed particles are colliding.")
                is_colliding = True
                break

        iteration += 1
        if iteration >= maxiter:
            raise Exception("Surpased maximum number of iterations.")

    snap.particles.position[placed_particles] = position



def init_snapshot_particle_data(snapshot: "Snapshot",
                                center_particle_types: list,
                                particles: dict) -> None:
    type_list = list(particles.keys())
    snapshot.particles.types = type_list
    for i in range(snapshot.particles.N):
        label = center_particle_types[i]
        snapshot.particles.typeid[i] = type_list.index(label)
        snapshot.particles.charge[i] = particles[label]["charge"]
        snapshot.particles.orientation[i] = [1,0,0,0]
        snapshot.particles.diameter[i] = particles[label]["diameter"]



def init_logfiles(project: str, overwrite=False, period: int=1e3) -> None:
    quantities = ["potential_energy", "translational_kinetic_energy",
                  "rotational_kinetic_energy"]

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%s")
    fname = f"{project}_{now}"
    hoomd.analyze.log(filename=f"./simulaitons/{fname}.log",
                      quantities=quantities,
                      period=period,
                      overwrite=overwrite)
    hoomd.dump.gsd(f"./simulations/{fname}.gsd",
                   period=period,
                   group=hoomd.group.all(),
                   overwrite=overwrite)
