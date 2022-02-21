import os
import datetime
from typing import List
from dataclasses import dataclass, field
from .rigidbody import RigidBody
from .particle import Particle
from .interaction import Interaction
from .box import Box
from .yaml_keys import SimType


@dataclass
class Simulation:

    project: str
    kT: float
    dt: float
    period: int
    duration: int
    seed: int
    box: Box
    path: str = "/hoomd-examples/workdir/new/simulations/"
    rigidbodies: List[dict] = field(default_factory=lambda: [])
    interactions: List[Interaction] = field(default_factory=lambda: [])
    timestamp: str = None
    start_from: int = 0
    simtype: SimType = None
    base: dict = None


    def __post_init__(self):
        self.period = float(self.period)
        self.duration = float(self.duration)


    def __eq__(self, other: RigidBody):
        if self.label != other.label: return False
        return True


    def set_frame(self, frame_index: int) -> None:
        if frame_index == -1:
            self.start_from = (self.duration / self.period) - 1
        if frame_index > self.duration / self.period:
            raise Exception("Frame is out of bounds.")
        self.start_from = frame_index


    def extend_duration(self, dur: int) -> None:
        self.start_from = self.duration
        self.duration += dur


    def add_rigidbody(self, rb: RigidBody, count: int) -> None:
        self.rigidbodies.append({"rb": rb, "count": count})


    def register_interaction(self, i: Interaction) -> None:
        self.interactions.append(i)


    def list_unique_particles(self) -> List[Particle]:
        unique = []
        for rbdict in self.rigidbodies:
            rb = rbdict["rb"]

            for p in rb:

                is_reg = False

                if len(unique) > 0:
                    for up in unique:
                        if p == up:
                            is_reg = True
                            break

                if not is_reg:
                    unique.append(p)

        return unique


    def list_unique_rigidbodies(self) -> List[RigidBody]:
        unique = []
        for rbdict in self.rigidbodies:
            rb = rbdict["rb"]
            is_reg = False

            if len(unique) > 0:
                for urb in unique:
                    if rb == urb:
                        is_reg = True
                        break

            if not is_reg:
                unique.append(rb)
        return unique


    def count_center_particles(self) -> int:
        return sum([rbd["count"] for rbd in self.rigidbodies])


    def list_center_particles(self) -> List[Particle]:
        cps = []
        for rbd in self.rigidbodies:
            cps+= [rbd["rb"].get_center()]*rbd["count"]
        return cps


    def unique_center_particles(self) -> List[Particle]:
        cps = []
        for rbd in self.rigidbodies:
            cps+= [rbd["rb"].get_center()]
        return cps


    def as_dict(self) -> dict:
        return {
            "rigidbodies":
                [{rbd["rb"].label: rbd["count"]} for rbd in self.rigidbodies],
            "kT": self.kT,
            "dt": self.dt,
            "seed": self.seed,
            "period": self.period,
            "duration": self.duration,
        }



    def get_particle(self, label: str) -> Particle:
        for p in self.list_unique_particles():
            if p.label == label: return p
        raise Exception(f"Particle with label {label} was not found.")


    def list_rigidbodies(self) -> List[RigidBody]:
        rbs = []
        for rbd in self.rigidbodies:
            rbs+= [rbd["rb"]]*rbd["count"]
        return rbs


    def mint(self) -> None:
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


    @property
    def project_filename(self) -> str:
        if self.timestamp is None:
            raise Exception("Project not minted")
        return f"{self.project}_{self.timestamp}.yaml"


    @project_filename.setter
    def project_filename(self, fname: str) -> None:
        project, date, time = fname.split(".")[0].split("_")
        self.project = project
        self.timestamp = f"{date}_{time}"


    @property
    def project_file(self) -> str:
        return os.path.join(self.path, self.project_filename)


    @property
    def log_filename(self) -> str:
        if self.timestamp is None:
            raise Exception("Project not minted")
        return f"{self.project}_{self.timestamp}.log"


    @property
    def log_file(self) -> str:
        return os.path.join(self.path, self.log_filename)


    @property
    def trajectory_filename(self) -> str:
        if self.timestamp is None:
            raise Exception("Project not minted")
        return f"{self.project}_{self.timestamp}.gsd"


    @property
    def trajectory_file(self) -> str:
        return os.path.join(self.path, self.trajectory_filename)


    def fork_data(self) -> dict:
        if self.simtype is not SimType.FORK: return None
        return {"forked_from": {"file": self.base["file"],
                                "frame": self.base["frame"]}}
