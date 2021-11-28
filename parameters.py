"""
Module to handle the parsing of the parameters directory
"""
import builtins
import inspect
from keyword import iskeyword

import numpy as np


class Parameters:
    """
    Defines all the parameters required to run the simulations.

    Each class attribute with an annotation corresponds to a parameter definition.
     Python builtins and keyword name cannot be used, prefix them with an underscore.
    The annotation is used as the expected type of the parameter or its sub elements if the parameter is not scalar
    The value of the class attribute is used to convert the actual value of the parameter, other parameters can be used
     as argument of the converter function, but only if said parameters don't depend on other parameters as well.
    """
    b: int
    sigma: float = lambda sigma, tau: sigma if sigma > 1 else sigma * tau
    tau: float
    upsilon: float = lambda upsilon, tau: upsilon if upsilon > 1 else upsilon * tau

    _lambda: float
    mu1: float
    mu2: float

    C: float
    D: float
    omega: float

    S: float
    beta: float
    T: float
    alpha: float

    @classmethod
    def get_from(cls, _dir):
        """
        Load all parameters from _dir

        :param _dir: the path to the directory containing the csv files defining all the parameters
        :return: A mapping of the parameters and their value
        :rtype: dict
        """
        param_definitions = cls.__annotations__

        assert _dir.exists(), f"Directory '{_dir}' should exist."
        assert _dir.is_dir(), f"Directory '{_dir}' should be a directory."

        p = {}
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
                exit(f"Could not parse {file}")

        convertibles = [pd for pd in param_definitions if hasattr(cls, pd)]
        for param_name in convertibles:
            converter = getattr(cls, param_name)
            sig = inspect.signature(converter)
            args = [p[arg] for arg in sig.parameters]
            p[param_name] = converter(*args)

        assert not param_definitions.keys() - p.keys(), f"Missing parameter(s) {param_definitions.keys() - p.keys()}"
        assert not p.keys() - param_definitions.keys(), f"Extraneous parameter(s) {p.keys() - param_definitions.keys()}"

        assert len(p['C']) == len(p['D']) == len(p['omega']), "C, D and omega must have the same size!"
        assert len(p['S']) == len(p['beta']), "S and beta must have the same size!"
        assert len(p['T']) == len(p['alpha']), "S and beta must have the same size!"

        return p
