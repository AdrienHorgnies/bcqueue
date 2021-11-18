"""
Orchestrate the simulations and generate the figures presenting the results
"""
import argparse
import sys

from numpy.random import SeedSequence, SFC64, Generator
from pathlib import Path
import csv

from measures import print_stats, print_graphs
from simulations import mm1_simulation, map_ph_simulation

SEED_SEQUENCE = SeedSequence()


def csv_to_matrix(path):
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


def csv_to_vector(path):
    with open(path) as file:
        reader = csv.reader(file)
        vector = next(reader)
        return [float(el.replace(' ', '')) for el in vector]


def csv_to_num(path):
    with open(path) as file:
        reader = csv.reader(file)
        line = next(reader)
        return float(line[0].replace(' ', ''))


def main():
    # ARGUMENTS
    description = 'Simulate a proof-of-work blockchain system with a M/M/1 or MAP/PH/1 queue.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('parameters_dir', nargs='?', type=str, default='parameters',
                        help='path to directory containing the parameters (README for details)')
    parser.add_argument('--seed', type=int, help='seed to initialize the random generator')
    parser.add_argument('--mm1', action='store_true', help='run the simulation with M/M/1 queue')
    parser.add_argument('--mapph1', action='store_true', help='run the simulation with MAP/PH/1 queue')
    args = parser.parse_args()

    parameters_dir = Path(args.parameters_dir)
    assert parameters_dir.exists(), f"Directory '{parameters_dir}' should exist."
    assert parameters_dir.is_dir(), f"Directory '{parameters_dir}' should be a directory."
    for name in ['C.csv', 'omega.csv', 'S.csv', 'beta.csv', 'T.csv', 'alpha.csv', 'b.csv', 'tau.csv', 'lambda.csv',
                 'mu1.csv', 'mu2.csv']:
        assert parameters_dir.joinpath(name).exists(), f"File '{name}' should exist."

    b = csv_to_vector(parameters_dir.joinpath('b.csv'))
    tau = csv_to_num(parameters_dir.joinpath('tau.csv'))

    C = csv_to_matrix(parameters_dir.joinpath('C.csv'))
    D = csv_to_matrix(parameters_dir.joinpath('D.csv'))
    omega = csv_to_vector(parameters_dir.joinpath('omega.csv'))
    assert len(C) == len(D) == len(omega), "C, D and omega must have the same size!"
    S = csv_to_vector(parameters_dir.joinpath('S.csv'))
    beta = csv_to_vector(parameters_dir.joinpath('beta.csv'))
    assert len(S) == len(beta), "S and beta must have the same size!"
    T = csv_to_vector(parameters_dir.joinpath('T.csv'))
    alpha = csv_to_vector(parameters_dir.joinpath('alpha.csv'))
    assert len(T) == len(alpha), "S and beta must have the same size!"

    _lambda = csv_to_num(parameters_dir.joinpath('lambda.csv'))
    mu1 = csv_to_num(parameters_dir.joinpath('mu1.csv'))
    mu2 = csv_to_num(parameters_dir.joinpath('mu2.csv'))

    # SETUP
    global SEED_SEQUENCE
    if args.seed:
        SEED_SEQUENCE = SeedSequence(args.seed)
    print('Seed : ', SEED_SEQUENCE.entropy)
    generators = [Generator(SFC64(stream)) for stream in SEED_SEQUENCE.spawn(10)]

    if args.mm1:
        arrivals, waitings, blocks = mm1_simulation(generators, b=b, tau=tau, _lambda=_lambda, mu1=mu1, mu2=mu2)

        print('M/M/1 stats:')
        print_stats(arrivals, waitings, blocks)
        print_graphs(arrivals, waitings, blocks)

    if args.mapph1:
        results = map_ph_simulation(generators, b=b, tau=tau, C=C, D=D, omega=omega, S=S, beta=beta, T=T, alpha=alpha)
        arrivals, waitings, blocks = results

        print('MAP/PH/1 stats:')
        print_stats(arrivals, waitings, blocks)
        print_graphs(arrivals, waitings, blocks)

    if not (args.mm1 or args.mapph1):
        print("You didn't select any simulation to run.", file=sys.stderr)
        parser.print_help()


if __name__ == '__main__':
    main()
