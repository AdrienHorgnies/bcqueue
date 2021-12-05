import scipy.stats as stats
from sortedcontainers import SortedList

from models import Block, Tx, RoomState
from processes import MapDoublePh, MDoubleM


def simulation(scheduler, g, b, sigma, tau, upsilon, fees, fee_min, fee_loc, fee_max, fee_scale):
    fee_dist = stats.truncnorm((fee_min - fee_loc) / fee_scale,
                               (fee_max - fee_loc) / fee_scale,
                               loc=fee_loc, scale=fee_scale)

    transactions = []
    blocks = []
    room_states = []

    waiting_room = SortedList() if fees else []
    server_room = []
    block = None

    while scheduler.t < tau + upsilon:
        event_name = scheduler.next()

        if event_name == 'arrival':
            if fees:
                tx = Tx(fee=fee_dist.rvs(1), arrival=scheduler.t)
                waiting_room.add(tx)
            else:
                tx = Tx(fee=0, arrival=scheduler.t)
                waiting_room.append(tx)

            if sigma <= scheduler.t < tau:
                transactions.append(tx)
                room_states.append(RoomState(t=scheduler.t, size=len(waiting_room)))
        elif event_name == 'selection':
            if fees:
                waiting_room, server_room = SortedList(waiting_room[:-b]), waiting_room[-b:]
            else:
                if b < len(waiting_room):
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
    Simulate the blockchain system with a M/M/1 queue

    :param generators: Pseudo random generators
    :param b: Max number of transactions per block
    :param sigma: Start time of the recording of measures
    :param tau: End time of the recording of new measures
    :param upsilon: Extra time after tau to complete existing measures
    :param _lambda: Expected inter-arrival time
    :param mu1: Expected selection duration
    :param mu2: Expected mining duration
    :param fees: whether to use fees to prioritize transactions or not
    :param fee_scale: Standard deviation of the truncated normal distribution to determine the fee of a transaction
    :param fee_min: Lower limit of the fee distribution
    :param fee_loc: Mean/Centre of the fee distribution
    :param fee_max: Upper limit of the fee distribution
    :param p: other unused parameters
    :return: dict containing transactions, blocks, room_sizes and queue parameters
    """
    sch = MDoubleM(generators, _lambda, mu1, mu2)

    return simulation(sch, generators[3], b, sigma, tau, upsilon, fees, fee_min, fee_loc, fee_max, fee_scale)


def map_ph_simulation(generators,
                      b, sigma, tau, upsilon,
                      C, D, omega,
                      S, beta,
                      T, alpha,
                      fees, fee_min, fee_loc, fee_max, fee_scale,
                      **p):
    """
    :param generators: Pseudo random generators
    :param b: Max number of transactions per block
    :param sigma: Start time of the recording of measures
    :param tau: End time of the simulation
    :param upsilon: Extra time after tau to complete existing measures
    :param C: Generating matrix for MAP (non absorbing)
    :param D: Generating matrix for MAP (absorbing)
    :param omega: Stationary probability vector for MAP
    :param S: Generating matrix for PH (selection)
    :param beta: Absorbing transitions probability vector for PH (selection)
    :param T: Generating matrix for PH (mining)
    :param alpha: Absorbing transitions probability vector for PH (mining)
    :param fees: whether to use fees to prioritize transactions or not
    :param fee_scale: Standard deviation of the truncated normal distribution to determine the fee of a transaction
    :param fee_min: Lower limit of the fee distribution
    :param fee_loc: Mean/Centre of the fee distribution
    :param fee_max: Upper limit of the fee distribution
    :param p: other unused parameters
    """
    scheduler = MapDoublePh(generators, C, D, omega, S, beta, T, alpha)

    return simulation(scheduler, generators[8], b, sigma, tau, upsilon, fees, fee_min, fee_loc, fee_max, fee_scale)
