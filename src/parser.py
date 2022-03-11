import os
import yaml
import numpy as np
from typing import List
from dataclasses import dataclass, field
from .particle import Particle
from .rigidbody import RigidBody
from .box import Box
from .interaction import Interaction
from .simulation import Simulation, SimData
from . import yaml_keys as ykeys

from .lists import ParticleList, RigidBodyList, InteractionList


SIMULATIONS_PATH = "/hoomd-examples/workdir/new/simulations/"



@dataclass
class Parser:

    filename: str
    simtype: ykeys.SimType = None
    project_name: str = None
    abs_path: str = "/hoomd-examples/workdir/new/"
    data: dict = None
    box: Box = None
    particles: ParticleList = ParticleList()
    rigidbodies: RigidBodyList = RigidBodyList()
    interactions: InteractionList = InteractionList()
    simulation: Simulation = None


    def __post_init__(self):
        self._read_file()
        self._read_simtype()
        self._parse_file()
        if "forked_from" in self.data:
            self.forked_from = self.data["forked_from"]


    def _parse_file(self):
        if self.simtype is ykeys.SimType.RUN:
            self._read_run()
        elif self.simtype is ykeys.SimType.CONTINUE:
            self._read_continue()
        elif self.simtype is ykeys.SimType.FORK:
            self._read_fork()
        self.simulation.simtype = self.simtype


    def _read_file(self) -> dict:
        with open(self.abs_file, "r") as f:
            self.data = yaml.safe_load(f)


    @property
    def abs_file(self) -> str:
        return os.path.join(self.abs_path, self.filename)


    def _read_simtype(self) -> None:
        self.simtype = ykeys.SimType.RUN
        if ykeys.Key.ACTION.value in self.data:
            action = self.data[ykeys.Key.ACTION.value]
            self.simtype = ykeys.SimType(action)


    def _read_box(self) -> None:
        if ykeys.Key.BOX.value not in self.data:
            raise Exception("Missing box data.")
        raw = self.data[ykeys.Key.BOX.value]
        self.box = Box(**raw)


    def _read_particles(self) -> None:
        if ykeys.Key.PARTICLES.value not in self.data:
            raise Exception("Missing particles data.")
        raw = self.data[ykeys.Key.PARTICLES.value]
        for item in raw:
            label, attrs = list(item.items())[0]
            p = Particle(label, **attrs)
            self.particles.add(p)


    def _read_rigidbodies(self) -> None:
        if ykeys.Key.RIGIDBODIES.value not in self.data:
            raise Exception("Missing rigid bodies data.")
        raw = self.data[ykeys.Key.RIGIDBODIES.value]
        for item in raw:
            label, ps = list(item.items())[0]
            rb = RigidBody(label)
            for pdata in ps:
                label, attrs = list(pdata.items())[0]
                p = self.particles.get(label)
                pos = np.asarray(attrs["position"])
                is_center = False
                if "is_center" in attrs: is_center = attrs["is_center"]
                rb.add_particle(p, pos, is_center=is_center)
            self.rigidbodies.add(rb)


    def _read_interactions(self) -> None:
        if ykeys.Key.INTERACTIONS.value not in self.data:
            raise Exception("Missing interaction data.")
        raw = self.data[ykeys.Key.INTERACTIONS.value]
        for item in raw:
            p1_label, attrs = list(item.items())[0]
            with_ = attrs.pop("with")
            for other in with_:
                i = Interaction(p1_label=p1_label, p2_label=other, **attrs)
                self.interactions.add(i)



    def _read_simulation(self) -> None:
        if ykeys.Key.SIMULATION.value not in self.data:
            raise Exception("Missing simulation data.")
        raw = self.data[ykeys.Key.SIMULATION.value]
        rb_data = raw.pop("rigidbodies")
        solvent_data = []
        if "solvent" in raw:
            solvent_data = raw.pop("solvent")
        sim = Simulation(**raw, box=self.box, project=self.project_name)
        for item in rb_data:
            label, count = list(item.items())[0]
            rb = self.rigidbodies.get(label)
            sim.add_rigidbody(rb, int(float(count)))
        for i in self.interactions._items:
            sim.register_interaction(i)
        for item in solvent_data:
            label, count = list(item.items())[0]
            sol = self.particles.get(label)
            sim.add_solvent(sol, int(float(count)))

        if ykeys.Key.FORKED_FROM in raw:
            fd = raw[ykeys.Key.FORKED_FROM]
            print(fd)

        self.simulation = sim


    def _read_project_name(self) -> None:
        self.project_name = None
        if ykeys.Key.PROJECT_NAME.value in self.data:
            self.project_name = self.data[ykeys.Key.PROJECT_NAME.value]


    def _read_forked_from(self) -> None:
        if ykeys.Key.FORKED_FROM.value in self.data:
            forked_from = self.data[ykeys.Key.FORKED_FROM.value]
            self.simulation.forked_from = SimData(**forked_from)


    def _read_run(self) -> None:
        self._read_project_name()
        if self.project_name is None:
            raise Exception("Project name not found.")
        self._read_box()
        self._read_particles()
        self._read_rigidbodies()
        self._read_interactions()
        self._read_simulation()
        self._read_forked_from()


    def _read_base_info(self) -> SimData:
        if ykeys.Key.BASE.value not in self.data:
            raise Exception("Missing base data.")
        raw = self.data[ykeys.Key.BASE.value]
        if "file" not in raw:
            raise Exception("Missing base file name.")
        return SimData(**raw)


    def _read_continue(self) -> None:
        if ykeys.Key.SIMULATION.value not in self.data:
            raise Exception("Missing simulation info.")
        raw = self.data[ykeys.Key.SIMULATION.value]
        if "duration" not in raw:
            raise Exception("Duration is missing.")

        base = self._read_base_info()
        basep = Parser(base.file, abs_path=SIMULATIONS_PATH)
        self.project_name = basep.project_name
        self.simulation = basep.simulation
        self.simulation.set_continuation_of(base, int(float(raw["duration"])))


    def _read_fork(self) -> None:
        if ykeys.Key.SIMULATION.value not in self.data:
            raise Exception("Missing simulation info.")
        raw = self.data[ykeys.Key.SIMULATION.value]
        if "duration" not in raw:
            raise Exception("Duration is missing.")

        self._read_project_name()
        if self.project_name is None:
            raise Exception("Missing project name")

        base = self._read_base_info()
        basep = Parser(base.file, abs_path=SIMULATIONS_PATH)
        self.simulation = basep.simulation
        self.simulation.project = self.project_name
        self.simulation.set_forked_from(base, int(float(raw["duration"])))
        if "kT" in raw: self.simulation.kT = raw["kT"]
        if "dt" in raw: self.simulation.dt = raw["dt"]


    @staticmethod
    def write(sim: Simulation, file: str) -> None:
        particles = {ykeys.Key.PARTICLES.value:
                     [p.as_dict() for p in sim.list_unique_particles()]}
        rigidbodies = {ykeys.Key.RIGIDBODIES.value:
                       [rb.as_dict() for rb in sim.list_unique_rigidbodies()]}
        box = {ykeys.Key.BOX.value: sim.box.as_dict()}
        interactions = {ykeys.Key.INTERACTIONS.value:
                        [i.as_dict() for i in sim.interactions]}
        simulation = {ykeys.Key.SIMULATION.value: sim.as_dict()}
        project_name = {ykeys.Key.PROJECT_NAME.value: sim.project}

        with open(file, "w") as f:
            doc = yaml.dump(project_name, f)
            doc = yaml.dump(particles, f)
            doc = yaml.dump(rigidbodies, f, default_flow_style=None)
            doc = yaml.dump(box, f)
            doc = yaml.dump(interactions, f, sort_keys=False,
                            default_flow_style=None)
            doc = yaml.dump(simulation, f, sort_keys=False)
            if sim.forked_from is not None:
                forked_from = {ykeys.Key.FORKED_FROM.value:
                               sim.forked_from.as_dict()}
                doc = yaml.dump(forked_from, f)
