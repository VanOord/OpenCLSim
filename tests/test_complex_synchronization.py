"""Test package."""
import simpy

import openclsim.model as model

from .test_utils import assert_log


def test_complex_synchronization():
    """Test complex synchronization."""

    simulation_start = 0
    my_env = simpy.Environment(initial_time=simulation_start)
    registry = {}
    keep_resources = {}

    reporting_activity = model.BasicActivity(
        env=my_env,
        name="Reporting activity",
        registry=registry,
        duration=0,
        keep_resources=keep_resources,
    )

    sub_processes = [
        model.BasicActivity(
            env=my_env,
            name="A Basic activity1",
            registry=registry,
            duration=14,
            additional_logs=[reporting_activity],
            keep_resources=keep_resources,
        ),
        model.BasicActivity(
            env=my_env,
            name="A Basic activity2",
            registry=registry,
            duration=10,
            additional_logs=[reporting_activity],
            keep_resources=keep_resources,
        ),
        model.BasicActivity(
            env=my_env,
            name="A Basic activity3",
            registry=registry,
            duration=220,
            additional_logs=[reporting_activity],
            keep_resources=keep_resources,
            start_event=[
                {"type": "activity", "name": "B Basic activity2", "state": "done"}
            ],
        ),
    ]

    sub_processes2 = [
        model.BasicActivity(
            env=my_env,
            name="B Basic activity1",
            registry=registry,
            duration=1,
            additional_logs=[reporting_activity],
            keep_resources=keep_resources,
        ),
        model.BasicActivity(
            env=my_env,
            name="B Basic activity2",
            registry=registry,
            duration=500,
            additional_logs=[reporting_activity],
            keep_resources=keep_resources,
        ),
        model.BasicActivity(
            env=my_env,
            name="B Basic activity3",
            registry=registry,
            duration=120,
            additional_logs=[reporting_activity],
            keep_resources=keep_resources,
        ),
    ]

    B = model.SequentialActivity(
        env=my_env,
        name="B Sequential process",
        registry=registry,
        sub_processes=sub_processes2,
        keep_resources=keep_resources,
    )

    A = model.SequentialActivity(
        env=my_env,
        name="A Sequential process",
        registry=registry,
        sub_processes=sub_processes,
        keep_resources=keep_resources,
    )

    model.register_processes([A, B, reporting_activity])
    my_env.run()

    assert my_env.now == 721
    assert_log(reporting_activity)
    assert_log(A)
    assert_log(B)
