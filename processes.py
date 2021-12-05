"""
Module that defines the stochastic processes used in the simulation.
Stochastic processes can only provide time and name of associated events (arrival, selection and mining).
It doesn't define the business logic of the blockchain system.
"""
from functools import cache

import numpy as np


class MapDoublePh:
    """
    A stochastic process composed of a Map and two PhaseType service processes.
    The service processes, selection and mining, are mutually exclusive:
      - Only one is active at a time
      - When the active PhaseType process is absorbed, it is swapped with the other one
      - Server starts with selection
    It is initiated at time 0 (self.t) and time elapses with the method `next`.
    """

    def __init__(self, generators,
                 C, D, omega,
                 S, beta,
                 T, alpha):
        """
        :param generators: array of pseudo random generators (uses indices 5 to 9)
        :param C: C+D = infinitesimal generator of an irreducible Markov process
        :param D: C+D = infinitesimal generator of an irreducible Markov process (arrival)
        :param omega: stationary probability vector of MAP C+D
        :param S: infinitesimal generator of PH process (selection)
        :param beta: stationary probability vector of PH (selection)
        :param T: infinitesimal generator of PH process (mining)
        :param alpha: stationary probability vector of PH (mining)
        """
        self.g = generators[9]

        self.t = 0

        self.map = Map(generators[5], C=C, D=D, stationary_probabilities=omega)
        self.ph = PhaseType(generators[6], name='selection', M=S, stationary_probabilities=beta)
        self.inactive_ph = PhaseType(generators[7], name='mining', M=T, stationary_probabilities=alpha)

        # events of MAP/PH/1 are represented by their index in this vector
        self.events = list(range(len(C) + len(D) + len(S) + 1))
        # ph can have different sizes, so we need two of them
        self.inactive_events = list(range(len(C) + len(D) + len(T) + 1))

    def next(self):
        """
        Advance the time of the simulation until MAP has an arrival or PH is absorbed,
         and returns the name of the associated event.

        :return: name of the realized process
        """
        self.t += self.g.exponential(1 / - (self.map.C[self.map.state][self.map.state] +
                                            self.ph.M[self.ph.state][self.ph.state]))

        probabilities = self.get_next_state_prob_vector(self.ph, self.map.state, self.ph.state)

        # Choosing next event, represented by his index
        next_event = self.g.choice(self.events, 1, p=probabilities)[0]

        # Find which event was chosen using his index
        if next_event < len(self.map.C):
            self.map.state = next_event
            return self.next()
        elif next_event < len(self.map.C) + len(self.map.D):
            self.map.state = next_event - len(self.map.C)
            return 'arrival'
        elif next_event < len(probabilities) - 1:
            self.ph.state = next_event - len(self.map.C) - len(self.map.C)
            return self.next()
        else:
            try:
                return self.ph.name
            finally:
                # finally is executed after the return is evaluated, but before code calling the method
                self.ph.absorption()
                self.ph, self.inactive_ph = self.inactive_ph, self.ph
                self.events, self.inactive_events = self.inactive_events, self.events

    @cache
    def get_next_state_prob_vector(self, ph, map_state, ph_state):
        """
        Compute the probability vector for the given state to simulate the next state

        The way it works is that it creates the concatenation of one row of C, D, M plus the
        absorbing event of M. The rows chosen depend on the state of the map and ph.

        This probability vector enables us to randomly choose the next event while respecting the probability of
        each event.
        Each event is identified by its index in this vector (C, then D, then M, then absorbing event of ph).
        Diagonal elements of matrix C and M are kept, but set to a probability of zero.

        :param ph: self.ph required for cache purpose
        :param map_state: self.map.state required for cache purpose
        :param ph_state: self.ph.state required for cache purpose
        :return: the probability vector of the current state to simulate the next state
        """
        # array beginning as weight, then becoming probabilities.
        # Same array to save execution time
        probabilities = np.ones(len(self.map.C) + len(self.map.D) + len(ph.M) + 1)

        offset = 0
        probabilities[offset:len(self.map.C)] = self.map.C[map_state]

        offset += len(self.map.C)
        probabilities[offset:offset + len(self.map.D)] = self.map.D[map_state]

        offset += len(self.map.D)
        probabilities[offset:offset + len(ph.M)] = ph.M[ph_state]

        offset += len(ph.M)
        probabilities[offset] = ph.absorbing_probabilities[ph_state]

        # render negative number on the diagonals inoffensive for the purpose of this array by setting them to 0
        probabilities[probabilities < 0] = 0

        # weights become probabilities
        probabilities /= probabilities.sum()

        return probabilities


