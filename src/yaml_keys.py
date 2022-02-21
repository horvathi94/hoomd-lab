from enum import Enum


class SimType(Enum):

    RUN = "run"
    CONTINUE = "continue"
    FORK = "fork"



class Key(Enum):

    PROJECT_NAME = "project_name"
    PARTICLES = "particles"
    RIGIDBODIES = "rigidbodies"
    BOX = "box"
    INTERACTIONS = "interactions"
    SIMULATION = "simulation"
    ACTION = "action"
    BASE = "base"
