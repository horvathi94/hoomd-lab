import os
import numpy as np

BASE_DIR = "/hoomd-examples/workdir"
SIMULATIONS_DIR = os.path.join(BASE_DIR, "simulations")
LOG_FILE = os.path.join(SIMULATIONS_DIR, ".current_files.txt")


def random_quaternion() -> list:
    q = np.zeros(4)
    v = np.random.uniform(0, 1, size=3)
    v = v / np.linalg.norm(v)
    s = 0.
    q[0] = s
    q[1:] = v
    return q.tolist()



def place_particle(snap: "Snapshot", placed_particles: int,
                   fixed_position: np.array=None,
                   dmin: float=0., maxiter: int=1e3) -> None:
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

