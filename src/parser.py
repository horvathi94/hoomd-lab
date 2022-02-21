import os
import yaml
import numpy as np
from typing import List
from enum import Enum
from dataclasses import dataclass, field
from .particle import Particle
from .rigidbody import RigidBody
from .box import Box
from .interaction import Interaction
from .simulation import Simulation



class Key(Enum):

    PARTICLES = "particles"
    RIGIDBODIES = "rigidbodies"
    BOX = "box"
    INTERACTIONS = "interactions"
    SIMULATION = "simulation"



class ParserProto:


    def read_file(self) -> dict:
        yamlf = os.path.join(self.path, self.fname)
        with open(yamlf, "r") as f:
            data = yaml.safe_load(f)
        return data



class Parser(ParserProto):


    def __init__(self, fname: str, project: str,
                 path: str="/hoomd-examples/workdir/new/"):
        self.fname = fname
        self.project = project
        self.path = path
        self.data = self.read_file()
        self.particles = []
        self.rigidbodies = []
        self.interactions = []


    def read_particles(self) -> list:
        raw = self.data[Key.PARTICLES.value]
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
        raw = self.data[Key.RIGIDBODIES.value]
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


    def read_simulation(self) -> Simulation:
        raw = self.data[Key.SIMULATION.value]
        rbvals = raw.pop("rigidbodies")
        sim = Simulation(**raw, box=self.read_box(), project=self.project)
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


    def read_box(self) -> Box:
        raw = self.data[Key.BOX.value]
        return Box(**raw)


    def read_interactions(self) -> List[Interaction]:
        raw = self.data[Key.INTERACTIONS.value]
        interactions = []
        for item in raw:
            p1_label = list(item.keys())[0]
            idata = list(item.values())[0]
            others = idata.pop("with")
            for o in others:
                i = Interaction(p1_label=p1_label, p2_label=o, **idata)
                interactions.append(i)
        return interactions


    def read(self) -> any:
        self.particles = self.read_particles()
        self.rigidbodies = self.read_rigidbodies()
        self.interactions = self.read_interactions()
        return self.read_simulation()


    @staticmethod
    def write(sim: Simulation, file: str) -> None:
        particles = {Key.PARTICLES.value:
                     [p.as_dict() for p in sim.list_unique_particles()]}
        rigidbodies = {Key.RIGIDBODIES.value:
                       [rb.as_dict() for rb in sim.list_unique_rigidbodies()]}
        box = {Key.BOX.value: sim.box.as_dict()}
        interactions = {Key.INTERACTIONS.value:
                        [i.as_dict() for i in sim.interactions]}
        simulation = {Key.SIMULATION.value: sim.as_dict()}

        with open(file, "w") as f:
            doc = yaml.dump(particles, f)
            doc = yaml.dump(rigidbodies, f, default_flow_style=None)
            doc = yaml.dump(box, f)
            doc = yaml.dump(interactions, f, sort_keys=False)
            doc = yaml.dump(simulation, f)


class ContParser(ParserProto):


    def __init__(self, fname: str, path: str="/hoomd-examples/workdir/new/"):
        self.fname = fname
        self.path = path
        self.data = self.read_file()


    def read_orig_sim(self) -> Simulation:
        from_file = self.data["from"]
        parser = Parser(from_file, path=self.path+"simulations/", project=None)
        sim = parser.read()
        return sim


    def read_simulation(self) -> Simulation:
        sim = self.read_orig_sim()
        raw = self.data[Key.SIMULATION.value]
        if "kT" in raw: sim.kT = raw["kT"]
        if "dt" in raw: sim.dt = raw["dt"]
        if "seed" in raw: sim.seed = raw["seed"]
        sim.extend_duration(int(float(raw["duration"])))
        sim.project_filename = self.data["from"]
        return sim

