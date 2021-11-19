import numpy as np

from models import Block


def mm1_simulation(generators, b, tau, _lambda, mu1, mu2):
    """
    :param generators: Pseudo random generators
    :param b: Max number of transactions per block
    :param tau: End time of the simulation
    :param _lambda: Average inter-arrival time
    :param mu1: Average service time (selection)
    :param mu2: Average service time (mining)
    :return: (arrivals, services, completions, blocks)
    """
    # each measure is a trio (arrival_time, service_beginning_time, completion_time)
    measures = []
    blocks = []

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

    # list of txs, identified by their time of arrival
    waiting_tx = []
    block_tx = []

    while t < tau:
        next_event_name = min(scheduler, key=scheduler.get)
        t = scheduler[next_event_name]

        if next_event_name == 'arrival':
            waiting_tx.append(t)
            scheduler['arrival'] = next_arrival()
        elif next_event_name == 'selection':
            # We select as many tx as possible, but at most b
            effective_b = min(len(waiting_tx), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            # TODO use efficient random sampling algorithm from Knuth.
            generators[3].shuffle(waiting_tx)
            block_tx, waiting_tx = waiting_tx[:effective_b], waiting_tx[effective_b:]

            scheduler['selection'] = float('inf')
            scheduler['mining'] = next_mining()
            block = Block(size=effective_b, selection=t)
        elif next_event_name == 'mining':
            if t > tau / 2:
                # noinspection PyUnboundLocalVariable
                measures.extend((tx, block.selection, t) for tx in block_tx)
                block.mining = t
                blocks.append(block)

            scheduler['selection'] = next_selection()
            scheduler['mining'] = float('inf')

    return *list(zip(*sorted(measures))), blocks


def map_ph_simulation(generators,
                      b, tau,
                      C, D, omega,
                      S, beta,
                      T, alpha
                      ):
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
        # TODO reuse array to avoid reallocation, it's always the same size !
        #  or cache it using map.state, ph.name, ph.state as a key ? Can't do that if matrices are too big
        weights = np.array(self.map.C[self.map.state] +
                           self.map.D[self.map.state] +
                           self.ph.M[self.ph.state] +
                           [self.ph.v[self.ph.state]])
        # exclude current state by setting its weight to zero
        weights[weights < 0] = 0

        probabilities = weights / weights.sum()

        # Choosing next event, represented by his index
        next_event = self.g.choice(self.range, 1, p=probabilities)[0]

        # Find which event was chosen using his index
        if next_event < len(self.map.C):
            self.map.state = next_event
            return self.next()
        elif next_event < len(self.map.C) + len(self.map.D):
            self.map.state = next_event - len(self.map.C)
            return self.t, 'arrival'
        elif next_event < len(weights) - 1:
            self.ph.state = next_event - len(self.map.C) - len(self.map.C)
            return self.next()
        else:
            try:
                return self.t, self.ph.name
            finally:
                self.ph.roll_state()
                self.ph, self.inactive_ph = self.inactive_ph, self.ph


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
