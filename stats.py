"""
Module to compute statistical measure to print to the console
"""
import numpy as np


def compute_print_stats(transactions, blocks, room_states):
    """
    Print statistical measures from received data, and return a dictionary with:
    - arrivals
    - services (time of start)
    - completions
    - inter_arrival_times
    - sojourn_durations
    - waiting_durations
    - service_durations
    - inter_block_times
    - block_sizes
    - room_times
    - room_sizes

    Under each key is a list of float ready to be used for graphs

    :param transactions: list of recorded transactions
    :param blocks:  list of recorded blocks
    :param room_states: list of recorded waiting room states

    :return: a dictionary with all sorts of measures
    """
    stats = {
        'arrivals': np.empty(len(transactions)),
        'services': np.empty(len(transactions)),
        'completions': np.empty(len(transactions))
    }

    if any(tx.fee for tx in transactions):
        stats['fees'] = np.empty(len(transactions))

    for idx, tx in enumerate(transactions):
        stats['arrivals'][idx] = tx.arrival
        stats['services'][idx] = tx.selection
        stats['completions'][idx] = tx.mining
        if 'fees' in stats:
            stats['fees'][idx] = tx.fee

    stats['inter_arrival_times'] = np.ediff1d(stats['arrivals'])
    stats['sojourn_durations'] = stats['completions'] - stats['arrivals']
    stats['waiting_durations'] = stats['services'] - stats['arrivals']
    stats['service_durations'] = stats['completions'] - stats['services']

    # ignore last block if not mined, very unlikely if sufficient extra time is provided
    if blocks[-1].mining is None:
        blocks = blocks[:-1]
    stats['inter_block_times'] = np.ediff1d([b.mining for b in blocks])
    stats['block_sizes'] = np.array([b.size for b in blocks], dtype=int)

    stats['room_times'] = np.array([s.t for s in room_states])
    stats['room_sizes'] = np.array([s.size for s in room_states], dtype=int)

    no_selection = np.isnan(stats['services']).sum()
    no_mining = np.isnan(stats['completions']).sum()

    print(f"""
    All transactions : {len(transactions)} (100%)
    Non selected transactions : {no_selection} ({no_selection / len(stats['services']):.3%})
    Non mined transactions : {no_mining} ({no_mining / len(stats['completions']):.3%})
    
    Average sojourn duration : {np.nanmean(stats['sojourn_durations']):.0f}
    Average waiting duration : {np.nanmean(stats['waiting_durations']):.0f}
    Average service duration : {np.nanmean(stats['service_durations']):.0f}

    Average block time : {stats['inter_block_times'].mean():.0f}
    Average block size: {stats['block_sizes'].mean():.0f}
    
    Average waiting room size: {stats['room_sizes'].mean():.0f}

    Average inter-arrival times : {stats['inter_arrival_times'].mean():.3f}    
    """)

    return stats
