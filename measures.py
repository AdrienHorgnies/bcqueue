import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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
    print(f"Average number of transactions per block : {len(arrivals) / len(blocks):.0f}")
    print(f"Average waiting time : {average_waiting:.0f}")
    print(f"Average service time : {average_service:.0f}")


def print_graphs(arrivals, waitings, blocks):
    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title('Trajectoire')

    scale_x = 600
    ticks_x = ticker.FuncFormatter(lambda x, pos: f"{x/scale_x:g}")
    ax.xaxis.set_major_formatter(ticks_x)

    scale_y = 1000
    ticks_y = ticker.FuncFormatter(lambda y, pos: f"{y/scale_y:g}")
    ax.yaxis.set_major_formatter(ticks_y)

    ax.set(xlabel='time (in 10 minutes units)', ylabel='waiting queue size (in 1000 units)',
           title='Size of the waiting queue through time')
    ax.plot(arrivals, waitings)

    plt.show()
