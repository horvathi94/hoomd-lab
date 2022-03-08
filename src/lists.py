from typing import List
from .particle import Particle
from .rigidbody import RigidBody
from .interaction import Interaction


class StructList:


    STRUCT_TYPE = any


    def __init__(self):
        self._items = []


    def __repr__(self):
        return "["+ ", ".join(self.labels) +"]"


    @property
    def labels(self) -> List[str]:
        return [item.label for item in self._items]


    def add(self, item: any) -> None:
        if not isinstance(item, self.STRUCT_TYPE):
            raise Exception("Unable to add, invalid type.")
        self._items.append(item)


    def get(self, label: str) -> any:
        for item in self._items:
            if item.label == label: return item
        raise Exception(f"Item with label {label} was not found.")



class ParticleList(StructList):

    STRUCT_TYPE = Particle



class RigidBodyList(StructList):

    STRUCT_TYPE = RigidBody



class InteractionList(StructList):

    STRUCT_TYPE = Interaction
