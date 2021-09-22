def simulation(generators):
    m = MapPh(generators[5])
    m.next()

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

            last_selection = scheduler['selection']
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


class MapPh:
    def __init__(self, g):
        self.g = g

        self.map_state = 0
        self.C = [[-1, 0.2],
                  [0.9, -3]]
        self.D = [[0.5, 0.3],
                  [2, 0.1]]

        self.ph_state = 1
        self.alpha = [0.1,
                      0.4,
                      0.5]
        self.T = [[-0.2, 0, 0],
                  [0.1, -0.4, 0],
                  [1, 0, -2]]
        self.t = [0.2,
                  0.3,
                  1]

    def next(self):
        pr_and_events = [(map_transition_pr, ('MAP_TRANSITION', self.map_state, idx))
                         for idx, map_transition_pr
                         in enumerate(self.C[self.map_state])
                         if map_transition_pr > 0]
        pr_and_events += [(map_arrival_pr, ('MAP_ARRIVAL', 0))  # 0 is dummy to avoid unpack by unzip
                          for map_arrival_pr
                          in self.D[self.map_state]
                          ]
        pr_and_events += [(ph_transition_pr, ('PH_TRANSITION', self.ph_state, idx))
                          for idx, ph_transition_pr
                          in enumerate(self.T[self.ph_state])
                          if ph_transition_pr > 0]

        pr_and_events.append((self.t[self.ph_state], ('PH_DONE', 0)))  # 0 is dummy to avoid unpack by unzip

        pr, events = zip(*pr_and_events)

        next_event = self.g.choice(events, 1, pr)[0]

        if next_event[0] == 'MAP_TRANSITION':
            self.map_state = next_event[2]
            return self.next()
        elif next_event[0] == 'MAP_ARRIVAL':
            # TODO WHAT NUMBER TO I DRAFT ?
            # TODO Are all MAP_ARRIVAL same event ? I think self.C[0,1] means we draft a number
            #  and transition to state 1
            return self.g.exponential(0.6)
        elif next_event[0] == 'PH_TRANSITION':
            self.ph_state = next_event[2]
            return self.next()
        elif next_event[0] == 'PH_DONE':
            # TODO WHAT NUMBER TO I DRAFT ?
            # TODO Do I always go to state 0 ?
            self.ph_state = 0
            return self.g.exponential(600)
        else:
            raise ValueError('Unknown event')
