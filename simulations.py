from models import Block


def simulation(generators, name='map_ph'):
    if name == 'map_ph':
        arrivals, blocks = map_ph_simulation(generators)
    else:
        arrivals, blocks = mm_simulation(generators)

    processed_tx = 0
    total_waiting = 0
    total_service = 0

    for block in blocks:
        block_tx = arrivals[processed_tx:processed_tx + block.size]

        total_waiting += block.size * block.selection - sum(block_tx)
        total_service += block.size * (block.mining - block.selection)

        processed_tx += block.size

    average_waiting = total_waiting / len(arrivals)
    average_service = total_service / len(arrivals)

    print(f"Number of blocks : {len(blocks)}")
    print(f"Average number of transactions per block : {len(arrivals) / len(blocks)}")
    print(f"Average waiting time : {average_waiting}")
    print(f"Average service time : {average_service}")
    # TODO trajectoire du nombre de tx dans le système, ça permettra de comparer M/M/1 et MAP/PH/1


def mm_simulation(generators):
    # PARLER du fait que j'ai cherché les paramètres qui correspondent à la réalité.

    # TODO integrate MapDoublePH, and make it easy to choose between M/M/1 and MAP/PH/1

    # time of arrival of transactions
    arrivals = []
    # tuples (size, selected, mined)
    blocks = []

    def next_arrival():
        return t + generators[0].exponential(0.6)

    def next_selection():
        return t + generators[1].exponential(10)

    def next_mining():
        return t + generators[2].exponential(590)

    # max number of transactions per block
    b = 1000

    t = 0

    scheduler = {
        'arrival': next_arrival(),
        'selection': next_selection(),
        'mining': float('inf')
    }

    # Duration to get an average of 1000 blocks
    end = 1000 * 600

    # list of txs, identified by their time of arrival
    waiting_tx = []
    block_tx = []

    while t < end:
        next_event_name = min(scheduler, key=scheduler.get)
        t = scheduler[next_event_name]

        if next_event_name == 'arrival':
            waiting_tx.append(t)
            scheduler['arrival'] = next_arrival()
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
                arrivals.extend(block_tx)
                blocks.append(Block(size=effective_b, selection=t, mining=scheduler['mining']))
        elif next_event_name == 'mining':
            # put the txs out, set up next selection
            block_tx = []

            scheduler['selection'] = next_selection()
            scheduler['mining'] = float('inf')

    return arrivals, blocks


def map_ph_simulation(generators):
    # time of arrival of transactions
    arrivals = []
    # tuples (size, selected, mined)
    blocks = []

    queue = MapDoublePh(generators[0])

    # max number of transactions per block
    b = 1000

    t = 0

    # Duration to get an average of 1000 blocks
    end = 1000 * 600

    # list of txs, identified by their time of arrival
    waiting_tx = []

    while t < end:
        t, event_name = queue.next()

        if event_name == 'arrival':
            waiting_tx.append(t)
        elif event_name == 'selection':
            # We select b transactions except if there is less than b transactions
            effective_b = min(len(waiting_tx), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            generators[3].shuffle(waiting_tx)
            block_tx, waiting_tx = waiting_tx[:effective_b], waiting_tx[effective_b:]

            if t > end * 3 / 4:
                arrivals.extend(block_tx)
                blocks.append(Block(size=effective_b, selection=t))
        elif event_name == 'mining':
            blocks[-1].mining = t

    return arrivals, blocks


class MapDoublePh:
    """
    A stochastic process composed of a Map and two PhaseType processes.
    The PhaseType processes are mutually exclusive:
      - Only one is active at a time
      - When the active PhaseType process is absorbed, it is swapped with the other one
    """

    def __init__(self, g):
        self.g = g

        self.t = 0

        self.map = Map(g)
        self.ph = PhaseType(self.g, 'selection')
        self.inactive_ph = PhaseType(self.g, 'mining')

    def forward(self):
        """
        Bring forward the time of the simulation by one step
        """
        self.t += self.g.exponential(- (self.map.C[self.map.state][self.map.state] +
                                        self.ph.T[self.ph.state][self.ph.state]))

    def next(self):
        """
        Run the process and return when either MAP or PH was absorbed
        :return: A tuple of the time and the name of the event
        """
        self.forward()

        # Build weight vector by appending correct rows of C, D, T and t
        weights = (self.map.C[self.map.state] +
                   self.map.D[self.map.state] +
                   self.ph.T[self.ph.state] +
                   [self.ph.t[self.ph.state]])
        # replace negative numbers with zero, they're non events
        weights[self.map.state] = 0
        weights[-len(self.ph.T) - 1 + self.ph.state] = 0

        # Choosing next event, represented by his index, using their respective probability as a weight
        next_event = self.g.choice(range(len(self.map.C) + len(self.map.D) + len(self.ph.T) + 1),
                                   1,
                                   p=weights)[0]

        # Find which event was chosen using his index
        if next_event < len(self.map.C):
            self.map.state = next_event
            return self.next()
        elif next_event < len(self.map.C) + len(self.map.D):
            self.map.state = next_event - len(self.map.C)
            return self.t, 'arrival'
        elif next_event < len(weights) - 1:
            self.ph.state = next_event - len(self.map.C) - len(self.map.D)
            return self.next()
        else:
            try:
                return self.t, self.ph.name
            finally:
                self.ph.roll_state()
                self.ph, self.inactive_ph = self.inactive_ph, self.ph


class StatefulProcess:
    """
    A mathematical object that has a number of states with each of them having a different probably to occur.
    A state is identified by its index in the probably vector.
    """

    def __init__(self, g, vector):
        """

        :param g: A random generator used to simulate random events
        :param vector: The probably of each state
        """
        assert sum(vector) == 1, "A probably vector sum must be 1"

        self.g = g
        self.vector = vector
        self.state = None
        self.roll_state()

    def roll_state(self):
        self.state = self.g.choice(range(len(self.vector)), 1, p=self.vector)[0]

# TODO ATM, generator matrices are hardcoded, they will become parameters to be provided in the future


class Map(StatefulProcess):
    def __init__(self, g):
        super().__init__(g, [0.3, 0.7])
        # TODO make a method to compute PI from C and D (must already exist)
        self.C = [[-1, 0.2],
                  [0.9, -3]]
        self.D = [[0.5, 0.3],
                  [2, 0.1]]


class PhaseType(StatefulProcess):
    def __init__(self, g, name):
        super().__init__(g, [0.1, 0.4, 0.5])
        self.T = [[-0.2, 0, 0],
                  [0.1, -0.4, 0],
                  [1, 0, -2]]
        self.t = [0.2,
                  0.3,
                  1]
        self.name = name
