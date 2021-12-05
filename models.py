from dataclasses import dataclass


@dataclass
class Block:
    selection: float
    size: int
    mining: float = None


@dataclass(order=True)
class Tx:
    fee: float
    arrival: float
    selection: float = None
    mining: float = None


@dataclass
class RoomState:
    t: float
    size: int
