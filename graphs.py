import inspect

import matplotlib.pyplot as plt
import numpy as np

GRAPH_HANDLERS = []


class Graph:
    """
    Decorator to register a function as a graph handler.
    Such decorated function will be called when graphs.draw is called
    The decorated function will receive the ax parameter along with any other available measure
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
        :return: A wrapper that gets func required parameters, create the graph and pass them along to func
        """

        def wrapper(**measures):
            signature = inspect.signature(func)
            keys = [param.name for param in signature.parameters.values()
                    if param.kind == param.POSITIONAL_OR_KEYWORD and param.name != 'ax']
            filtered_kwargs = {key: measures[key] for key in keys}

            fig, ax = plt.subplots()
            fig.canvas.manager.set_window_title(f"{self.title} ({measures['queue_name']})")

            ax.set(xlabel=self.xlabel, ylabel=self.ylabel,
                   title=self.title)
            return func(ax=ax, **filtered_kwargs)

        GRAPH_HANDLERS.append(wrapper)
        return wrapper


def draw(**measures):
    """
    Call all the GRAPH_HANDLERS registered with @graph
    
    :param measures: the measures passed to the functions
    :return: None
    """
    for graph_handler in GRAPH_HANDLERS:
        graph_handler(**measures)


@Graph("Temps d'attente des transactions", ylabel="Nombre de transactions", xlabel="Temps")
def waiting_time(arrivals, services, ax):
    waiting_times = services - arrivals

    ax.hist(waiting_times, bins='auto')


@Graph("Temps de bloc", xlabel="Temps", ylabel="Nombre de blocs")
def block_time(blocks, ax):
    block_times = np.array([b.mining for b in blocks])

    inter_block_times = block_times[1:] - block_times[:-1]

    ax.hist(inter_block_times, bins='auto')


@Graph("Temps de service", xlabel="Temps", ylabel="Nombre de transactions")
def service_time(services, completions, ax):
    service_durations = completions - services

    ax.hist(service_durations, bins='auto')


@Graph("Temps inter-arrivées", ylabel="Nombre d'arrivées", xlabel="Temps")
def inter_arrival_time(arrivals, ax):
    inter_arrival_times = arrivals[1:] - arrivals[:-1]

    ax.hist(inter_arrival_times, bins='auto')


@Graph("Trajectoire de la fil d'attente", ylabel="Nombre de transactions", xlabel="Temps")
def trajectory(arrivals, blocks, ax):
    # we need to replay the arrivals and blocks to evaluate the waiting room size
    arrival_deltas = list(zip(arrivals, np.ones(len(arrivals))))
    blocks_deltas = [(b.selection, -b.size) for b in blocks]
    zipped_deltas = arrival_deltas + blocks_deltas
    zipped_deltas.sort()
    timings, deltas = zip(*zipped_deltas)

    waiting_room = np.zeros(len(arrivals) + len(blocks))

    count = 0
    for idx, delta in enumerate(deltas):
        count += delta
        waiting_room[idx] = count

    ax.plot(timings, waiting_room)
