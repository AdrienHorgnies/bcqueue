from models import Block, Tx, RoomState
from processes import MapDoublePh, MDoubleM


def simulation(scheduler, g, b, sigma, tau, upsilon):
    transactions = []
    blocks = []
    room_states = []

    waiting_room = []
    server_room = []
    block = None

    while scheduler.t < tau + upsilon:
        event_name = scheduler.next()

        if event_name == 'arrival':
            tx = Tx(arrival=scheduler.t)
            waiting_room.append(tx)

            if sigma <= scheduler.t < tau:
                transactions.append(tx)
                room_states.append(RoomState(t=scheduler.t, size=len(waiting_room)))
        elif event_name == 'selection':
            # We select as many tx as possible, but at most b
            effective_b = min(len(waiting_room), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            g.shuffle(waiting_room)
            server_room, waiting_room = waiting_room[:effective_b], waiting_room[effective_b:]

            for tx in server_room:
                tx.selection = scheduler.t

            block = Block(selection=scheduler.t, size=effective_b)

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
    :param p: other unused parameters
    :return: dict containing transactions, blocks, room_sizes and queue parameters
    """
    sch = MDoubleM(generators, _lambda, mu1, mu2)

    return simulation(sch, generators[3], b, sigma, tau, upsilon)


def map_ph_simulation(generators,
                      b, sigma, tau, upsilon,
                      C, D, omega,
                      S, beta,
                      T, alpha,
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
    :param p: other unused parameters
    """
    # TODO BONUS voir comment tenir compte de la prio ?
    scheduler = MapDoublePh(generators, C, D, omega, S, beta, T, alpha)

    return simulation(scheduler, generators[8], b, sigma, tau, upsilon)
