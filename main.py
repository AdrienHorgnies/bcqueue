"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse
import sys

from numpy.random import SeedSequence, SFC64, Generator

from measures import print_stats, print_graphs
from simulations import mm1_simulation, map_ph_simulation, Map

SEED_SEQUENCE = SeedSequence()


def main():
    # ARGUMENTS
    description = 'Simulate a proof-of-work blockchain system with a M/M/1 or MAP/PH/1 queue.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('parameters_dir', type=str,
                        help='path to directory containing the parameters (README for details)')
    parser.add_argument('--seed', type=int, help='seed to initialize the random generator')
    parser.add_argument('--mm1', action='store_true', help='run the simulation with M/M/1 queue')
    parser.add_argument('--mapph1', action='store_true', help='run the simulation with MAP/PH/1 queue')
    args = parser.parse_args()

    # SETUP
    global SEED_SEQUENCE
    if args.seed:
        SEED_SEQUENCE = SeedSequence(args.seed)
    print('Seed : ', SEED_SEQUENCE.entropy)
    generators = [Generator(SFC64(stream)) for stream in SEED_SEQUENCE.spawn(10)]

    if args.mm1:
        arrivals, waitings, blocks = mm1_simulation(generators, tau=1000 * 600,
                                                    _lambda=0.7,
                                                    mu1=10,
                                                    mu2=590)

        print('M/M/1 stats:')
        print_stats(arrivals, waitings, blocks)
        print_graphs(arrivals, waitings, blocks)

    if args.mapph1:
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
