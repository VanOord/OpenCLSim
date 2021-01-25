"""Component to process with the simulation objecs."""
import logging

from .simpy_object import SimpyObject

logger = logging.getLogger(__name__)


class Processor(SimpyObject):
    """
    Processor class.

    Adds the loading and unloading components and checks for possible downtime.

    If the processor class is used to allow "loading" or "unloading" the mixins "LoadingFunction" and "UnloadingFunction" should be added as well.
    If no functions are used a subcycle should be used, which is possible with the mixins "LoadingSubcycle" and "UnloadingSubcycle".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""


class LoadingFunction:
    """
    Create a loading function and add it a processor.

    This is a generic and easy to read function, you can create your own LoadingFunction class and add this as a mixin.

    Parameters
    ----------
    loading_rate : amount / second
        The rate at which units are loaded per second
    load_manoeuvring : seconds
        The time it takes to manoeuvring in minutes
    """

    def __init__(
        self, loading_rate: float, load_manoeuvring: float = 0, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.loading_rate = loading_rate
        self.load_manoeuvring = load_manoeuvring

    def loading(self, origin, destination, amount, id_="default"):
        """
        Determine the duration based on an amount that is given as input with processing.

        The origin an destination are also part of the input, because other functions might be dependent on the location.
        """
        if not hasattr(self.loading_rate, "__call__"):
            duration = amount / self.loading_rate + self.load_manoeuvring * 60
            return duration, amount
        else:
            loading_time = self.loading_rate(
                destination.container.get_level(id_),
                destination.container.get_level(id_) + amount,
            )
            duration = loading_time + self.load_manoeuvring * 60
            return duration, amount


class UnloadingFunction:
    """
    Create an unloading function and add it a processor.

    This is a generic and easy to read function, you can create your own LoadingFunction class and add this as a mixin.

    Parameters
    ----------
    unloading_rate : volume / second
        the rate at which units are loaded per second
    unload_manoeuvring : minutes
        the time it takes to manoeuvring in minutes
    """

    def __init__(
        self, unloading_rate: float, unload_manoeuvring: float = 0, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.unloading_rate = unloading_rate
        self.unload_manoeuvring = unload_manoeuvring

    def unloading(self, origin, destination, amount, id_="default"):
        """
        Determine the duration based on an amount that is given as input with processing.

        The origin an destination are also part of the input, because other functions might be dependent on the location.
        """

        if not hasattr(self.unloading_rate, "__call__"):
            duration = amount / self.unloading_rate + self.unload_manoeuvring * 60
            return duration, amount
        else:
            unloading_time = self.unloading_rate(
                origin.container.get_level(id_) + amount,
                origin.container.get_level(id_),
            )
            duration = unloading_time + self.unload_manoeuvring * 60
            return duration, amount
