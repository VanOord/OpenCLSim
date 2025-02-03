import shapely.geometry
import simpy

import openclsim.core as core
import openclsim.model as model

from .test_utils import assert_log

def test_produce_amount():
    """Test the shift amount activity."""

    simulation_start = 0
    my_env = simpy.Environment(initial_time=simulation_start)
    registry = {}

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
        core.ContainerDependentMovable, 
        core.HasResource,
        core.Processor_wid,
        core.Identifiable,
        core.Log,
    ),
    {},
    )

    location_from_site = shapely.geometry.Point(4.057883, 51.947782)

    from_site = Site(
    env=my_env,
    name=from_site,
    geometry=location_from_site,    
    capacity=150000,
    level=150000,
    )

    vessel01 = TransportProcessingResource(
    env=my_env,
    name=vessel01,
    geometry=location_from_site,  
    capacity=1740,
    compute_v=lambda x: 10
    )

    activity = model.ProduceAmountActivity(
        env=my_env,
        name="Transfer MP",
        registry=registry,
        processor=vessel01,
        origin=from_site,
        destination=vessel01,
        amount=100,
        duration=10,
    )

    model.register_processes([activity])
    my_env.run()

    assert my_env.now == 10
    assert_log(from_site)
    assert_log(vessel01)
    assert_log(activity)