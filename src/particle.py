import numpy as np
from dataclasses import dataclass


@dataclass
class Particle:

    label: str
    q: int = 0
    m: int = 1
    diam: int = 1
    x: float = 0
    y: float = 0
    z: float = 0
    is_center: bool = False


    def copy(self) -> "Particle":
        new = Particle(self.label)
        new.q = self.q
        new.m = self.m
        new.diam = self.diam
        return new


    def __eq__(self, other: "Particle") -> bool:
        if self.label != other.label: return False
        return True


    @property
    def r(self) -> float:
        return self.diam / 2.


    @r.setter
    def r(self, r: float) -> None:
        self.diam = 2*r


    def as_dict(self) -> dict:
        return {self.label:
            {"q": self.q,
            "m": self.m,
            "diam": self.diam}
        }


    def as_rb_dict(self) -> dict:
        return {self.label:
            {"position": self.position.tolist(),
             "is_center": self.is_center}
        }


    @property
    def position(self) -> np.array:
        return np.array([self.x, self.y, self.z])


    @position.setter
    def position(self, pos: np.array) -> None:
        if len(pos) != 3: raise ValueError
        self.x, self.y, self.z = pos
