"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from numpy.random import SeedSequence, SFC64, Generator

import graphs
from stats import print_stats
from simulations import mm1_simulation, map_ph_simulation

SEED_SEQUENCE = SeedSequence()


def matrix_from(path):
    matrix = []
    with open(path) as file:
        reader = csv.reader(file)

        first_line = next(reader)
        matrix.append([float(el) for el in first_line])

        matrix_size = len(matrix[0])

        line_num = 1
        for line in reader:
            line_num += 1
            assert len(line) == matrix_size, f"Matrix {path} is not square! Line {line_num} size is not {matrix_size}."
            matrix.append([float(el.replace(' ', '')) for el in line])
        assert line_num == matrix_size, f"Matrix {path} is not square ({matrix_size}x{line_num})! " \
                                        f"Rows and columns sizes don't match."

    return matrix


def vector_from(path):
    with open(path) as file:
        reader = csv.reader(file)
        vector = next(reader)
        return [float(el.replace(' ', '')) for el in vector]


def float_from(path):
    with open(path) as file:
        reader = csv.reader(file)
        line = next(reader)
        return float(line[0].replace(' ', ''))


def int_from(path):
    return int(float_from(path))


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
    C, D, S, T, _lambda, alpha, b, beta, mu1, mu2, omega, tau = parameters_from(Path(args.parameters_dir))

    # Initiating pseudo random generator
    global SEED_SEQUENCE
    if args.seed:
        SEED_SEQUENCE = SeedSequence(args.seed)
    print('Seed : ', SEED_SEQUENCE.entropy)
    generators = [Generator(SFC64(stream)) for stream in SEED_SEQUENCE.spawn(10)]

    # Simulations
    if args.mm1:
        measured_values = mm1_simulation(generators, b=b, tau=tau, _lambda=_lambda, mu1=mu1, mu2=mu2)

        stats = print_stats(**measured_values)
        graphs.draw(**measured_values, **stats)

    if args.mapph1:
        results = map_ph_simulation(generators, b=b, tau=tau, C=C, D=D, omega=omega, S=S, beta=beta, T=T, alpha=alpha)
        arrivals, services, completions, blocks = results

        print('MAP/PH/1 stats:')
        print_stats(arrivals, services, completions, blocks, tau)
        graphs.draw(**{
            'arrivals': np.array(arrivals),
            'services': np.array(services),
            'completions': np.array(completions),
            'blocks': blocks,
            'tau': tau,
            'queue_name': 'MAP/PH/1'
        })

    if not (args.mm1 or args.mapph1):
        print("You didn't select any simulation to run.", file=sys.stderr)
        parser.print_help()
    else:
        plt.show()


def parameters_from(_dir):
    assert _dir.exists(), f"Directory '{_dir}' should exist."
    assert _dir.is_dir(), f"Directory '{_dir}' should be a directory."
    for name in ['C.csv', 'omega.csv', 'S.csv', 'beta.csv', 'T.csv', 'alpha.csv', 'b.csv', 'tau.csv', 'lambda.csv',
                 'mu1.csv', 'mu2.csv']:
        assert _dir.joinpath(name).exists(), f"File '{name}' should exist."

    b = int_from(_dir.joinpath('b.csv'))
    tau = float_from(_dir.joinpath('tau.csv'))

    _lambda = float_from(_dir.joinpath('lambda.csv'))
    mu1 = float_from(_dir.joinpath('mu1.csv'))
    mu2 = float_from(_dir.joinpath('mu2.csv'))

    C = matrix_from(_dir.joinpath('C.csv'))
    D = matrix_from(_dir.joinpath('D.csv'))
    omega = vector_from(_dir.joinpath('omega.csv'))
    assert len(C) == len(D) == len(omega), "C, D and omega must have the same size!"

    S = matrix_from(_dir.joinpath('S.csv'))
    beta = vector_from(_dir.joinpath('beta.csv'))
    assert len(S) == len(beta), "S and beta must have the same size!"

    T = matrix_from(_dir.joinpath('T.csv'))
    alpha = vector_from(_dir.joinpath('alpha.csv'))
    assert len(T) == len(alpha), "S and beta must have the same size!"

    return C, D, S, T, _lambda, alpha, b, beta, mu1, mu2, omega, tau


if __name__ == '__main__':
    main()
