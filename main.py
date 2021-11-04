"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse

from numpy.random import SeedSequence, SFC64, Generator

from measures import print_stats, print_graphs
from simulations import mm_simulation, map_ph_simulation

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
    description = 'Simulate a proof-of-work blockchain system with a MAP/PH/1 queue.'
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
        arrivals, waitings, blocks = mm_simulation(generators)

        print('M/M/1 stats:')
        print_stats(arrivals, waitings, blocks)
        print_graphs(arrivals, waitings, blocks)
    if args.mapph1:
        arrivals, waitings, blocks = map_ph_simulation(generators,
                                                       C=[[-1.5, 0.5],
                                                          [0.2, -1.2]],
                                                       D=[[-1.5, 0.5],
                                                          [0.2, -1.2]],
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


if __name__ == '__main__':
    main()
