import os
import yaml
import numpy as np
from typing import List
from dataclasses import dataclass, field
from .particle import Particle
from .rigidbody import RigidBody
from .box import Box
from .interaction import Interaction
from .simulation import Simulation
from . import yaml_keys as ykeys



@dataclass
class Parser:

    filename: str
    simtype: ykeys.SimType = None
    project_name: str = None
    abs_path: str = "/hoomd-examples/workdir/new/"
    box: Box = None
    particles: List[Particle] = field(default_factory=lambda: [])
    rigidbodies: List[RigidBody] = field(default_factory=lambda: [])
    interactions: List[Interaction] = field(default_factory=lambda: [])
    simulation: Simulation = None


    def __post_init__(self):
        self.data = self.read_file()
        self.simtype = self.get_simulation_type()
        if self.simtype is ykeys.SimType.RUN:
            self._read_run()
        elif self.simtype is ykeys.SimType.CONTINUE:
            self._read_continue()
        elif self.simtype is ykeys.SimType.FORK:
            self._read_fork()


    def read_file(self) -> dict:
        yamlf = os.path.join(self.abs_path, self.filename)
        with open(yamlf, "r") as f:
            data = yaml.safe_load(f)
        return data


    def get_simulation_type(self) -> ykeys.SimType:
        if ykeys.Key.ACTION.value in self.data:
            action = self.data[ykeys.Key.ACTION.value]
            return ykeys.SimType(action)
        return ykeys.SimType.RUN


    def read_box(self) -> Box:
        if ykeys.Key.BOX.value not in self.data:
            raise Exception("Missing box data.")
        raw = self.data[ykeys.Key.BOX.value]
        return Box(**raw)


    def read_particles(self) -> list:
        if ykeys.Key.PARTICLES.value not in self.data:
            raise Exception("Missing particles data.")
        raw = self.data[ykeys.Key.PARTICLES.value]
        particles = []
        for item in raw:
           label = list(item.keys())[0]
           props = list(item.values())[0]
           p = Particle(label, **props)
           particles.append(p)
        return particles


    def fetch_particle(self, label: str) -> Particle:
        for p in self.particles:
            if p.label == label: return p
        raise Exception(f"Particle with label {label} was no found.")


    def read_rigidbodies(self) -> list:
        if ykeys.Key.RIGIDBODIES.value not in self.data:
            raise Exception("Missing rigid bodies data.")
        raw = self.data[ykeys.Key.RIGIDBODIES.value]
        rigidbodies = []
        for item in raw:
            label = list(item.keys())[0]
            rb = RigidBody(label)
            for rawp in list(item.values())[0]:
                p = self.fetch_particle(list(rawp.keys())[0])
                props = list(rawp.values())[0]
                pos = np.asarray(props["position"])
                is_center = False
                if "is_center" in props:
                    is_center = props["is_center"]
                rb.add_particle(p, pos, is_center=is_center)
            rigidbodies.append(rb)
        return rigidbodies


    def fetch_rigidbody(self, label: str) -> RigidBody:
        for rb in self.rigidbodies:
            if rb.label == label: return rb
        raise Exception(f"Rigid body with label {label} was not found.")


    def read_interactions(self) -> List[Interaction]:
        if ykeys.Key.INTERACTIONS.value not in self.data:
            raise Exception("Missing interaction data.")
        raw = self.data[ykeys.Key.INTERACTIONS.value]
        interactions = []
        for item in raw:
            p1_label = list(item.keys())[0]
            idata = list(item.values())[0]
            others = idata.pop("with")
            for o in others:
                i = Interaction(p1_label=p1_label, p2_label=o, **idata)
                interactions.append(i)
        return interactions


    def read_simulation(self) -> Simulation:
        if ykeys.Key.SIMULATION.value not in self.data:
            raise Exception("Missing simulation data.")
        raw = self.data[ykeys.Key.SIMULATION.value]
        rbvals = raw.pop("rigidbodies")
        sim = Simulation(**raw, box=self.read_box(), project=self.project_name)
        for rbval in rbvals:
            label = list(rbval.keys())[0]
            count = list(rbval.values())[0]
            rb = self.fetch_rigidbody(label)
            if count == 1 and "fixed_position" in rbval:
                rb.fixed_position = rbval["fixed_position"]
            sim.add_rigidbody(rb, count)
        for i in self.interactions:
            sim.register_interaction(i)
        return sim


    def read_project_name(self) -> str:
        if ykeys.Key.PROJECT_NAME.value in self.data:
            return self.data[ykeys.Key.PROJECT_NAME.value]
        return None


    def _read_run(self) -> None:
        self.project_name = self.read_project_name()
        if self.project_name is None:
            raise Exception("Missing project name.")
        self.box = self.read_box()
        self.particles = self.read_particles()
        self.rigidbodies = self.read_rigidbodies()
        self.interactions = self.read_interactions()
        self.simulation = self.read_simulation()


    def read_base_info(self) -> dict:
        if ykeys.Key.BASE.value not in self.data:
            raise Exception("Missing base data.")
        raw = self.data[ykeys.Key.BASE.value]
        if "file" not in raw:
            raise Exception("Missing base file name.")
        frame_index = -1 if "frame" not in raw else int(raw["frame"])
        return {"file": raw["file"], "frame_index": frame_index}


    @classmethod
    def _read_base(self, fname: str) -> any:
        return Parser(fname,
                      abs_path="/hoomd-examples/workdir/new/simulations/")


    def _read_continue(self) -> None:
        base_info = self.read_base_info()
        base = self._read_base(base_info["file"])
        self.project_name = self.read_project_name()
        if self.project_name is None: self.project_name = base.project_name
        self.box = base.box
        self.particles = base.particles
        self.rigidbodies = base.rigidbodies
        self.interactions = base.interactions
        self.simulation = base.simulation
        self.simulation.set_frame(base_info["frame_index"])
        if ykeys.Key.SIMULATION.value not in self.data:
            raise Exception("Missing simulation info.")
        raw = self.data[ykeys.Key.SIMULATION.value]
        if "duration" not in raw:
            raise Exception("Duration is missing.")
        else:
            self.simulation.extend_duration(int(float(raw["duration"])))
        self.simulation.project_filename = base_info["file"]



    def _read_fork(self) -> None:
        base_info = self.read_base_info()
        base = self._read_base(base_info["file"])
        self.project_name = self.read_project_name()
        if self.project_name is None:
            self.project_name = base.project_name + "_fork"
        self.box = base.box
        self.particles = base.particles
        self.rigidbodies = base.rigidbodies
        self.interactions = base.interactions
        self.simulation = base.simulation
        self.simulation.set_frame(base_info["frame_index"])
        if ykeys.Key.SIMULATION.value not in self.data:
            raise Exception("Missing simulation info.")
        raw = self.data[ykeys.Key.SIMULATION.value]
        if "duration" not in raw:
            raise Exception("Duration is missing.")
        else:
            self.simulation.duration = int(float(raw["duration"]))
        if "kT" in raw: self.simulation.kT = raw["kT"]
        if "dt" in raw: self.simulation.dt = raw["dt"]
        self.simulation.action = ykeys.SimType.FORK
        self.simulation.base = base_info


    @staticmethod
    def write(sim: Simulation, file: str) -> None:
        particles = {ykeys.Keys.PARTICLES.value:
                     [p.as_dict() for p in sim.list_unique_particles()]}
        rigidbodies = {ykeys.Keys.RIGIDBODIES.value:
                       [rb.as_dict() for rb in sim.list_unique_rigidbodies()]}
        box = {ykeys.Keys.BOX.value: sim.box.as_dict()}
        interactions = {ykeys.Keys.INTERACTIONS.value:
                        [i.as_dict() for i in sim.interactions]}
        simulation = {ykeys.Keys.SIMULATION.value: sim.as_dict()}
        project_name = {ykeys.Keys.PROJECT_NAME: sim.project}

        with open(file, "w") as f:
            doc = yaml.dump(project_name, f)
            doc = yaml.dump(particles, f)
            doc = yaml.dump(rigidbodies, f, default_flow_style=None)
            doc = yaml.dump(box, f)
            doc = yaml.dump(interactions, f, sort_keys=False)
            doc = yaml.dump(simulation, f)
            if simulation.simtype is ykeys.SimType.FORK:
                doc = yaml.dump(simulation.fork_data(), f)
