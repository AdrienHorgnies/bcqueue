import inspect

import matplotlib.pyplot as plt

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
