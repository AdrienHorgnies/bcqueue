"""
Module that models the proof-of-work blockchain systems
"""
import time

import scipy.stats as stats

from models import Block, Tx, RoomState
from processes import MapDoublePh, MDoubleM


def simulation(scheduler, g, b, sigma, tau, upsilon, fees, fee_min, fee_loc, fee_max, fee_scale):
    """
    Simulate the blockchain system from t=0 to t=tau+sigma

    :param scheduler: Control the flow of time (self.t) and events (self.next)
    :param g: pseudo random generator used to randomly select transactions or choose fees
    :param b: max number of transactions in a block
    :param sigma: time to start recording transaction arrivals and block selections
    :param tau: time to stop recording transactions arrivals and block selections
    :param upsilon: extra time to continue record transaction and block mining
    :param fees: if fees must be used to prioritize transactions, random otherwise
    :param fee_min: lower bound of fees
    :param fee_loc: mean of the truncated normal distribution of fees
    :param fee_max: upper bound of fees
    :param fee_scale: standard deviation of the fees distribution
    :return: the measures recorded during the simulation, a mapping with keys transactions, blocks and room_states;
     respectively a list of Tx, a list of Block and a list of RoomState.
    """
    print("Simulation started.")
    start = time.perf_counter()

    fee_dist = stats.truncnorm((fee_min - fee_loc) / fee_scale,
                               (fee_max - fee_loc) / fee_scale,
                               loc=fee_loc, scale=fee_scale)
    # set pseudo random generator of fee_dist
    fee_dist.random_state = g

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
                tx = Tx(fee=fee_dist.rvs(1), arrival=scheduler.t)
            else:
                tx = Tx(fee=0, arrival=scheduler.t)

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
        elif event_name == 'mining':
            block.mining = scheduler.t
            for tx in server_room:
                tx.mining = scheduler.t

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
                   fees, fee_min, fee_loc, fee_max, fee_scale,
                   **p):
    """
    Simulate the blockchain system with a M/M/1 queue.

    See method simulation for undocumented parameters.

    :param generators: Pseudo random generators (use indices 0 to 4)
    :param _lambda: Expected inter-arrival time
    :param mu1: Expected selection duration
    :param mu2: Expected mining duration
    :param p: other unused parameters
    :return: see simulation
    """
    scheduler = MDoubleM(generators, _lambda, mu1, mu2)

    return simulation(scheduler, generators[3], b, sigma, tau, upsilon, fees, fee_min, fee_loc, fee_max, fee_scale)


def map_ph_simulation(generators,
                      b, sigma, tau, upsilon,
                      C, D, omega,
                      S, beta,
                      T, alpha,
                      fees, fee_min, fee_loc, fee_max, fee_scale,
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
    :param T: Generating matrix for PH (mining)
    :param alpha: Absorbing transitions probability vector for PH (mining)
    :param p: other unused parameters
    """
    scheduler = MapDoublePh(generators, C, D, omega, S, beta, T, alpha)

    return simulation(scheduler, generators[8], b, sigma, tau, upsilon, fees, fee_min, fee_loc, fee_max, fee_scale)
