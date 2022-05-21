"""
Module that models the proof-of-work blockchain systems
"""
import time

from models import Block, Tx, RoomState
from processes import MapDoublePh, MDoubleM


def simulation(scheduler, g, b, sigma, tau, upsilon, fees, ratios):
    """
    Simulate the blockchain system from t=0 to t=tau+sigma

    :param scheduler: Control the flow of time (self.t) and events (self.next)
    :param g: pseudo random generator used to randomly select transactions or choose fees
    :param b: max number of transactions in a block
    :param sigma: time to start recording transaction arrivals and block selections
    :param tau: time to stop recording transactions arrivals and block selections
    :param upsilon: extra time to continue record transaction and block broadcast
    :param fees: if fees must be used to prioritize transactions, random otherwise
    :param ratios: a list of fee on weight ratios to randomly choose from
    :return: the measures recorded during the simulation, a mapping with keys transactions, blocks and room_states;
     respectively a list of Tx, a list of Block and a list of RoomState.
    """
    print("Simulation started.")
    start = time.perf_counter()

    transactions = []
    blocks = []
    room_states = []

    waiting_room = []
    server_room = []
    block = None

    while scheduler.t < tau + upsilon:
        event_name = scheduler.next()

        if event_name == 'arrival':
            if fees:
                tx = Tx(ratio=g.choice(ratios), arrival=scheduler.t)
            else:
                tx = Tx(ratio=0, arrival=scheduler.t)

            waiting_room.append(tx)

            if sigma <= scheduler.t < tau:
                transactions.append(tx)
                room_states.append(RoomState(t=scheduler.t, size=len(waiting_room)))
        elif event_name == 'selection':
            if b >= len(waiting_room):
                waiting_room, server_room = [], waiting_room
            elif fees:
                waiting_room.sort()
                server_room = [waiting_room.pop() for _ in range(b)]
            else:
                g.shuffle(waiting_room)
                waiting_room, server_room = waiting_room[b:], waiting_room[:b]

            for tx in server_room:
                tx.selection = scheduler.t

            block = Block(selection=scheduler.t, size=len(server_room))

            if sigma <= scheduler.t < tau:
                blocks.append(block)
                room_states.append(RoomState(t=scheduler.t, size=len(waiting_room)))
        elif event_name == 'broadcast':
            block.broadcast = scheduler.t
            for tx in server_room:
                tx.broadcast = scheduler.t

    print(f"Simulation finished in {time.perf_counter() - start:.0f} seconds.")
    return {
        'transactions': transactions,
        'blocks': blocks,
        'room_states': room_states,
    }


def mm1_simulation(generators,
                   b, sigma, tau, upsilon,
                   _lambda,
                   mu1,
                   mu2,
                   fees, ratios,
                   **p):
    """
    Simulate the blockchain system with a M/M/1 queue.

    See method simulation for undocumented parameters.

    :param generators: Pseudo random generators (use indices 0 to 4)
    :param _lambda: Expected inter-arrival time
    :param mu1: Expected selection duration
    :param mu2: Expected broadcast duration
    :param p: other unused parameters
    :return: see simulation
    """
    scheduler = MDoubleM(generators, _lambda, mu1, mu2)

    return simulation(scheduler, generators[3], b, sigma, tau, upsilon, fees, ratios)


def map_ph_simulation(generators,
                      b, sigma, tau, upsilon,
                      C, D, omega,
                      S, beta,
                      T, alpha,
                      fees, ratios,
                      **p):
    """
    Simulate the blockchain system with a MAP/PH/1 queue.

    See method simulation for undocumented parameters.

    :param generators: Pseudo random generators (use indices 5 to 9)
    :param C: Generating matrix for MAP (non absorbing)
    :param D: Generating matrix for MAP (absorbing)
    :param omega: Stationary probability vector for MAP
    :param S: Generating matrix for PH (selection)
    :param beta: Absorbing transitions probability vector for PH (selection)
    :param T: Generating matrix for PH (broadcast)
    :param alpha: Absorbing transitions probability vector for PH (broadcast)
    :param p: other unused parameters
    :return: see simulation
    """
    scheduler = MapDoublePh(generators, C, D, omega, S, beta, T, alpha)

    return simulation(scheduler, generators[8], b, sigma, tau, upsilon, fees, ratios)
