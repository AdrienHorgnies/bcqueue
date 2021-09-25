def simulation(generators):
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
            chosen_number = min(len(waiting_tx), b)
            # We select b transactions by shuffling the whole list and select the b first transactions
            generators[3].shuffle(waiting_tx)
            block_tx, waiting_tx = waiting_tx[:chosen_number], waiting_tx[chosen_number:]

            scheduler['selection'] = float('inf')
            scheduler['mining'] = next_mining()

            if t > end * 3 / 4:
                arrivals.extend(block_tx)
                blocks.append((chosen_number, t, scheduler['mining']))
        elif next_event_name == 'mining':
            # put the txs out, set up next selection
            block_tx = []

            scheduler['selection'] = next_selection()
            scheduler['mining'] = float('inf')

    processed_tx = 0
    total_waiting = 0
    total_service = 0

    for block in blocks:
        size, selected, mined = block
        block_tx = arrivals[processed_tx:processed_tx + size]

        total_waiting += size * selected - sum(block_tx)
        total_service += size * (mined - selected)

        processed_tx += size

    average_waiting = total_waiting / len(arrivals)
    average_service = total_service / len(arrivals)

    print(f"Number of blocks : {len(blocks)}")
    print(f"Average number of transactions per block : {len(arrivals) / len(blocks)}")
    print(f"Average waiting time : {average_waiting}")
    print(f"Average service time : {average_service}")
    # TODO trajectoire du nombre de tx dans le système, ça permettra de comparer M/M/1 et MAP/PH/1


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
        self.active_ph = PhaseType(self.g)
        self.inactive_ph = PhaseType(self.g)

    def forward(self):
        """
        Bring forward the time of the simulation by one step
        """
        self.t += self.g.exponential(- (self.map.C[self.map.state][self.map.state] +
                                        self.active_ph.T[self.active_ph.state][self.active_ph.state]))

    def next(self):
        """
        Run the process and return when either MAP or PH was absorbed
        :return: The name of the process that was absorbed
        """
        self.forward()

        # Build weight vector by appending correct rows of C, D, T and t
        weights = (self.map.C[self.map.state] +
                   self.map.D[self.map.state] +
                   self.active_ph.T[self.active_ph.state] +
                   [self.active_ph.t[self.active_ph.state]])
        # replace negative numbers with zero, they're non events
        weights[self.map.state] = 0
        weights[-len(self.active_ph.T) - 1 + self.active_ph.state] = 0

        # Find index of next event, using their respective probability as a weight
        next_event = self.g.choice(range(len(self.map.C) + len(self.map.D) + len(self.active_ph.T) + 1),
                                   1,
                                   p=weights)[0]

        # Find which event was chosen using his index
        if next_event < len(self.map.C):
            self.map.state = next_event
            return self.next()
        elif next_event < len(self.map.C) + len(self.map.D):
            self.map.state = next_event - len(self.map.C)
            return 'MAP'
        elif next_event < len(weights) - 1:
            self.active_ph.state = next_event - len(self.map.C) - len(self.map.D)
            return self.next()
        else:
            self.active_ph, self.inactive_ph = self.inactive_ph, self.active_ph
            self.active_ph.roll_state()
            return 'PH'


class Stationary:
    """
    A mathematical object that has a number of states which each of them has a different probably to occur.
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


class Map(Stationary):
    def __init__(self, g):
        super().__init__(g, [0.3, 0.7])
        # TODO make a method to compute PI from C and D (must already exist)
        self.C = [[-1, 0.2],
                  [0.9, -3]]
        self.D = [[0.5, 0.3],
                  [2, 0.1]]


class PhaseType(Stationary):
    def __init__(self, g):
        super().__init__(g, [0.1, 0.4, 0.5])
        self.T = [[-0.2, 0, 0],
                  [0.1, -0.4, 0],
                  [1, 0, -2]]
        self.t = [0.2,
                  0.3,
                  1]
