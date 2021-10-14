import matplotlib.pyplot as plt
import numpy as np


def print_stats(arrivals, waitings, blocks):
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


def print_graphs(arrivals, waitings, blocks):
    events = [(t, 'arrival') for t in arrivals] + \
             [(b.selection, 'selection', b) for b in blocks] + \
             [(b.mining, 'mining', b) for b in blocks]
    events.sort()
    timings = np.zeros(len(events))
    waiting = np.zeros(len(events))
    mining = np.zeros(len(events))

    # waiting_size = 0
    # mining_size = 0
    # for idx, t in enumerate(events):
    #     timings[idx] = t[0]
    #     if t[1] == 'arrival':
    #         waiting_size += 1
    #     elif t[1] == 'selection':
    #         waiting_size -= t[2].size
    #         mining_size = t[2].size
    #     elif t[1] == 'mining':
    #         mining_size = 0
    #     waiting[idx] = waiting_size
    #     mining[idx] = mining_size

    fig, ax = plt.subplots()
    fig.canvas.set_window_title('Trajectoire')
    fig.set(label='TEST 1')

    ax.set(xlabel='time', ylabel='waiting queue size', title='Size of the waiting queue through time')
    ax.plot(arrivals, waitings)

    plt.show()
