import os
import datetime
from typing import List
from dataclasses import dataclass, field
from .rigidbody import RigidBody
from .particle import Particle
from .interaction import Interaction
from .box import Box
from .yaml_keys import SimType
from .utils import SIMULATIONS_DIR


@dataclass
class SimData:

    file: str
    frame: int = -1


    def as_dict(self) -> dict:
        return {"file": self.file, "frame": self.frame}



@dataclass
class Simulation:

    project: str
    kT: float
    dt: float
    period: int
    duration: int
    seed: int
    box: Box
    path: str = SIMULATIONS_DIR
    rigidbodies: List[dict] = field(default_factory=lambda: [])
    solvents: List[dict] = field(default_factory=lambda: [])
    interactions: List[Interaction] = field(default_factory=lambda: [])
    timestamp: str = None
    start_from: int = 0
    simtype: SimType = None

    continuation_of: SimData = None
    forked_from: SimData = None
    base_trajectory: str = None
    previous_duration: int = 0


    def __post_init__(self):
        self.period = float(self.period)
        self.duration = float(self.duration)


    def __eq__(self, other: RigidBody):
        if self.label != other.label: return False
        return True


    def set_frame(self, frame_index: int) -> None:
        if frame_index == -1:
            frame_index = (self.duration / self.period) - 1
        if frame_index > self.duration / self.period:
            raise Exception("Frame is out of bounds.")
        self.start_from = int(frame_index)


    def set_continuation_of(self, simd: SimData, dur: int) -> None:
        self.continuation_of = simd
        self.set_frame(-1)
        self.project_filename = simd.file
        self.previous_duration = self.duration
        self.duration = dur


    def set_forked_from(self, simd: SimData, dur: int) -> None:
        self.forked_from = simd
        self.set_frame(simd.frame)
        self.base_trajectory = os.path.join(self.path,
                                self.forked_from.file.replace(".yaml", ".gsd"))
        self.duration = dur
        self.forked_from.frame = self.start_from


    def add_rigidbody(self, rb: RigidBody, count: int) -> None:
        self.rigidbodies.append({"rb": rb, "count": count})


    def add_solvent(self, sol: Particle, count: int) -> None:
        self.solvents.append({"sol": sol, "count": count})


    def register_interaction(self, i: Interaction) -> None:
        self.interactions.append(i)


    def list_unique_particles(self) -> List[Particle]:
        unique = []
        for rbdict in self.rigidbodies:
            for p in rbdict["rb"]:
                is_reg = False
                if len(unique) > 0:
                    for up in unique:
                        if p == up:
                            is_reg = True
                            break
                if not is_reg:
                    unique.append(p)

        for sol in self.solvents:
            unique.append(sol["sol"])

        return unique


    @property
    def types_list(self) -> List[str]:
        return [p.label for p in self.list_unique_particles()]


    @property
    def N(self) -> int:
        return self.count_center_particles() + self.count_solvents()


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


    def count_solvents(self) -> int:
        return sum([sol["count"] for sol in self.solvents])


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
        data = {
            "rigidbodies":
                [{rbd["rb"].label: rbd["count"]} for rbd in self.rigidbodies],
            "kT": self.kT,
            "dt": self.dt,
            "seed": self.seed,
            "period": self.period,
            "duration": self.total_duration,
        }
        if self.has_solvent():
            data["solvent"] = \
                    [{sol["sol"].label: sol["count"]} for sol in self.solvents]
        return data



    def get_particle(self, label: str) -> Particle:
        for p in self.list_unique_particles():
            if p.label == label: return p
        raise Exception(f"Particle with label {label} was not found.")


    def list_rigidbodies(self) -> List[RigidBody]:
        rbs = []
        for rbd in self.rigidbodies:
            rbs+= [rbd["rb"]]*rbd["count"]
        return rbs


    def list_solvents(self) -> List[Particle]:
        if not self.has_solvent(): return []
        solvs = []
        for sold in self.solvents:
            solvs+= [sold["sol"]]*sold["count"]
        return solvs


    def mint(self) -> None:
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


    def try_minting(self) -> None:
        if self.simtype is SimType.RUN or self.simtype is SimType.FORK:
            self.mint()


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


    def set_fork_data(self, fd: dict) -> None:
        self.forked_from = fd


    def fork_data(self) -> dict:
        return {"forked_from": self.forked_from}


    def is_run(self) -> bool:
        if self.simtype == SimType.RUN: return True
        return False


    def is_continue(self) -> bool:
        if self.simtype == SimType.CONTINUE: return True
        return False


    def is_fork(self) -> bool:
        if self.simtype == SimType.FORK: return True
        return False


    def has_solvent(self) -> bool:
        if self.count_solvents() == 0: return False
        return True


    def was_forked(self) -> bool:
        if self.forked_from is None: return False
        return True


    @property
    def keep_particles(self) -> List[str]:
        labels = [rb["rb"].get_center().label for rb in self.rigidbodies]
        labels+= [sol["sol"].label for sol in self.solvents]
        return labels


    def check_keep_particle(self, label: str) -> bool:
        if label in self.keep_particles: return True
        return False


    @property
    def overwrite(self) -> bool:
        if self.is_fork(): return True
        if self.is_run(): return True
        if self.is_continue(): return False
        raise Exception("Overwrite not defined.")


    @property
    def total_duration(self) -> int:
        return self.previous_duration + self.duration
