"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse
import time
from pathlib import Path

import matplotlib.pyplot as plt
from numpy.random import SeedSequence, SFC64, Generator

import graphs
from parameters import Parameters
from simulations import mm1_simulation, map_ph_simulation
from stats import compute_print_stats

SEED_SEQUENCE = SeedSequence()


def main():
    # Defining CLI Arguments
    description = 'Simulate a proof-of-work blockchain system with a M/M/1 or MAP/PH/1 queue, with fees or not.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('parameters_dir', nargs='?', type=str, default='parameters',
                        help='path to directory containing the parameters (README for details)')
    parser.add_argument('--seed', type=int, help='seed to initialize the pseudo random generator')
    parser.add_argument('--mm1', action='store_true', help='run the simulation with M/M/1 queue')
    parser.add_argument('--mapph1', action='store_true', help='run the simulation with MAP/PH/1 queue')
    parser.add_argument('--fees', action='store_true',
                        help='Prioritize transactions according to offered fees (otherwise, random order)')
    args = parser.parse_args()

    # Parsing parameters from file system
    p = Parameters.get_from(Path(args.parameters_dir))

    # Initiating pseudo random generator
    global SEED_SEQUENCE
    if args.seed:
        SEED_SEQUENCE = SeedSequence(args.seed)
    print('Seed :', SEED_SEQUENCE.entropy)
    generators = [Generator(SFC64(stream)) for stream in SEED_SEQUENCE.spawn(10)]

    # Simulations
    if args.mm1:
        if args.fees:
            print('M/M/1 with fees :')
        else:
            print('M/M/1 :')
        start = time.perf_counter()

        measures = mm1_simulation(generators, fees=args.fees, **p)
        stats = compute_print_stats(**measures)
        graphs.draw(**measures, **stats, queue_name='M/M/1')

        print(f"Done after {time.perf_counter() - start:.0f}s")

    if args.mapph1:
        if args.fees:
            print('MAP/PH/1 with fees :')
        else:
            print('MAP/PH/1 :')
        start = time.perf_counter()

        measures = map_ph_simulation(generators, fees=args.fees, **p)
        stats = compute_print_stats(**measures)
        graphs.draw(**measures, **stats, queue_name='MAP/PH/1')

        print(f"Done after {time.perf_counter() - start:.0f}s")

    if not (args.mm1 or args.mapph1):
        parser.print_help()
        exit("You didn't select any simulation to run.")
    else:
        plt.show()


if __name__ == '__main__':
    main()
