from functools import cache

import numpy as np

from models import Block, Tx, RoomState


def mm1_simulation(generators, b, sigma, tau, upsilon, _lambda, mu1, mu2, **p):
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
    transactions = []
    blocks = []
    room_states = []

    def next_arrival():
        return t + generators[0].exponential(_lambda)

    def next_selection():
        return t + generators[1].exponential(mu1)

    def next_mining():
        return t + generators[2].exponential(mu2)

    t = 0
    scheduler = {
        'arrival': next_arrival(),
        'selection': next_selection(),
        'mining': float('inf')
    }

    waiting_room = []
    server_room = []
    block = None

    while t < tau + upsilon:
        next_event_name = min(scheduler, key=scheduler.get)
        t = scheduler[next_event_name]

        if next_event_name == 'arrival':
            tx = Tx(arrival=t)
            waiting_room.append(tx)
            scheduler['arrival'] = next_arrival()

            if sigma <= t < tau:
                transactions.append(tx)
                room_states.append(RoomState(t=t, size=len(waiting_room)))
        elif next_event_name == 'selection':
            # We select as many tx as possible, but at most b
            effective_b = min(len(waiting_room), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            generators[3].shuffle(waiting_room)
            server_room, waiting_room = waiting_room[:effective_b], waiting_room[effective_b:]

            for tx in server_room:
                tx.selection = t

            scheduler['selection'] = float('inf')
            scheduler['mining'] = next_mining()
            block = Block(selection=t, size=effective_b)

            if sigma <= t < tau:
                blocks.append(block)
                room_states.append(RoomState(t=t, size=len(waiting_room)))
        elif next_event_name == 'mining':
            scheduler['selection'] = next_selection()
            scheduler['mining'] = float('inf')

            block.mining = t
            for tx in server_room:
                tx.mining = t

    return {
        'transactions': transactions,
        'blocks': blocks,
        'room_states': room_states,
    }


def map_ph_simulation(generators,
                      b, tau,
                      C, D, omega,
                      S, beta,
                      T, alpha,
                      **p):
    """
    :param generators: Pseudo random generators
    :param b: Max number of transactions per block
    :param tau: End time of the simulation
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

    # time of arrival of transactions
    measures = []
    blocks = []

    queue = MapDoublePh(generators[5], C, D, omega, S, beta, T, alpha)

    t = 0

    # list of txs, identified by their time of arrival
    waiting_tx = []

    while t < tau:
        t, event_name = queue.next()

        if event_name == 'arrival':
            waiting_tx.append(t)
        elif event_name == 'selection':
            # We select as many tx as possible, but at most b
            effective_b = min(len(waiting_tx), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            generators[6].shuffle(waiting_tx)
            block_tx, waiting_tx = waiting_tx[:effective_b], waiting_tx[effective_b:]

            block = Block(size=effective_b, selection=t)
        elif event_name == 'mining' and t > tau / 2:
            # noinspection PyUnboundLocalVariable
            measures.extend((tx, block.selection, t) for tx in block_tx)
            block.mining = t
            blocks.append(block)

    return *list(zip(*sorted(measures))), blocks


class MapDoublePh:
    """
    A stochastic process composed of a Map and two PhaseType processes.
    The PhaseType processes are mutually exclusive:
      - Only one is active at a time
      - When the active PhaseType process is absorbed, it is swapped with the other one
    """

    def __init__(self, generators,
                 C, D, omega,
                 S, beta,
                 T, alpha):
        """
        :param generators: pseudo random generator
        :param C: C+D = infinitesimal generator of an irreducible Markov process
        :param D: C+D = infinitesimal generator of an irreducible Markov process
        :param omega: stationary probability vector of MAP C+D
        :param S: infinitesimal generator of PH process (selection)
        :param beta: stationary probability vector of PH (selection)
        :param T: infinitesimal generator of PH process (mining)
        :param alpha: stationary probability vector of PH T (mining)
        """
        self.g = generators

        self.t = 0

        self.map = Map(generators, C=C, D=D, v=omega)
        self.ph = PhaseType(self.g, name='selection', M=S, v=beta)
        self.inactive_ph = PhaseType(self.g, name='mining', M=T, v=alpha)

        self.range = list(range(len(C) + len(D) + len(S) + 1))

    def forward(self):
        """
        Advance the time of the simulation by one step
        """
        self.t += self.g.exponential(1 / - (self.map.C[self.map.state][self.map.state] +
                                            self.ph.M[self.ph.state][self.ph.state]))

    def next(self):
        """
        Advance the time of the simulation until either MAP or PH is absorbed

        :return: A tuple of the time and the name of the event
        """
        self.forward()

        # Build weight vector by appending correct rows of C, D, M1 and M2
        probabilities = self.get_next_state_prob_vector(self.map.state, self.ph.state)

        # Choosing next event, represented by his index
        next_event = self.g.choice(self.range, 1, p=probabilities)[0]

        # Find which event was chosen using his index
        if next_event < len(self.map.C):
            self.map.state = next_event
            return self.next()
        elif next_event < len(self.map.C) + len(self.map.D):
            self.map.state = next_event - len(self.map.C)
            return self.t, 'arrival'
        elif next_event < len(probabilities) - 1:
            self.ph.state = next_event - len(self.map.C) - len(self.map.C)
            return self.next()
        else:
            try:
                return self.t, self.ph.name
            finally:
                self.ph.roll_state()
                self.ph, self.inactive_ph = self.inactive_ph, self.ph

    @cache
    def get_next_state_prob_vector(self, map_state, ph_state):
        """
        Compute the probability vector for the given state to simulate the next state

        The way it works is that it creates the concatenation of one row of C, D, M plus the
        absorbing event of M. The row chosen depends on the state of the map and ph.

        This probability vector enables us to randomly choose the next event while respecting the probability of
        each event.
        Each event is identified by its index in this vector.
        Diagonal elements of matrix C and M are kept but set to a probability of zero.

        :param map_state: self.map.state required for cache purpose
        :param ph_state: self.ph.state required for cache purpose
        :return: the probability linked to the current state
        """
        # array beginning as weight, then becoming probabilities.
        # Same array to save execution time
        probabilities = np.ones(len(self.map.C) + len(self.map.D) + len(self.ph.M) + 1)

        offset = 0
        probabilities[offset:len(self.map.C)] = self.map.C[map_state]

        offset += len(self.map.C)
        probabilities[offset:offset + len(self.map.D)] = self.map.D[map_state]

        offset += len(self.map.D)
        probabilities[offset:offset + len(self.ph.M)] = self.ph.M[ph_state]

        offset += len(self.ph.M)
        probabilities[offset] = -sum(self.ph.M[ph_state])

        # render negative number on the diagonals inoffensive for the purpose of this array by setting them to 0
        probabilities[probabilities < 0] = 0

        probabilities /= probabilities.sum()

        return probabilities


class StatefulProcess:
    """
    A mathematical object that has a number of states with each of them having a different stationary probability.
    A state is identified by its index in the probability vector.
    """

    def __init__(self, g, v):
        """
        :param g: A random generator used to simulate random events
        :param v: stationary probability vector of the process
        """
        assert sum(v) == 1, "A probability vector sum must be 1"

        self.g = g
        self.v = v
        self.state = None
        self.roll_state()

    def roll_state(self):
        """
        Randomly choose a state according to its probability distribution
        """
        self.state = self.g.choice(range(len(self.v)), 1, p=self.v)[0]


class Map(StatefulProcess):
    def __init__(self, g, C, D, v):
        super().__init__(g, v)
        # TODO make a method to compute v from C and D (find the method in a math lib)
        self.C = C
        self.D = D

    def __str__(self):
        return "<MAP>"


class PhaseType(StatefulProcess):
    def __init__(self, g, M, v, name):
        super().__init__(g, v)
        self.M = M
        self.name = name

    def __str__(self):
        return f"<PH '{self.name}'>"
