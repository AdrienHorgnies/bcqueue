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
    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title('Trajectoire')

    arrivals_10min = arrivals / (10 * 600)
    ax.set(xlabel='time (in 10 minutes units)', ylabel='waiting queue size',
           title='Size of the waiting queue through time')
    ax.plot(arrivals_10min, waitings)

    plt.show()
