import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from sortedcontainers import SortedList


def print_stats(arrivals, services, completions, blocks):
    arrivals = np.array(arrivals)

    average_waiting = (sum(services) - sum(arrivals)) / len(arrivals)
    average_service = (sum(completions) - sum(services)) / len(arrivals)
    block_time = sum(b.mining - b.selection for b in blocks) / len(blocks)

    print(f"Number of blocks : {len(blocks)}")
    print(f"Average number of transactions per block : {len(arrivals) / len(blocks):.0f}")
    print(f"Average waiting time : {average_waiting:.0f}")
    print(f"Average service time : {average_service:.0f}")
    print(f"Average block time : {block_time:.0f}")


def print_graphs(arrivals, services, completions, blocks):
    arrivals = np.array(arrivals)
    waiting_room = np.zeros(len(arrivals) + len(blocks))

    # we need to replay the arrivals and blocks to evaluate the waiting room size
    deltas = list(zip(arrivals, np.ones(len(arrivals)))) + [(b.selection, -b.size) for b in blocks]
    deltas.sort()

    count = 0
    for idx, (_, delta) in enumerate(deltas):
        count += delta
        waiting_room[idx] = count
    waiting_room_timings = [t for t, d in deltas]

    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title('Trajectoire')

    scale_x = 600
    ticks_x = ticker.FuncFormatter(lambda x, pos: f"{x / scale_x:g}")
    ax.xaxis.set_major_formatter(ticks_x)

    scale_y = 1000
    ticks_y = ticker.FuncFormatter(lambda y, pos: f"{y / scale_y:g}")
    ax.yaxis.set_major_formatter(ticks_y)

    ax.set(xlabel='time (in 10 minutes units)', ylabel='waiting queue size (in 1000 units)',
           title='Size of the waiting queue through time')
    ax.plot(waiting_room_timings, waiting_room)

    plt.show()
