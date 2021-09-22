def simulation(generators):
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
