"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse

from numpy.random import SeedSequence, SFC64, Generator

from simulations import mm_simulation, map_ph_simulation
from measures import print_stats, print_graphs

SEED_SEQUENCE = None


def spawn_generators(n):
    """
    Spawn n random generators

    Generators are insured independent if you spawn less than 2^64 of them and you pull less than 2^64 variates for
    each generators

    :return: a list of n generators
    """
    return [Generator(SFC64(stream)) for stream in SEED_SEQUENCE.spawn(n)]


def main():
    # ARGUMENTS
    description = 'Simulate a proof-of-work blockchain system with a MAP/PH/1 queue.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('seed', nargs='?', type=int, help='seed to initialize the random generator')
    args = parser.parse_args()

    # SETUP
    global SEED_SEQUENCE
    SEED_SEQUENCE = SeedSequence(args.seed) if args.seed else SeedSequence()
    print('Seed : ', SEED_SEQUENCE.entropy)
    generators = spawn_generators(10)

    # SIMULATION
    arrivals, waitings, blocks = mm_simulation(generators)

    # GRAPHS
    print_stats(arrivals, waitings, blocks)
    print_graphs(arrivals, waitings, blocks)


if __name__ == '__main__':
    main()
