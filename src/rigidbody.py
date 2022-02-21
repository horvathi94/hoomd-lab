import numpy as np
from typing import List
from dataclasses import dataclass, field
from .particle import Particle


class Iterator:

    def __init__(self, particles: list):
        self._particles = particles
        self._index = 0


    def __next__(self):
        if self._index < len(self._particles):
            self._index += 1
            return self._particles[self._index-1]
        self._index = 0
        raise StopIteration




@dataclass
class RigidBody:

    label: str
    _particles: List[Particle] = field(default_factory=lambda: [])
    fixed_pos_x: float = None
    fixed_pos_y: float = None
    fixed_pos_z: float = None


    def __getitem__(self, index) -> Particle:
        if index >= len(self._particles):
            raise IndexError
        return self._particles[index]


    def __iter__(self):
        return Iterator(self._particles)


    def add_particle(self, p: Particle, pos: np.array,
                     is_center: bool=False) -> None:
        toadd = p.copy()
        toadd.position = pos
        toadd.is_center = is_center
        self._particles.append(toadd)


    @property
    def fixed_position(self) -> np.array:
        if self.fixed_pos_x is None: return None
        if self.fixed_pos_y is None: return None
        if self.fixed_pos_z is None: return None
        return np.array([self.fixed_pos_x, self.fixed_pos_y, self.fixed_pos_z])


    @fixed_position.setter
    def fixed_position(self, fp: List[float]) -> None:
        if fp is None:
            self.fixed_pos_x = None
            self.fixed_pos_y = None
            self.fixed_pos_z = None
        if len(fp) != 3: raise Exception("Unable to set fixed position")
        self.fixed_pos_x, self.fixed_pos_y, self.fixed_pos_z = fp


    def is_fixed(self) -> bool:
        if self.fixed_position is not None: return True
        return False


    def list_unique_particles(self) -> List[Particle]:
        unique = []
        for p in self:

            is_reg = False

            if len(unique) > 0:
                for up in unique:
                    if p == up:
                        is_reg = True
                        break

            if not is_reg:
                unique.append(p)

        return unique


    def get_center(self) -> Particle:
        for p in self:
            if p.is_center: return p
        raise Exception("No center particle found.")


    def get_non_center(self) -> List[Particle]:
        return [p for p in self if not p.is_center]


    def as_dict(self) -> dict:
        return {self.label: [p.as_rb_dict() for p in self]}


    @property
    def mass(self) -> float:
        return sum([p.m for p in self])


    @property
    def center_of_mass(self) -> np.array:
        wpos = [p.m*p.position for p in self]
        return np.sum(np.asarray(wpos), axis=0) / self.mass


    @property
    def moment_of_inertia(self) -> np.array:
        I = np.zeros(3)
        pc = self.get_center()
        I+= 0.4 * pc.r**2 * pc.m
        for p in self:
            if p.is_center: continue
            I += p.m * (self.center_of_mass - p.position)**2
        return I
