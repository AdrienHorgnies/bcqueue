"""
Defines data classes to aggregate data measures on blocks, transactions and the waiting room
"""
from dataclasses import dataclass


@dataclass
class Block:
    selection: float  # when it selected transactions
    size: int  # number of selected transactions
    mining: float = None  # when it was mined


@dataclass(order=True)
class Tx:
    ratio: float  # ratio of fee / weight
    arrival: float  # when it arrives into the queue
    selection: float = None  # when it was selected in a block
    mining: float = None  # when the containing block was mined


@dataclass
class RoomState:
    t: float  # when the measure was observed (right after tx arrival or block selection)
    size: int  # number of transactions in the waiting room
