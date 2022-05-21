"""
Module which defines and parse the parameters required to run the simulation
"""
import builtins
import inspect
from keyword import iskeyword

import numpy as np


class Rule:
    """
    Dummy class to annotate a rule in the Parameters class.
    """
    pass


class Parameters:
    """
    Defines all the parameters required to run the simulations.
    For more details on how they are used, read the README.

    A parameter is defined by a class attribute with an annotation other than Rule.
      A parameter is defined by its name (name of the class attribute), its type (annotation) and converter (value).
      Python builtins and keyword name cannot be used, prefix them with an underscore.
      If the parameter is a structured type, the annotation is used for the sub elements of the structure.
      If present, the converter receives actual value of parameters and returns the new value to use.

    A rule is defined by a class attribute with an annotation Rule.
      A rule's value must be a tuple (lambda, message).
      The lambda can use any defined parameter and must return True if rule is respected, False otherwise.
      If the rule is not respected, raise an AssertionError and print the provided message.
    """
    b: int
    sigma: float = lambda sigma, tau: sigma if sigma > 1 else sigma * tau
    tau: float
    upsilon: float = lambda upsilon, tau: upsilon if upsilon > 1 else upsilon * tau
    b_min: Rule = lambda b: b > 0, "b must be a strict positive integer."
    sigma_tau: Rule = lambda sigma, tau: 0 < sigma < tau, "0 < sigma < tau"
    upsilon_min: Rule = lambda upsilon: upsilon > 0, "upsilon must be strictly positive"

    _lambda: float
    mu1: float
    mu2: float
    lambda_min: Rule = lambda _lambda: _lambda > 0, "_lambda > 0"
    mu1_min: Rule = lambda mu1: mu1 > 0, "mu1 > 0"
    mu2_min: Rule = lambda mu2: mu2 > 0, "mu2 > 0"

    C: float
    D: float
    omega: float
    map_dimensions: Rule = lambda C, D, omega: len(C) == len(D) == len(omega), "C, D and omega must have the same size!"

    S: float
    beta: float
    ph_selection_size: Rule = lambda S, beta: len(S) == len(beta), "S and beta must have the same size!"

    T: float
    alpha: float
    ph_broadcast_size: Rule = lambda T, alpha: len(T) == len(alpha), "T and alpha must have the same size!"

    ratios: float

    @classmethod
    def get_from(cls, _dir):
        """
        Load all parameters from _dir

        :param _dir: the path to the directory containing the csv files defining all the parameters
        :return: A mapping of the parameters and their value
        :rtype: dict
        """
        assert _dir.exists(), f"Directory '{_dir}' should exist."
        assert _dir.is_dir(), f"Directory '{_dir}' should be a directory."

        param_definitions = {name: definition for name, definition in cls.__annotations__.items() if
                             not issubclass(definition, Rule)}

        # parameters
        p = {}

        # Loading parameter values from files
        for file in _dir.iterdir():
            param_name = file.stem
            if iskeyword(param_name) or param_name in dir(builtins):
                param_name = '_' + param_name

            try:
                dtype = param_definitions[param_name]
            except KeyError:
                exit(f"Parameter definition for {param_name!a} is missing its type annotation.")

            try:
                p[param_name] = np.loadtxt(file, delimiter=',', dtype=dtype)
            except ValueError:
                exit(f"Could not parse {file}, should be a CSV!")

        assert not param_definitions.keys() - p.keys(), f"Missing parameter(s) {param_definitions.keys() - p.keys()}"
        assert not p.keys() - param_definitions.keys(), f"Extraneous parameter(s) {p.keys() - param_definitions.keys()}"

        # Convert the value of parameters defining a converter function.
        convertibles = [pd for pd in param_definitions if hasattr(cls, pd)]
        for param_name in convertibles:
            converter = getattr(cls, param_name)
            sig = inspect.signature(converter)
            args = [p[arg] for arg in sig.parameters]

            p[param_name] = converter(*args)

        # Checking that all rules are respected
        rules = {name: rule for name, rule in cls.__annotations__.items() if issubclass(rule, Rule)}
        for rule_name, rule in rules.items():
            assert hasattr(cls, rule_name), f"You forgot to provide a lambda and assert message, for {rule_name!a}."
            rule_func = getattr(cls, rule_name)[0]
            fail_msg = getattr(cls, rule_name)[1]

            sig = inspect.signature(rule_func)
            args = [p[arg] for arg in sig.parameters]
            assert rule_func(*args), fail_msg

        return p
