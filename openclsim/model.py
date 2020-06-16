from functools import partial
import openclsim.core as core
import simpy
import numpy as np

from abc import ABC


class AbstractPluginClass(ABC):
    """Abstract class used as the basis for all Classes implementing a plugin for a specific Activity. 
    Instance checks will be performed on this class level."""

    def __init__(self, plugin_name, activity):
        self.plugin_name = plugin_name
        self.activity = activity

    def pre_process(self, *args, **kwargs):
        return {}

    def post_process(self, *args, **kwargs):
        return {}


class PluginActivity(core.Identifiable, core.Log):
    """"This is the base class for all activities which will provide a plugin mechanism. 
    The plugin mechanism foresees that the plugin function pre_process is called before the activity is executed, while
    the function post_process is called after the activity has been executed."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugins = list()

    def get_priority(self, elem):
        return elem["priority"]

    def register_plugin(self, plugin, priority=0):
        self.plugins.append({"priority": priority, "plugin": plugin})
        self.plugins = sorted(self.plugins, key=self.get_priority)

    def pre_process(self, args_data):
        # iterating over all registered plugins for this activity calling pre_process
        for item in self.plugins:
            yield from item["plugin"].pre_process(**args_data)

    def post_process(self, *args, **kwargs):
        # iterating over all registered plugins for this activity calling post_process
        for item in self.plugins:
            item["plugin"].post_process(*args, **kwargs)

    def delay_processing(self, env, delay_name, activity_log, waiting):
        """Waiting must be a delay expressed in seconds"""
        print(f"delay processing {waiting}")
        activity_log.log_entry(
            delay_name, env.now, -1, None, activity_log.id, core.LogState.WAIT_START
        )
        print(f"before delay {env.now}")
        yield env.timeout(waiting)
        print(f"after delay {env.now}")
        activity_log.log_entry(
            delay_name, env.now, -1, None, activity_log.id, core.LogState.WAIT_STOP
        )


class GenericActivity(PluginActivity):
    """The GenericActivity Class forms a generic class which sets up all required mechanisms to control 
    an activity by providing a start event. Since it is generic, a parameter of the initialization
    is the main process, which is provided by an inheriting class
    main_proc  : the main process to be executed
    start_event: the activity will start as soon as this event is triggered
                 by default will be to start immediately
    requested_resources: a call by refernce value to a dictionary of resources, which have been requested and not released yet.
    keep_resources: a list of resources, which should not be released at the end of the activity
    postpone_start: if set to True, the activity will not be directly started in the simpy environment, 
                but will be started by a structrual activity, like sequential or while activity.
    """

    def __init__(
        self,
        registry,
        postpone_start=False,
        start_event=None,
        requested_resources=dict(),
        keep_resources=list(),
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        """Initialization"""
        if "name" not in registry:
            registry["name"] = {}
        if self.name not in registry["name"]:
            l_ = []
        else:
            l_ = registry["name"][self.name]
        l_.append(self)
        registry["name"][self.name] = l_
        if "id" not in registry:
            registry["id"] = {}
        if self.id not in registry["id"]:
            l_ = []
        else:
            l_ = registry["id"][self.id]
        l_.append(self)
        registry["id"][self.id] = l_

        self.registry = registry
        self.postpone_start = postpone_start
        self.start_event = start_event
        self.requested_resources = requested_resources
        self.keep_resources = keep_resources
        self.done_event = self.env.event()

    def register_process(self, main_proc, show=False, additional_logs=[]):
        # replace the done event
        self.done_event = self.env.event()

        start_event = None
        if self.start_event != None:
            print(f"start event expression {self.start_event}")
            start_event = self.parse_expression(self.start_event)
            print(f"start event {start_event}")
        start_event_instance = start_event
        (
            start_event
            if start_event is None or isinstance(start_event, simpy.Event)
            else self.env.all_of(events=start_event)
        )
        print(f"start event instance {start_event_instance}")
        if start_event_instance is not None:
            main_proc = partial(
                delayed_process,
                start_event=start_event_instance,
                sub_processes=[main_proc],
                additional_logs=additional_logs,
                requested_resources=self.requested_resources,
                keep_resources=self.keep_resources,
            )
        self.main_proc = main_proc
        if not self.postpone_start:
            self.main_process = self.env.process(
                self.main_proc(activity_log=self, env=self.env)
            )

    def parse_expression(self, expr):
        """Parsing of the expression language used for start_events and conditional_events."""
        res = []
        if not isinstance(expr, list):
            raise Exception(
                f"expression must be a list, but is {type(expr)}. Therefore it can not be parsed: {expr}"
            )
        for key_val in expr:
            if isinstance(key_val, dict):
                if "and" in key_val:
                    partial_res = self.parse_expression(key_val["and"])
                    self.env.timeout(0)
                    res.append(
                        # self.env.all_of(events=[event() for event in partial_res])
                        self.env.all_of(events=partial_res)
                    )
                    self.env.timeout(0)
                elif "or" in key_val:
                    partial_res = self.parse_expression(key_val["or"])
                    self.env.timeout(0)
                    for item in partial_res:
                        print(
                            f"evaluate event {item} as triggered {item.triggered} and processed {item.processed}"
                        )
                    res.append(
                        # self.env.any_of(events=[event() for event in partial_res])
                        self.env.any_of(events=partial_res)
                    )
                    self.env.timeout(0)
                elif "type" in key_val:
                    if key_val["type"] == "container":
                        id_ = None
                        if "id_" in key_val:
                            id_ = key_val["id_"]
                        state = key_val["state"]
                        obj = key_val["concept"]
                        if isinstance(obj, core.HasContainer):
                            if state == "full":
                                if id_ != None:
                                    res.append(obj.container.get_full_event(id_=id_))
                                else:
                                    res.append(obj.container.get_full_event())
                            elif state == "empty":
                                if id_ != None:
                                    res.append(obj.container.get_empty_event(id_=id_))
                                else:
                                    res.append(obj.container.get_empty_event())
                            else:
                                raise Exception(
                                    f"Unknown state {state} for a container event"
                                )
                        else:
                            raise Exception(
                                f"Referneced concept in a container expression is not of type HasContainer, but of type {type(obj)}"
                            )
                    elif key_val["type"] == "activity":
                        state = key_val["state"]
                        if state != "done":
                            raise Exception(
                                f"Unknown state {state} in ActivityExpression."
                            )
                        activity_ = None
                        key = "unknown"
                        if "ID" in key_val:
                            key = key_val["ID"]
                            if "id" in self.registry:
                                if key in self.registry["id"]:
                                    activity_ = self.registry["id"][key]
                        elif "name" in key_val:
                            key = key_val["name"]
                            if "name" in self.registry:
                                if key in self.registry["name"]:
                                    activity_ = self.registry["name"][key]
                        if activity_ == None:
                            raise Exception(
                                f"No activity found in ActivityExpression for id/name {key}"
                            )
                        if isinstance(activity_, list):
                            if len(activity_) == 1:
                                res.append(activity_[0].get_done_event())
                            else:
                                res.extend(
                                    [
                                        activity_item.get_done_event()
                                        for activity_item in activity_
                                    ]
                                )
                        else:
                            res.append(activity_[0].get_done_event())
                else:
                    raise Exception(
                        f"Logical AND can not have an additional key next to it. {expr}"
                    )
        if len(res) > 1:
            return res
        elif len(res) == 1:
            return res[0]
        return res

    def get_done_event(self):
        if self.postpone_start:
            return self.done_event
        elif hasattr(self, "main_process"):
            return self.main_process
        else:
            return self.done_event

    def call_main_proc(self, activity_log, env):
        res = self.main_proc(activity_log=activity_log, env=env)
        return res

    def end(self):
        print(f"Activity end({self.name})")
        self.done_event.succeed()


class MoveActivity(GenericActivity):
    """The MoveActivity Class forms a specific class for a single move activity within a simulation.
    It deals with a single origin container, destination container and a single combination of equipment
    to move substances from the origin to the destination. It will initiate and suspend processes
    according to a number of specified conditions. To run an activity after it has been initialized call env.run()
    on the Simpy environment with which it was initialized.

    To check when a transportation of substances can take place, the Activity class uses three different condition
    arguments: start_condition, stop_condition and condition. These condition arguments should all be given a condition
    object which has a satisfied method returning a boolean value. True if the condition is satisfied, False otherwise.

    destination: object inheriting from HasContainer, HasResource, Locatable, Identifiable and Log
    mover: moves to 'origin' if it is not already there, is loaded, then moves to 'destination' and is unloaded
           should inherit from Movable, HasContainer, HasResource, Identifiable and Log
           after the simulation is complete, its log will contain entries for each time it started moving,
           stopped moving, started loading / unloading and stopped loading / unloading
    start_event: the activity will start as soon as this event is triggered
                 by default will be to start immediately
    """

    def __init__(self, mover, destination, show=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.destination = destination
        self.mover = mover
        self.print = show
        if not self.postpone_start:
            self.start()

    def start(self):
        main_proc = partial(
            move_process,
            name=self.name,
            destination=self.destination,
            mover=self.mover,
            requested_resources=self.requested_resources,
            keep_resources=self.keep_resources,
            activity=self,
        )
        self.register_process(main_proc=main_proc, show=self.print)


class BasicActivity(GenericActivity):
    """The BasicActivity Class is a generic class to describe an activity, which does not require any specific resource, 
    but has a specific duration.

    duration: time required to perform the described activity.
    additional_logs: list of other concepts, where the start and the stop of the basic activity should be recorded.
    start_event: the activity will start as soon as this event is triggered
                 by default will be to start immediately
    """

    def __init__(self, duration, additional_logs=[], show=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""

        self.print = show
        self.duration = duration
        self.additional_logs = additional_logs
        # print(f"BasicActivity {self.name} - postpone_start {self.postpone_start}")
        if not self.postpone_start:
            self.start()

    def start(self):
        main_proc = partial(
            basic_process,
            name=self.name,
            duration=self.duration,
            additional_logs=self.additional_logs,
            requested_resources=self.requested_resources,
            keep_resources=self.keep_resources,
        )
        self.register_process(
            main_proc=main_proc, show=self.print, additional_logs=self.additional_logs
        )


class SequentialActivity(GenericActivity):
    """The SequenceActivity Class forms a specific class for executing multiple activities in a dedicated order within a simulation.
    It is a structural activity, which does not require specific resources.
    
    sub_processes: a list of activities to be executed in the provided sequence.
    start_event: the activity will start as soon as this event is triggered
                 by default will be to start immediately
    """

    def __init__(self, sub_processes, show=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""

        self.print = show
        self.sub_processes = sub_processes
        if not self.postpone_start:
            self.start()

    def start(self):
        main_proc = partial(
            sequential_process,
            name=self.name,
            sub_processes=self.sub_processes,
            requested_resources=self.requested_resources,
            keep_resources=self.keep_resources,
        )
        self.register_process(main_proc=main_proc, show=self.print)


class WhileActivity(GenericActivity):
    """The WhileActivity Class forms a specific class for executing multiple activities in a dedicated order within a simulation.
    The while activity is a structural activity, which does not require specific resources.

    sub_process: the sub_process which is executed in every iteration
    condition_event: a condition event provided in the expression language which will stop the iteration as soon as the event is fulfilled.    
    start_event: the activity will start as soon as this event is triggered
                 by default will be to start immediately
    """

    #     activity_log, env, stop_event, sub_processes, requested_resources, keep_resources
    def __init__(self, sub_process, condition_event, show=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""

        self.print = show
        print(f"while Activity keep_resources {self.keep_resources}")
        self.sub_process = sub_process
        if not self.sub_process.postpone_start:
            raise Exception(
                f"In While activity {self.name} the sub_process must have postpone_start=True"
            )
        self.condition_event = condition_event
        if not self.postpone_start:
            self.start()

    def start(self):
        main_proc = partial(
            conditional_process,
            name=self.name,
            sub_process=self.sub_process,
            condition_event=self.parse_expression(self.condition_event),
            requested_resources=self.requested_resources,
            keep_resources=self.keep_resources,
        )
        self.register_process(main_proc=main_proc, show=self.print)


class ShiftAmountActivity(GenericActivity):
    """The ShiftAmountActivity Class forms a specific class for shifting material from an origin to a destination.
    It deals with a single origin container, destination container and a single processor
    to move substances from the origin to the destination. It will initiate and suspend processes
    according to a number of specified conditions. To run an activity after it has been initialized call env.run()
    on the Simpy environment with which it was initialized.

    
    origin: container where the source objects are located.
    destination: container, where the objects are assigned to
    processor: resource responsible to implement the transfer.
    amount: the maximum amount of objects to be transfered.
    duration: time specified in seconds on how long it takes to transfer the objects.
    id_: in case of MultiContainers the id_ of the container, where the objects should be removed from or assiged to respectively.
    start_event: the activity will start as soon as this event is triggered
                 by default will be to start immediately
    """

    def __init__(
        self,
        processor,
        origin,
        destination,
        duration=None,
        amount=None,
        id_="default",
        show=False,
        phase=None,  # loading / unloading
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.origin = origin
        self.destination = destination

        self.processor = processor
        self.amount = amount
        self.duration = duration
        self.id_ = id_
        self.print = show
        self.phase = phase
        if not self.postpone_start:
            self.start()

    def start(self):
        print(f"SHift amount Activity keep_resources {self.keep_resources}")

        main_proc = partial(
            shift_amount_process,
            name=self.name,
            processor=self.processor,
            origin=self.origin,
            destination=self.destination,
            amount=self.amount,
            duration=self.duration,
            id_=self.id_,
            requested_resources=self.requested_resources,
            keep_resources=self.keep_resources,
            activity=self,
            phase=self.phase,
        )
        self.register_process(main_proc=main_proc, show=self.print)


def delayed_process(
    activity_log,
    env,
    start_event,
    sub_processes,
    requested_resources,
    keep_resources,
    additional_logs=[],
):
    """"Returns a generator which can be added as a process to a simpy.Environment. In the process the given
    sub_processes will be executed after the given start_event occurs.

    activity_log: the core.Log object in which log_entries about the activities progress will be added.
    env: the simpy.Environment in which the process will be run
    start_event: a simpy.Event object, when this event occurs the delayed process will start executing its sub_processes
    sub_processes: an Iterable of methods which will be called with the activity_log and env parameters and should
                   return a generator which could be added as a process to a simpy.Environment
                   the sub_processes will be executed sequentially, in the order in which they are given after the
                   start_event occurs
    """
    if hasattr(start_event, "__call__"):
        start_event = start_event()
    activity_log.log_entry(
        activity_log.name, env.now, -1, None, activity_log.id, core.LogState.WAIT_START
    )
    if isinstance(additional_logs, list) and len(additional_logs) > 0:
        for log in additional_logs:
            for sub_process in sub_processes:
                log.log_entry(
                    activity_log.name,
                    env.now,
                    -1,
                    None,
                    activity_log.id,
                    core.LogState.WAIT_START,
                )
    print(f"delayed process : {start_event}")
    yield start_event
    print(f"delayed process : after yield {start_event.processed}")
    activity_log.log_entry(
        activity_log.name, env.now, -1, None, activity_log.id, core.LogState.WAIT_STOP
    )
    if isinstance(additional_logs, list) and len(additional_logs) > 0:
        for log in additional_logs:
            for sub_process in sub_processes:
                log.log_entry(
                    activity_log.name,
                    env.now,
                    -1,
                    None,
                    activity_log.id,
                    core.LogState.WAIT_STOP,
                )

    for sub_process in sub_processes:
        print(f"delayed process start subprocess {sub_process}")
        yield from sub_process(activity_log=activity_log, env=env)


def conditional_process(
    activity_log,
    env,
    condition_event,
    sub_process,
    name,
    requested_resources,
    keep_resources,
):
    """Returns a generator which can be added as a process to a simpy.Environment. In the process the given
    sub_process will be executed until the given condition_event occurs. If the condition_event occurs during the execution
    of the sub_process, the conditional process will first complete the sub_process before finishing its own process.

    activity_log: the core.Log object in which log_entries about the activities progress will be added.
    env: the simpy.Environment in which the process will be run
    condition_event: a simpy.Event object, when this event occurs, the conditional process will finish executing its current
                run of its sub_processes and then finish
    sub_process: an Iterable of methods which will be called with the activity_log and env parameters and should
                   return a generator which could be added as a process to a simpy.Environment
                   the sub_processes will be executed sequentially, in the order in which they are given as long
                   as the stop_event has not occurred.
    """
    if activity_log.log["Message"]:
        if activity_log.log["Message"][-1] == "delayed activity started" and hasattr(
            condition_event, "__call__"
        ):
            condition_event = condition_event()

    if hasattr(condition_event, "__call__"):
        condition_event = condition_event()
    elif type(condition_event) == list:
        condition_event = env.any_of(events=[event() for event in condition_event])

    activity_log.log_entry(
        f"conditional process {name}",
        env.now,
        -1,
        None,
        activity_log.id,
        core.LogState.START,
    )
    ii = 0
    while (not condition_event.processed) and ii < 100:
        print(sub_process)
        # for sub_process_ in (proc for proc in [sub_process]):
        print("conditional ")
        activity_log.log_entry(
            f"sub process {sub_process.name}",
            env.now,
            -1,
            None,
            activity_log.id,
            core.LogState.START,
        )
        sub_process.start()
        yield from sub_process.call_main_proc(activity_log=activity_log, env=env)
        sub_process.end()
        activity_log.log_entry(
            f"sub process {sub_process.name}",
            env.now,
            -1,
            None,
            activity_log.id,
            core.LogState.STOP,
        )
        # work around for the event evaluation
        # this delay of 0 time units ensures that the simpy environment gets a chance to evaluate events
        # which will result in triggered but not processed events to be taken care of before further progressing
        # maybe there is a better way of doing it, but his option works for now.
        yield env.timeout(0)
        print(
            f"condition event triggered: {condition_event.triggered} {condition_event.processed} round {ii}"
        )
        print(f"while loop requested_resources {requested_resources}")
        print(f"while loop keep_resources {keep_resources}")
        ii = ii + 1
    activity_log.log_entry(
        f"conditional process {name}",
        env.now,
        -1,
        None,
        activity_log.id,
        core.LogState.STOP,
    )


def basic_process(
    activity_log,
    env,
    name,
    duration,
    requested_resources,
    keep_resources,
    additional_logs=[],
):
    """Returns a generator which can be added as a process to a simpy.Environment. The process will report the start of the 
    activity, delay the execution for the provided duration, and finally report the completion of the activiy.

    activity_log: the core.Log object in which log_entries about the activities progress will be added.
    env: the simpy.Environment in which the process will be run
    stop_event: a simpy.Event object, when this event occurs, the conditional process will finish executing its current
                run of its sub_processes and then finish
    sub_processes: an Iterable of methods which will be called with the activity_log and env parameters and should
                   return a generator which could be added as a process to a simpy.Environment
                   the sub_processes will be executed sequentially, in the order in which they are given as long
                   as the stop_event has not occurred.
    """
    # print(f"basic process {name} start")
    activity_log.log_entry(
        name, env.now, duration, None, activity_log.id, core.LogState.START
    )
    if isinstance(additional_logs, list) and len(additional_logs) > 0:
        for log_item in additional_logs:
            log_item.log_entry(
                name, env.now, duration, None, activity_log.id, core.LogState.START
            )

    yield env.timeout(duration)
    activity_log.log_entry(
        name, env.now, duration, None, activity_log.id, core.LogState.STOP
    )
    if isinstance(additional_logs, list) and len(additional_logs) > 0:
        for log_item in additional_logs:
            log_item.log_entry(
                name, env.now, duration, None, activity_log.id, core.LogState.STOP
            )
    # print(f"basic process {name} end")


def _request_resource_if_available(
    env,
    resource_requests,
    site,
    processor,
    amount,
    kept_resource,
    ActivityID,
    id_="default",
    engine_order=1.0,
    verbose=False,
):
    all_available = False
    while not all_available and amount > 0:
        # yield until enough content and space available in origin and destination
        yield env.all_of(events=[site.container.get_available(amount, id_)])

        yield from _request_resource(resource_requests, processor.resource)
        print(f"processor request : {resource_requests}")
        if site.container.get_level(id_) < amount:
            # someone removed / added content while we were requesting the processor, so abort and wait for available
            # space/content again
            _release_resource(
                resource_requests, processor.resource, kept_resource=kept_resource
            )
            continue

        if not processor.is_at(site):
            # todo have the processor move simultaneously with the mover by starting a different process for it?
            yield from _move_mover(
                processor,
                site,
                ActivityID=ActivityID,
                engine_order=engine_order,
                verbose=verbose,
            )
            if site.container.get_level(id_) < amount:
                # someone messed us up again, so return to waiting for space/content
                _release_resource(
                    resource_requests, processor.resource, kept_resource=kept_resource
                )
                continue

        yield from _request_resource(resource_requests, site.resource)
        print(f"site request : {resource_requests}")
        if site.container.get_level(id_) < amount:
            _release_resource(
                resource_requests, processor.resource, kept_resource=kept_resource
            )
            _release_resource(
                resource_requests, site.resource, kept_resource=kept_resource
            )
            continue
        all_available = True
        print(f"end requestIfAvailable : {resource_requests}")


def shift_amount_process(
    activity_log,
    env,
    processor,
    origin,
    destination,
    name,
    duration,
    activity,
    amount=None,
    requested_resources={},
    keep_resources=[],
    id_="default",
    engine_order=1.0,
    stop_reservation_waiting_event=None,
    phase=None,
):
    """Origin and Destination are of type HasContainer """
    assert processor.is_at(origin)
    assert destination.is_at(origin)

    if not isinstance(origin, core.HasContainer) or not isinstance(
        destination, core.HasContainer
    ):
        raise Exception("Invalide use of method shift_amount")

    verbose = True
    filling = 1.0
    resource_requests = requested_resources
    print(f"start : {resource_requests}")

    if not hasattr(activity_log, "processor"):
        activity_log.processor = processor
    if not hasattr(activity_log, "mover"):
        activity_log.mover = origin
    amount, all_amounts = processor.determine_processor_amount(
        [origin], destination, amount, id_
    )

    if 0 != amount:

        yield from _request_resource(resource_requests, destination.resource)
        print(f"destination request : {resource_requests}")
        print(f"shift amount process keep_resources {keep_resources}")

        yield from _request_resource_if_available(
            env,
            resource_requests,
            origin,
            processor,
            amount,
            None,  # for now release all
            activity_log.id,
            id_,
            engine_order,
            verbose=False,
        )
        print(f"after req resource if available : {resource_requests}")
        activity_log.log_entry(
            name, env.now, amount, None, activity_log.id, core.LogState.START
        )

        if duration is not None:
            rate = None
        elif duration is not None:
            rate = processor.loading

        elif phase == "loading":
            rate = processor.loading
        elif phase == "unloading":
            rate = processor.unloading
        else:
            raise RuntimeError(
                f"Both the pase (loading / unloading) and the duration of the shiftamount activity are undefined. At least one is required!"
            )

        start_time = env.now
        args_data = {
            "env": env,
            "processor": processor,
            "origin": origin,
            "destination": destination,
            "engine_order": engine_order,
            "activity_log": activity_log,
            "message": name,
            "activity": activity,
            "duration": duration,
            "amount": amount,
        }
        yield from activity.pre_process(args_data)

        start_shift = env.now
        print("_shift_amount")
        yield from _shift_amount(
            env,
            processor,
            origin,
            origin.container.get_level(id_) + amount,
            destination,
            ActivityID=activity_log.id,
            duration=duration,
            rate=rate,
            id_=id_,
            verbose=verbose,
        )

        args_data["start_preprocessing"] = start_time
        args_data["start_activity"] = start_shift
        activity.post_process(**args_data)

        activity_log.log_entry(
            name, env.now, amount, None, activity_log.id, core.LogState.STOP
        )
        print(f"after shift amount : {resource_requests}")

        # release the unloader, destination and mover requests
        print(f"keep resources {keep_resources}")
        _release_resource(resource_requests, destination.resource, keep_resources)
        print(f"release destination : {resource_requests}")
        if origin.resource in resource_requests:
            _release_resource(resource_requests, origin.resource, keep_resources)
        print(f"released origin : {resource_requests}")
        if processor.resource in resource_requests:
            _release_resource(resource_requests, processor.resource, keep_resources)
        print(f"released processor : {resource_requests}")
    else:
        raise RuntimeError(
            f"Attempting to shift content from an empty origin or to a full destination. ({all_amounts})"
        )
    print(resource_requests)


def sequential_process(
    activity_log, env, sub_processes, name, requested_resources, keep_resources
):
    """Returns a generator which can be added as a process to a simpy.Environment. In the process the given
    sub_processes will be executed sequentially in the order in which they are given.

    activity_log: the core.Log object in which log_entries about the activities progress will be added.
    env: the simpy.Environment in which the process will be run
    sub_processes: an Iterable of methods which will be called with the activity_log and env parameters and should
                   return a generator which could be added as a process to a simpy.Environment
                   the sub_processes will be executed sequentially, in the order in which they are given
    """
    activity_log.log_entry(
        f"sequential {name}", env.now, -1, None, activity_log.id, core.LogState.START
    )
    for sub_process in sub_processes:
        print(sub_process)
        print(f"keep_resources {keep_resources}")
        if not sub_process.postpone_start:
            raise Exception(
                f"SequentialActivity requires all sub processes to have a postponed start. {sub_process.name} does not have attribute postpone_start."
            )
            # print(
            #    (
            #        f"SequentialActivity requires all sub processes to have a postponed start. {sub_process.name} does not have attribute postpone_start."
            #    )
            # )
        activity_log.log_entry(
            f"sub process {sub_process.name}",
            env.now,
            -1,
            None,
            activity_log.id,
            core.LogState.START,
        )
        sub_process.start()
        yield from sub_process.call_main_proc(activity_log=sub_process, env=env)
        sub_process.end()
        # work around for the event evaluation
        # this delay of 0 time units ensures that the simpy environment gets a chance to evaluate events
        # which will result in triggered but not processed events to be taken care of before further progressing
        # maybe there is a better way of doing it, but his option works for now.
        yield env.timeout(0)
        activity_log.log_entry(
            f"sub process {sub_process.name}",
            env.now,
            -1,
            None,
            activity_log.id,
            core.LogState.STOP,
        )
    activity_log.log_entry(
        f"sequential {name}", env.now, -1, None, activity_log.id, core.LogState.STOP
    )


def move_process(
    activity_log,
    env,
    mover,
    destination,
    name,
    requested_resources,
    keep_resources,
    activity,
    engine_order=1.0,
):
    """Returns a generator which can be added as a process to a simpy.Environment. In the process, a move will be made
    by the mover, moving it to the destination.

    activity_log: the core.Log object in which log_entries about the activities progress will be added.
    env: the simpy.Environment in which the process will be run
    mover: moves from its current position to the destination
           should inherit from core.Movable
    destination: the location the mover will move to
                 should inherit from core.Locatable
    engine_order: optional parameter specifying at what percentage of the maximum speed the mover should sail.
                  for example, engine_order=0.5 corresponds to sailing at 50% of max speed
    """
    message = "move activity {} of {} to {}".format(name, mover.name, destination.name)
    print("Mover_move before mover resource request")
    # if mover.resource not in requested_resources:
    #    with mover.resource.request() as my_mover_turn:
    #        yield my_mover_turn
    yield from _request_resource(requested_resources, mover.resource)
    print("Mover_move after mover resource request")

    start_time = env.now
    args_data = {
        "env": env,
        "mover": mover,
        "origin": mover,
        "destination": destination,
        "engine_order": engine_order,
        "activity_log": activity_log,
        "message": message,
        "activity": activity,
    }
    yield from activity.pre_process(args_data)

    activity_log.log_entry(
        message, env.now, -1, mover.geometry, activity_log.id, core.LogState.START
    )

    start_mover = env.now
    mover.ActivityID = activity_log.id
    yield from mover.move(destination=destination, engine_order=engine_order)
    print("Mover_move after move")

    args_data["start_preprocessing"] = start_time
    args_data["start_activity"] = start_mover
    activity.post_process(**args_data)

    _release_resource(requested_resources, mover.resource, keep_resources)
    activity_log.log_entry(
        message, env.now, -1, mover.geometry, activity_log.id, core.LogState.STOP
    )


def _request_resource(requested_resources, resource):
    """Requests the given resource and yields it.
    """
    if resource not in requested_resources:
        requested_resources[resource] = resource.request()
        yield requested_resources[resource]


def _release_resource(requested_resources, resource, kept_resource=None):
    """Releases the given resource, provided it does not equal the kept_resource parameter.
    Deletes the released resource from the requested_resources dictionary."""
    if kept_resource != None:
        if isinstance(kept_resource, list):
            if resource in [item.resource for item in kept_resource]:
                return
        elif resource == kept_resource.resource or resource == kept_resource:
            return

    if resource in requested_resources.keys():
        resource.release(requested_resources[resource])
        del requested_resources[resource]


def _shift_amount(
    env,
    processor,
    origin,
    desired_level,
    destination,
    ActivityID,
    duration=None,
    rate=None,
    id_="default",
    verbose=False,
):
    print("start _shift_amount")
    """Calls the processor.process method, giving debug print statements when verbose is True."""
    amount = np.abs(origin.container.get_level(id_) - desired_level)
    print(f"amount {amount}")
    # Set ActivityID to processor and mover
    processor.ActivityID = ActivityID
    origin.ActivityID = ActivityID

    print("processor start process")
    # Check if loading or unloading

    yield from processor.process(
        origin, amount, destination, id_=id_, duration=duration, rate=rate
    )
    print("processor end process")

    if verbose:
        org_level = origin.container.get_level(id_)
        dest_level = destination.container.get_level(id_)
        print(f"Processed {amount} of {id_}:")
        print(f"  by:          {processor.name}")
        print(f"  origin        {origin.name}  contains: {org_level} of {id_}")
        print(f"  destination:  {destination.name} contains: {dest_level} of {id_}")


def _move_mover(mover, origin, ActivityID, engine_order=1.0, verbose=False):
    """Calls the mover.move method, giving debug print statements when verbose is True."""
    old_location = mover.geometry

    # Set ActivityID to mover
    mover.ActivityID = ActivityID
    yield from mover.move(origin, engine_order=engine_order)

    if verbose:
        print("Moved:")
        print(
            "  object:      "
            + mover.name
            + " contains: "
            + str(mover.container.get_level())
        )
        print(
            "  from:        "
            + format(old_location.x, "02.5f")
            + " "
            + format(old_location.y, "02.5f")
        )
        print(
            "  to:          "
            + format(mover.geometry.x, "02.5f")
            + " "
            + format(mover.geometry.y, "02.5f")
        )


def single_run_process(
    env,
    registry,
    name,
    origin,
    destination,
    mover,
    loader,
    unloader,
    start_event=None,
    stop_event=[],
    requested_resources={},
):

    if stop_event == []:
        stop_event = [
            {
                "or": [
                    {"type": "container", "concept": origin, "state": "empty"},
                    {"type": "container", "concept": destination, "state": "full"},
                ]
            }
        ]

    single_run = [
        MoveActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            postpone_start=True,
            name=f"{name} sailing empty",
            mover=mover,
            destination=origin,
        ),
        ShiftAmountActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            postpone_start=True,
            phase="loading",
            name=f"{name} loading",
            processor=loader,
            origin=origin,
            destination=mover,
        ),
        MoveActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            postpone_start=True,
            name=f"{name} sailing filled",
            mover=mover,
            destination=destination,
        ),
        ShiftAmountActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            phase="unloading",
            name=f"{name} unloading",
            postpone_start=True,
            processor=unloader,
            origin=mover,
            destination=destination,
        ),
    ]

    activity = SequentialActivity(
        env=env,
        name=f"{name} sequence",
        registry=registry,
        sub_processes=single_run,
        postpone_start=True,
    )

    while_activity = WhileActivity(
        env=env,
        name=name,
        registry=registry,
        sub_process=activity,
        condition_event=stop_event,
        start_event=start_event,
        postpone_start=False,
    )

    return single_run, activity, while_activity
