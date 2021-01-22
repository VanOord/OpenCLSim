"""Component to process with the simulation objecs."""
import logging

from .container import HasContainer
from .log import Log, LogState
from .resource import HasResource
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

    def process(
        self,
        origin,
        destination,
        shiftamount_fcn,
        id_="default",
    ):
        """
        Move content from ship to the site or from the site to the ship.

        This to ensure that the ship's container reaches the desired level.
        Yields the time it takes to process.
        """

        assert isinstance(origin, HasContainer)
        assert isinstance(destination, HasContainer)
        assert isinstance(origin, HasResource)
        assert isinstance(destination, HasResource)
        assert isinstance(self, Log)
        assert isinstance(origin, Log)
        assert isinstance(destination, Log)
        assert self.is_at(origin)
        assert destination.is_at(origin)

        # Log the process for all parts
        for location in set([self, origin, destination]):
            location.log_entry(
                t=location.env.now,
                activity_id=self.activity_id,
                activity_state=LogState.START,
            )

        succeeded = False
        nr_tries = 0
        while not succeeded and nr_tries < 200:
            nr_tries += 1
            try:
                duration, amount = shiftamount_fcn(origin, destination)
                assert amount > 0, "Nothing is transfered"

                yield self.env.all_of(
                    [
                        origin.container.get_available(amount=amount, id_=id_),
                        destination.container.put_available(amount=amount, id_=id_),
                    ]
                )

                assert origin.container.get_available(
                    amount=amount, id_=id_
                ).triggered, "Origin is empty"
                assert destination.container.put_available(
                    amount=amount, id_=id_
                ).triggered, "destination is full"

                succeeded = True
            except Exception as e:
                print(e)
                logger.info(e)
                pass

        yield from self.get_from_origin(origin, amount, id_)
        yield self.env.timeout(duration)
        yield from self.put_in_destination(destination, amount, id_)

        # Log the process for all parts
        for location in set([self, origin, destination]):
            location.log_entry(
                t=location.env.now,
                activity_id=self.activity_id,
                activity_state=LogState.STOP,
            )

    def get_from_origin(self, origin, amount, id_="default"):
        start_time = self.env.now
        yield origin.container.get(amount, id_)
        end_time = self.env.now

        if start_time != end_time:
            self.log_entry(
                t=start_time,
                activity_id=self.activity_id,
                activity_state=LogState.WAIT_START,
                activity_label={
                    "type": "subprocess",
                    "ref": "waiting origin content",
                },
            )
            self.log_entry(
                t=end_time,
                activity_id=self.activity_id,
                activity_state=LogState.WAIT_STOP,
                activity_label={
                    "type": "subprocess",
                    "ref": "waiting origin content",
                },
            )

    def put_in_destination(self, destination, amount, id_="default"):
        start_time = self.env.now
        yield destination.container.put(amount, id_=id_)
        end_time = self.env.now

        if start_time != end_time:
            self.log_entry(
                t=start_time,
                activity_id=self.activity_id,
                activity_state=LogState.WAIT_START,
                activity_label={
                    "type": "subprocess",
                    "ref": "waiting destination content",
                },
            )
            self.log_entry(
                t=end_time,
                activity_id=self.activity_id,
                activity_state=LogState.WAIT_STOP,
                activity_label={
                    "type": "subprocess",
                    "ref": "waiting destination content",
                },
            )


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
