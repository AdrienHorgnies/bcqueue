import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


def print_stats(arrivals, services, completions, blocks, tau):
    arrivals = np.array(arrivals)
    services = np.array(services)
    completions = np.array(completions)

    average_inter_arrival = (arrivals[1:] - arrivals[:-1]).mean()
    average_waiting = (services - arrivals).mean()
    average_service = (completions - services).mean()
    block_time = sum(b.mining - b.selection for b in blocks) / len(blocks)

    print(f"Number of blocks : {len(blocks)}")
    print(f"Average inter-arrival time : {average_inter_arrival}")
    print(f"Average number of tx per block : {len(arrivals) / len(blocks):.0f}")
    print(f"Average waiting time : {average_waiting:.0f}")
    print(f"Average service time : {average_service:.0f}")
    print(f"Average block time : {block_time:.0f}")
    print(f"Average inter-mining time : {tau / 2 / len(blocks)}")


def print_graphs(arrivals, services, completions, blocks):
    arrivals = np.array(arrivals)
    waiting_room = np.zeros(len(arrivals) + len(blocks))

    # we need to replay the arrivals and blocks to evaluate the waiting room size
    zipped_deltas = list(zip(arrivals, np.ones(len(arrivals)))) + [(b.selection, -b.size) for b in blocks]
    zipped_deltas.sort()
    timings, deltas = zip(*zipped_deltas)

    count = 0
    for idx, delta in enumerate(deltas):
        count += delta
        waiting_room[idx] = count

    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title('Trajectoire')

    scale_x = 600
    ticks_x = ticker.FuncFormatter(lambda x, pos: f"{x / scale_x:g}")
    ax.xaxis.set_major_formatter(ticks_x)

    scale_y = 1000
    ticks_y = ticker.FuncFormatter(lambda y, pos: f"{y / scale_y:g}")
    ax.yaxis.set_major_formatter(ticks_y)

    ax.set(xlabel='Temps (par 600)', ylabel='(Taille de la file (par 1000))',
           title="Trajectoire du la taille de la file d'attente.")
    ax.plot(timings, waiting_room)

    plt.show()
