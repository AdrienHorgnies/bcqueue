from models import Block


def mm_simulation(generators):
    # PARLER du fait que j'ai cherché les paramètres qui correspondent à la réalité.

    # TODO integrate MapDoublePH, and make it easy to choose between M/M/1 and MAP/PH/1

    # time of arrival of transactions
    arrivals = []
    # tuples (size, selected, mined)
    blocks = []

    def next_arrival():
        return t + generators[0].exponential(10)

    def next_selection():
        return t + generators[1].exponential(10)

    def next_mining():
        return t + generators[2].exponential(590)

    # max number of transactions per block
    b = 150

    t = 0

    scheduler = {
        'arrival': next_arrival(),
        'selection': next_selection(),
        'mining': float('inf')
    }

    # Duration to get an average of 1000 blocks
    end = 50 * 600

    # list of txs, identified by their time of arrival
    waiting_tx = []
    block_tx = []
    waitings = []

    while t < end:
        next_event_name = min(scheduler, key=scheduler.get)
        t = scheduler[next_event_name]

        if next_event_name == 'arrival':
            waiting_tx.append(t)
            scheduler['arrival'] = next_arrival()
            if t > end * 3 / 4:
                arrivals.append(t)
                waitings.append(len(waiting_tx))
        elif next_event_name == 'selection':
            # We select b transactions except if there is less than b transactions
            effective_b = min(len(waiting_tx), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            # TODO shuffle might not be the most efficient way to randomly select tx
            generators[3].shuffle(waiting_tx)
            block_tx, waiting_tx = waiting_tx[:effective_b], waiting_tx[effective_b:]

            scheduler['selection'] = float('inf')
            scheduler['mining'] = next_mining()

            if t > end * 3 / 4:
                blocks.append(Block(size=effective_b, selection=t, mining=scheduler['mining']))
        elif next_event_name == 'mining':
            # put the txs out, set up next selection
            block_tx = []

            scheduler['selection'] = next_selection()
            scheduler['mining'] = float('inf')

    return arrivals, waitings, blocks


def map_ph_simulation(generators,
                      C, D, w,
                      S, b,
                      T, a
                      ):
    # TODO fix
    # TODO compare MM & MAPPH
    # TODO histogram wait
    # TODO distrib block size
    # TODO BONUS voir comment tenir compte de la prio ?

    # time of arrival of transactions
    arrivals = []
    # tuples (size, selected, mined)
    blocks = []

    queue = MapDoublePh(generators[0], C, D, w, S, b, T, a)

    # max number of transactions per block
    b = 1000

    t = 0

    # Duration to get an average of 1000 blocks
    end = 1000 * 600

    # list of txs, identified by their time of arrival
    waiting_tx = []

    waiting_sizes = []

    while t < end:
        t, event_name = queue.next()

        if event_name == 'arrival':
            waiting_tx.append(t)
            arrivals.append(t)
            waiting_sizes.append(len(waiting_tx))
        elif event_name == 'selection':
            # We select b transactions except if there is less than b transactions
            effective_b = min(len(waiting_tx), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            generators[3].shuffle(waiting_tx)
            block_tx, waiting_tx = waiting_tx[:effective_b], waiting_tx[effective_b:]

            if t > end * 3 / 4:
                blocks.append(Block(size=effective_b, selection=t))
        elif event_name == 'mining':
            if t > end * 3 / 4 and len(blocks) > 0:
                blocks[-1].mining = t
    # CHEATCHODE because I stopped recording before end of last block
    blocks[-1].mining = blocks[-1].selection + 1

    return arrivals, waiting_sizes, blocks


class MapDoublePh:
    """
    A stochastic process composed of a Map and two PhaseType processes.
    The PhaseType processes are mutually exclusive:
      - Only one is active at a time
      - When the active PhaseType process is absorbed, it is swapped with the other one
    """
    def __init__(self, g,
                 C, D, w,
                 S, b,
                 T, a):
        """
        :param g: pseudo random generator
        :param C: C+D = infinitesimal generator of an irreducible Markov process
        :param D: C+D = infinitesimal generator of an irreducible Markov process
        :param w: stationary probability vector of MAP C+D
        :param S: infinitesimal generator of PH process
        :param b: stationary probability vector of PH S
        :param T: infinitesimal generator of PH process
        :param a: stationary probability vector of PH T
        """
        self.g = g

        self.t = 0

        self.map = Map(g, M1=C, M2=D, v=w)
        self.ph = PhaseType(self.g, name='selection', M=S, v=b)
        self.inactive_ph = PhaseType(self.g, name='mining', M=T, v=a)

    def forward(self):
        """
        Advance the time of the simulation by one step
        """
        self.t += self.g.exponential(- (self.map.M1[self.map.state][self.map.state] +
                                        self.ph.M1[self.ph.state][self.ph.state]))

    def next(self):
        """
        Advance the time of the simulation until either MAP or PH is absorbed

        :return: A tuple of the time and the name of the event
        """
        self.forward()

        # Build weight vector by appending correct rows of C, D, M1 and M2
        weights = (self.map.M1[self.map.state] +
                   self.map.M1[self.map.state] +
                   self.ph.M1[self.ph.state] +
                   [self.ph.M2[self.ph.state]])
        # weight of current state is zero, replace negative numbers by zero
        #  I could have excluded these numbers, but it's easier to manipulate the index
        #  when they're still there
        weights[self.map.state] = 0
        weights[-len(self.ph.M1) - 1 + self.ph.state] = 0

        total = sum(weights)
        probabilities = [w / total for w in weights]

        # Choosing next event, represented by his index
        next_event = self.g.choice(range(len(self.map.M1) + len(self.map.M1) + len(self.ph.M1) + 1),
                                   1,
                                   p=probabilities)[0]

        # Find which event was chosen using his index
        if next_event < len(self.map.M1):
            self.map.state = next_event
            return self.next()
        elif next_event < len(self.map.M1) + len(self.map.M1):
            self.map.state = next_event - len(self.map.M1)
            return self.t, 'arrival'
        elif next_event < len(weights) - 1:
            self.ph.state = next_event - len(self.map.M1) - len(self.map.M1)
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
        self.vector = v
        self.state = None
        self.roll_state()

    def roll_state(self):
        """
        Randomly choose a state according to is probability distribution
        """
        self.state = self.g.choice(range(len(self.vector)), 1, p=self.vector)[0]


class Map(StatefulProcess):
    def __init__(self, g, M1, M2, v):
        super().__init__(g, v)
        # TODO make a method to compute v from C and D (find the method in a math lib)
        self.M1 = M1
        self.M1 = M2


class PhaseType(StatefulProcess):
    def __init__(self, g, M, v, name):
        super().__init__(g, v)
        self.M1 = M
        self.name = name
