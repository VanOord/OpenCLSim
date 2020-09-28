"""Test package."""
import datetime

import shapely.geometry
import simpy

import openclsim.core as core
import openclsim.model as model

from .test_utils import parse_log


def test_wraped_single_run():
    """Test wraped single run."""
    # setup environment
    simulation_start = 0
    my_env = simpy.Environment(initial_time=simulation_start)

    Site = type(
        "Site",
        (
            core.Identifiable,
            core.Log,
            core.Locatable,
            core.HasContainer,
            core.HasResource,
        ),
        {},
    )

    TransportProcessingResource = type(
        "TransportProcessingResource",
        (
            core.Identifiable,
            core.Log,
            core.ContainerDependentMovable,
            core.Processor,
            core.LoadingFunction,
            core.UnloadingFunction,
            core.HasResource,
        ),
        {},
    )

    location_from_site = shapely.geometry.Point(4.18055556, 52.18664444)  # lon, lat
    location_to_site = shapely.geometry.Point(4.25222222, 52.11428333)  # lon, lat

    data_from_site = {
        "env": my_env,
        "name": "Winlocatie",
        "geometry": location_from_site,
        "capacity": 5_000,
        "level": 5_000,
    }

    data_to_site = {
        "env": my_env,
        "name": "Dumplocatie",
        "geometry": location_to_site,
        "capacity": 5_000,
        "level": 0,
    }

    from_site = Site(**data_from_site)
    to_site = Site(**data_to_site)

    data_hopper = {
        "env": my_env,
        "name": "Hopper 01",
        "geometry": location_from_site,
        "capacity": 1000,
        "compute_v": lambda x: 10 + 2 * x,
        "loading_rate": 1,
        "unloading_rate": 5,
    }

    hopper = TransportProcessingResource(**data_hopper)

    single_run, activity, while_activity = model.single_run_process(
        name="single_run",
        registry={},
        env=my_env,
        origin=from_site,
        destination=to_site,
        mover=hopper,
        loader=hopper,
        unloader=hopper,
    )

    my_env.run()

    hopper_log = {
        "Message": [
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "move activity single_run sailing empty of Hopper 01 to Winlocatie",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "move activity single_run sailing filled of Hopper 01 to Dumplocatie",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
        ],
        "Timestamp": [
            datetime.datetime(1970, 1, 1, 0, 0),
            datetime.datetime(1970, 1, 1, 0, 0),
            datetime.datetime(1970, 1, 1, 0, 0),
            datetime.datetime(1970, 1, 1, 0, 0),
            datetime.datetime(1970, 1, 1, 0, 16, 40),
            datetime.datetime(1970, 1, 1, 0, 16, 40),
            datetime.datetime(1970, 1, 1, 0, 16, 40),
            datetime.datetime(1970, 1, 1, 0, 29, 45, 687159),
            datetime.datetime(1970, 1, 1, 0, 29, 45, 687159),
            datetime.datetime(1970, 1, 1, 0, 29, 45, 687159),
            datetime.datetime(1970, 1, 1, 0, 33, 5, 687159),
            datetime.datetime(1970, 1, 1, 0, 33, 5, 687159),
            datetime.datetime(1970, 1, 1, 0, 33, 5, 687159),
            datetime.datetime(1970, 1, 1, 0, 48, 48, 511751),
            datetime.datetime(1970, 1, 1, 0, 48, 48, 511751),
            datetime.datetime(1970, 1, 1, 0, 48, 48, 511751),
            datetime.datetime(1970, 1, 1, 1, 5, 28, 511751),
            datetime.datetime(1970, 1, 1, 1, 5, 28, 511751),
            datetime.datetime(1970, 1, 1, 1, 5, 28, 511751),
            datetime.datetime(1970, 1, 1, 1, 18, 34, 198910),
            datetime.datetime(1970, 1, 1, 1, 18, 34, 198910),
            datetime.datetime(1970, 1, 1, 1, 18, 34, 198910),
            datetime.datetime(1970, 1, 1, 1, 21, 54, 198910),
            datetime.datetime(1970, 1, 1, 1, 21, 54, 198910),
            datetime.datetime(1970, 1, 1, 1, 21, 54, 198910),
            datetime.datetime(1970, 1, 1, 1, 37, 37, 23501),
            datetime.datetime(1970, 1, 1, 1, 37, 37, 23501),
            datetime.datetime(1970, 1, 1, 1, 37, 37, 23501),
            datetime.datetime(1970, 1, 1, 1, 54, 17, 23501),
            datetime.datetime(1970, 1, 1, 1, 54, 17, 23501),
            datetime.datetime(1970, 1, 1, 1, 54, 17, 23501),
            datetime.datetime(1970, 1, 1, 2, 7, 22, 710661),
            datetime.datetime(1970, 1, 1, 2, 7, 22, 710661),
            datetime.datetime(1970, 1, 1, 2, 7, 22, 710661),
            datetime.datetime(1970, 1, 1, 2, 10, 42, 710661),
            datetime.datetime(1970, 1, 1, 2, 10, 42, 710661),
            datetime.datetime(1970, 1, 1, 2, 10, 42, 710661),
            datetime.datetime(1970, 1, 1, 2, 26, 25, 535252),
            datetime.datetime(1970, 1, 1, 2, 26, 25, 535252),
            datetime.datetime(1970, 1, 1, 2, 26, 25, 535252),
            datetime.datetime(1970, 1, 1, 2, 43, 5, 535252),
            datetime.datetime(1970, 1, 1, 2, 43, 5, 535252),
            datetime.datetime(1970, 1, 1, 2, 43, 5, 535252),
            datetime.datetime(1970, 1, 1, 2, 56, 11, 222411),
            datetime.datetime(1970, 1, 1, 2, 56, 11, 222411),
            datetime.datetime(1970, 1, 1, 2, 56, 11, 222411),
            datetime.datetime(1970, 1, 1, 2, 59, 31, 222411),
            datetime.datetime(1970, 1, 1, 2, 59, 31, 222411),
            datetime.datetime(1970, 1, 1, 2, 59, 31, 222411),
            datetime.datetime(1970, 1, 1, 3, 15, 14, 47003),
            datetime.datetime(1970, 1, 1, 3, 15, 14, 47003),
            datetime.datetime(1970, 1, 1, 3, 15, 14, 47003),
            datetime.datetime(1970, 1, 1, 3, 31, 54, 47003),
            datetime.datetime(1970, 1, 1, 3, 31, 54, 47003),
            datetime.datetime(1970, 1, 1, 3, 31, 54, 47003),
            datetime.datetime(1970, 1, 1, 3, 44, 59, 734162),
            datetime.datetime(1970, 1, 1, 3, 44, 59, 734162),
            datetime.datetime(1970, 1, 1, 3, 44, 59, 734162),
            datetime.datetime(1970, 1, 1, 3, 48, 19, 734162),
            datetime.datetime(1970, 1, 1, 3, 48, 19, 734162),
        ],
        "Value": [
            0.0,
            0.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            0.0,
            0.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            0.0,
            0.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            0.0,
            0.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            0.0,
            0.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
        ],
        "Geometry": [
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
        ],
        "ActivityState": [
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
            "START",
            "STOP",
            "START",
            "START",
            "STOP",
            "STOP",
        ],
    }

    from_site_log = {
        "Message": [
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
            "Shift amount activity single_run loading transfer default from Winlocatie to Hopper 01 with Hopper 01",
        ],
        "Timestamp": [
            datetime.datetime(1970, 1, 1, 0, 0),
            datetime.datetime(1970, 1, 1, 0, 16, 40),
            datetime.datetime(1970, 1, 1, 0, 48, 48, 511751),
            datetime.datetime(1970, 1, 1, 1, 5, 28, 511751),
            datetime.datetime(1970, 1, 1, 1, 37, 37, 23501),
            datetime.datetime(1970, 1, 1, 1, 54, 17, 23501),
            datetime.datetime(1970, 1, 1, 2, 26, 25, 535252),
            datetime.datetime(1970, 1, 1, 2, 43, 5, 535252),
            datetime.datetime(1970, 1, 1, 3, 15, 14, 47003),
            datetime.datetime(1970, 1, 1, 3, 31, 54, 47003),
        ],
        "Value": [
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
        ],
        "Geometry": [
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
            (4.18055556, 52.18664444),
        ],
        "ActivityState": [
            "START",
            "STOP",
            "START",
            "STOP",
            "START",
            "STOP",
            "START",
            "STOP",
            "START",
            "STOP",
        ],
    }

    to_site_log = {
        "Message": [
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
            "Shift amount activity single_run unloading transfer default from Hopper 01 to Dumplocatie with Hopper 01",
        ],
        "Timestamp": [
            datetime.datetime(1970, 1, 1, 0, 29, 45, 687159),
            datetime.datetime(1970, 1, 1, 0, 33, 5, 687159),
            datetime.datetime(1970, 1, 1, 1, 18, 34, 198910),
            datetime.datetime(1970, 1, 1, 1, 21, 54, 198910),
            datetime.datetime(1970, 1, 1, 2, 7, 22, 710661),
            datetime.datetime(1970, 1, 1, 2, 10, 42, 710661),
            datetime.datetime(1970, 1, 1, 2, 56, 11, 222411),
            datetime.datetime(1970, 1, 1, 2, 59, 31, 222411),
            datetime.datetime(1970, 1, 1, 3, 44, 59, 734162),
            datetime.datetime(1970, 1, 1, 3, 48, 19, 734162),
        ],
        "Value": [
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
            1000.0,
        ],
        "Geometry": [
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
            (4.25222222, 52.11428333),
        ],
        "ActivityState": [
            "START",
            "STOP",
            "START",
            "STOP",
            "START",
            "STOP",
            "START",
            "STOP",
            "START",
            "STOP",
        ],
    }

    del hopper.log["ActivityID"]
    del from_site.log["ActivityID"]
    del to_site.log["ActivityID"]

    assert parse_log(hopper.log) == hopper_log
    assert parse_log(from_site.log) == from_site_log
    assert parse_log(to_site.log) == to_site_log