class StatefulProcess:
    """
    A mathematical object that has a number of states with each of them having a different probability to occur.
    A state is identified by its index in the stationary_probabilities vector.
    """

    def __init__(self, g, stationary_probabilities):
        """
        It stores the arguments, computes the possible states, and initializes it with a random state.

        :param g: pseudo random generator to randomly choose a state
        :param stationary_probabilities: stationary probability vector of the process
        """
        assert sum(stationary_probabilities) == 1, "A probability vector sum must be 1"

        self.g = g
        self.state_probabilities = stationary_probabilities
        self.possible_states = list(range(len(self.state_probabilities)))
        self.state = g.choice(self.possible_states, 1, p=self.state_probabilities)[0]


class Map(StatefulProcess):
    """
    Markovian Arrival Process
    """

    def __init__(self, g, C, D, stationary_probabilities):
        """

        :param g: pseudo random generator to randomly choose a state
        :param C: C+D = infinitesimal generator of an irreducible Markov process
        :param D: C+D = infinitesimal generator of an irreducible Markov process (arrival)
        :param stationary_probabilities: stationary probability vector of the process
        """
        super().__init__(g, stationary_probabilities)
        self.C = C
        self.D = D

    def __str__(self):
        return "<MAP>"


class PhaseType(StatefulProcess):
    """
    Phase Type process
    """

    def __init__(self, g, M, stationary_probabilities, name):
        """

        :param g: pseudo random generator to randomly choose a state
        :param M: infinitesimal generator of PH process
        :param stationary_probabilities: stationary probability vector of the process
        :param name: name of the phenomenon simulated by this process
        """
        super().__init__(g, stationary_probabilities)
        self.M = M
        self.name = name
        self.absorbing_probabilities = [-sum(row) for row in M]

    def __str__(self):
        return f"<PH '{self.name}'>"

    def absorption(self):
        """
        Randomly set a state, to use after an absorption
        """
        self.state = self.g.choice(self.possible_states, 1, p=self.state_probabilities)[0]


class MDoubleM:
    """
    A stochastic process composed of a Poisson arrival process and two exponential service processes.
    The service processes (selection and mining) are mutually exclusive:
      - Only one is active at a time
      - When the active service process is absorbed, it is swapped with the other one
      - Server starts with selection
    It is initiated at time 0 (self.t) and time elapses with the method `next`.
    """

    def __init__(self, generators, _lambda, mu1, mu2):
        """

        :param generators: array of pseudo random generators (uses indices 0 to 4)
        :param _lambda: Expected inter-arrival time
        :param mu1: expected service time (selection)
        :param mu2: expected service time (mining)
        """
        self.generators = generators

        self._lambda = _lambda
        self.mu1 = mu1
        self.mu2 = mu2

        self.t = 0
        # contains the timing of the next event for each type of event, infinity if None is planned
        self.planning = {
            'arrival': self.next_arrival(),
            'selection': self.next_selection(),
            'mining': float('inf')
        }

    def next_arrival(self):
        """
        :return: timing of the next arrival, estimated at current time
        """
        return self.t + self.generators[0].exponential(self._lambda)

    def next_selection(self):
        """
        :return: timing of the next selection, estimated at current time
        """
        return self.t + self.generators[1].exponential(self.mu1)

    def next_mining(self):
        """
        :return: timing of the next mining, estimated at current time
        """
        return self.t + self.generators[2].exponential(self.mu2)

    def next(self):
        """
        Elapse time to the next event and returns its name

        :return: the name of the event occurring now
        """
        event_name = min(self.planning, key=self.planning.get)
        self.t = self.planning[event_name]

        if event_name == 'arrival':
            self.planning['arrival'] = self.next_arrival()
        elif event_name == 'selection':
            self.planning['selection'] = float('inf')
            self.planning['mining'] = self.next_mining()
        else:
            self.planning['mining'] = float('inf')
            self.planning['selection'] = self.next_selection()

        return event_name
