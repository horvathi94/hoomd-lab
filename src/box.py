from dataclasses import dataclass


@dataclass
class Box:

    Lx: int
    Ly: int
    Lz: int


    def as_dict(self) -> dict:
        return {"Lx": self.Lx, "Ly": self.Ly, "Lz": self.Lz}
