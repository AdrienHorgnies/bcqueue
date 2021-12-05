"""
Module handles the creation of graphs.

It provides a decoration Graph that helps quickly create a new graph and a function draw which actually draw the graphs
"""
import inspect

import matplotlib.pyplot as plt

GRAPH_HANDLERS = []


class Graph:
    """
    Decorator to register a function as a graph handler.
    Such decorated function will be called when graphs.draw is called
    The decorated function will receive the ax parameter along with any other available parameter.
     It is thus mandatory to define an ax parameter.
     The ax parameter is the AxesSubplot from matplotlib.pyplot.
    """

    def __init__(self, title, ylabel, xlabel):
        """
        :param title: The title of the graph
        :param ylabel: The label of the y-axis
        :param xlabel: The label of the x-axis
        """
        self.title = title
        self.ylabel = ylabel
        self.xlabel = xlabel

    def __call__(self, func):
        """
        Decorate the function, and register the wrapper

        :param func: The decorated function
        :return: A wrapper that filters func required parameters, creates the AxesSubplot and pass it along to func
        """

        def wrapper(**parameters):
            signature = inspect.signature(func)
            param_names = [param.name for param in signature.parameters.values()
                           if param.kind == param.POSITIONAL_OR_KEYWORD and param.name != 'ax']
            filtered_parameters = {key: parameters[key] for key in param_names}

            fig, ax = plt.subplots()
            fig.canvas.manager.set_window_title(f"{self.title} ({parameters['queue_name']})")

            ax.set(xlabel=self.xlabel, ylabel=self.ylabel,
                   title=self.title)
            return func(ax=ax, **filtered_parameters)

        GRAPH_HANDLERS.append(wrapper)
        return wrapper


def draw(**parameters):
    """
    Call all the functions decorated with @Graph, and provide them their required parameter
    
    :param parameters: a mapping of parameters names and values,
     containing at least the ones required by the @Graph decorated functions
    """
    for graph_handler in GRAPH_HANDLERS:
        graph_handler(**parameters)


@Graph("Temps d'attente des transactions", ylabel="Nombre de transactions", xlabel="Temps")
def waiting_duration(waiting_durations, ax):
    ax.hist(waiting_durations, bins='auto')


@Graph("Temps de bloc", xlabel="Temps", ylabel="Nombre de blocs")
def block_time(inter_block_times, ax):
    ax.hist(inter_block_times, bins='auto')


@Graph("Temps de service", xlabel="Temps", ylabel="Nombre de transactions")
def service_time(service_durations, ax):
    ax.hist(service_durations, bins='auto')


@Graph("Temps inter-arrivées", ylabel="Nombre d'arrivées", xlabel="Temps")
def inter_arrival_time(inter_arrival_times, ax):
    ax.hist(inter_arrival_times, bins='auto')


@Graph("Trajectoire de la fil d'attente", ylabel="Nombre de transactions", xlabel="Temps")
def trajectory(room_times, room_sizes, ax):
    ax.plot(room_times, room_sizes)
