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
