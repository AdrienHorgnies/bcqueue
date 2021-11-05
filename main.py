"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse
import sys

from numpy.random import SeedSequence, SFC64, Generator

from measures import print_stats, print_graphs
from simulations import mm1_simulation, map_ph_simulation, Map

SEED_SEQUENCE = SeedSequence()


def spawn_generators(n):
    """
    Spawn n random generators

    Generators are independent if you spawn less than 2^64 of them and you pull less than 2^64 variates for
    each generators

    :return: a list of n generators
    """
    return [Generator(SFC64(stream)) for stream in SEED_SEQUENCE.spawn(n)]


def main():
    # ARGUMENTS
    description = 'Simulate a proof-of-work blockchain system with a M/M/1 or MAP/PH/1 queue.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('seed', nargs='?', type=int, help='seed to initialize the random generator')
    parser.add_argument('--mm1', action='store_true', help='run the simulation with M/M/1 queue')
    parser.add_argument('--mapph1', action='store_true', help='run the simulation with MAP/PH/1 queue')
    args = parser.parse_args()

    # SETUP
    global SEED_SEQUENCE
    if args.seed:
        SEED_SEQUENCE = SeedSequence(args.seed)
    print('Seed : ', SEED_SEQUENCE.entropy)
    generators = spawn_generators(10)

    if args.mm1:
        arrivals, waitings, blocks = mm1_simulation(generators, tau=1000 * 600,
                                                    _lambda=0.7,
                                                    mu1=10,
                                                    mu2=590)

        print('M/M/1 stats:')
        print_stats(arrivals, waitings, blocks)
        print_graphs(arrivals, waitings, blocks)

    import numpy as np
    if args.mapph1:
        g = generators[0]

        C = np.array([
            [-1.5, +0.5],
            [+0.2, -1.2]
        ])
        D = np.array([
            [+0.5, +0.5],
            [+0.5, +0.5]
        ])
        p = np.array([0.5, 0.5])

        arrival_rate = np.matmul(np.matmul(p, D), np.ones(2))
        print(f"arrival rate : {arrival_rate}")

        _map = Map(g,
                   C=C,
                   D=D,
                   v=p
                   )

        t = 0
        tau = 10 ** 3
        print(f"expected number of arrivals : {tau * arrival_rate:.0f}")

        def next_arrival():
            nonlocal t
            t += g.exponential(- (_map.C[_map.state][_map.state]))

            weights = np.concatenate((_map.C[_map.state], _map.D[_map.state]))
            weights[weights < 0] = 0
            probabilities = weights / weights.sum()

            next_state = g.choice(list(range(len(probabilities))), 1, p=probabilities)[0]

            if next_state < len(_map.C):
                _map.state = next_state
                return next_arrival()
            else:
                _map.state = next_state - len(_map.C)
                return t

        tx_count = 0

        _map.roll_state()

        while t < tau:
            next_arrival()

            tx_count += 1

        print(f"simulated number of arrival : {tx_count}")

        return
        arrivals, waitings, blocks = map_ph_simulation(generators, tau=1000 * 600,
                                                       C=[[-1.5, 0.5],
                                                          [0.2, -1.2]],
                                                       D=[[0.5, 0.5],
                                                          [0.5, 0.5]],
                                                       w=[0.5, 0.5],
                                                       S=[[-10, 0],
                                                          [0, -10]],
                                                       b=[0.5, 0.5],
                                                       T=[[-590, 0],
                                                          [0, -590]],
                                                       a=[0.5, 0.5],
                                                       )
        print('MAP/PH/1 stats:')
        print_stats(arrivals, waitings, blocks)
        print_graphs(arrivals, waitings, blocks)

    if not (args.mm1 or args.mapph1):
        print("You didn't select any simulation to run.", file=sys.stderr)
        parser.print_help()


if __name__ == '__main__':
    main()
