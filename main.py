"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from numpy.random import SeedSequence, SFC64, Generator

import graphs
from parameters import Parameters
from simulations import mm1_simulation, map_ph_simulation
from stats import print_stats

SEED_SEQUENCE = SeedSequence()


def main():
    # CLI ARGUMENTS
    description = 'Simulate a proof-of-work blockchain system with a M/M/1 or MAP/PH/1 queue.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('parameters_dir', nargs='?', type=str, default='parameters',
                        help='path to directory containing the parameters (README for details)')
    parser.add_argument('--seed', type=int, help='seed to initialize the random generator')
    parser.add_argument('--mm1', action='store_true', help='run the simulation with M/M/1 queue')
    parser.add_argument('--mapph1', action='store_true', help='run the simulation with MAP/PH/1 queue')
    args = parser.parse_args()

    # Parsing parameters from file system
    p = Parameters.get_from(Path(args.parameters_dir))

    # Initiating pseudo random generator
    global SEED_SEQUENCE
    if args.seed:
        SEED_SEQUENCE = SeedSequence(args.seed)
    print('Seed : ', SEED_SEQUENCE.entropy)
    generators = [Generator(SFC64(stream)) for stream in SEED_SEQUENCE.spawn(10)]

    # Simulations
    if args.mm1:
        print('M/M/1:')
        measured_values = mm1_simulation(generators, **p)

        stats = print_stats(**measured_values)
        graphs.draw(**measured_values, **stats, queue_name='M/M/1')

    if args.mapph1:
        print('MAP/PH/1')
        measured_values = map_ph_simulation(generators, **p)

        stats = print_stats(**measured_values)
        graphs.draw(**measured_values, **stats, queue_name='MAP/PH/1')

    if not (args.mm1 or args.mapph1):
        print("You didn't select any simulation to run.", file=sys.stderr)
        parser.print_help()
    else:
        plt.show()


if __name__ == '__main__':
    main()
