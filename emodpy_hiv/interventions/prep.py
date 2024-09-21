from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emodpy_hiv.interventions.utils import set_intervention_properties

from typing import List


def _validate_times_and_values( times, values ):
    if len( times ) != len( values ):
        raise ValueError( f"Length of times array ({times}) doesn't match length of values array ({values})." )

    if any(t < 0 for t in times):
        raise ValueError(f"All time values ({times}) must be greater than 0")
    
    if times != sorted(times):
        raise ValueError(f"Time values ({times}) must be in ascending order")
    
    if any(v < 0 or v > 1 for v in values):
        raise ValueError(f"All values ({values}) must be between 0 and 1")
    

def new_intervention(
        camp,
        efficacy_times=[0,365],
        efficacy_values=[0.5,0],
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
    ):
    """
    Create a new PrEP (Pre-Exposure Prophylaxis) intervention.

    This function creates and configures a new PrEP intervention using the provided efficacy times and values.

    Args:
        camp (emod_api.campaign): The central campaign builder object.
        efficacy_times (list of float): A list of times at which the PrEP efficacy changes. Times must be > 0 and in ascending order.
        efficacy_values (list of float): A list of efficacy values corresponding to the times. Values must be between 0 and 1.
        intervention_name (str): The name of the intervention.
        disqualifying_properties (list of str): A list of IndividualProperty key:value pairs that cause an intervention to be aborted
        new_property_value (str): An optional IndividualProperty key:value pair that will be assigned when the intervention is distributed.

    Returns:
        A new PrEP intervention with the specified efficacy configuration, which can be passed to a scheduled or triggered campaign event function.

    Raises:
        ValueError: If the lengths of efficacy_times and efficacy_values do not match.
        ValueError: If any time value in efficacy_times is not greater than 0.
        ValueError: If the time values in efficacy_times are not in ascending order.
        ValueError: If any value in efficacy_values is not between 0 and 1.

    Example:

    .. code-block:: python

        camp.set_schema("path/to/schema.json")
        times = [1, 2, 3, 4, 5, 6, 7]
        values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        intervention = new_intervention(camp, times, values)

    """

    _validate_times_and_values( efficacy_times, efficacy_values )

    intervention = s2c.get_class_with_defaults( "ControlledVaccine", camp.schema_path )
    waning = s2c.get_class_with_defaults( "WaningEffectMapPiecewise", camp.schema_path )
    waning.Durability_Map.Times = efficacy_times
    waning.Durability_Map.Values = efficacy_values
    waning.Initial_Effect = waning.Durability_Map.Values[0]
    intervention.Waning_Config = waning
    set_intervention_properties(intervention,
                                intervention_name=intervention_name,
                                disqualifying_properties=disqualifying_properties,
                                new_property_value=new_property_value)

    return intervention

def new_intervention_event( 
        camp, 
        efficacy_times=[0,365],
        efficacy_values=[0.5,0],
        start_day=1, 
        coverage=1.0, 
        node_ids=None,
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
    ):
    """
    Create a new PrEP (Pre-Exposure Prophylaxis) intervention as complete (scheduled) event.

    This function creates and configures a new PrEP intervention using the provided efficacy times and values, and adds it to a scheduled event. You need to add it to the campaign.

    Args:
        camp (emod_api.campaign): The central campaign builder object.
        efficacy_times (list of float): A list of times at which the PrEP efficacy changes. Times must be > 0 and in ascending order.
        efficacy_values (list of float): A list of efficacy values corresponding to the times. Values must be between 0 and 1.
        start_day (int): When this campaign event should occur.
        coverage (float): Who should get this -- i.e., what percentage of the population.
        node_ids (list of integers): Where this campaign event should be distributed. Leave as default if 'everywhere'.
        intervention_name (str): The name of the intervention.
        disqualifying_properties (list of str): A list of IndividualProperty key:value pairs that cause an intervention to be aborted
        new_property_value (str): An optional IndividualProperty key:value pair that will be assigned when the intervention is distributed.

    Returns:
        A new PrEP intervention with the specified efficacy configuration, which can be passed to a scheduled or triggered campaign event function.

    Raises:
        ValueError: If the lengths of efficacy_times and efficacy_values do not match.
        ValueError: If any time value in efficacy_times is not greater than 0.
        ValueError: If the time values in efficacy_times are not in ascending order.
        ValueError: If any value in efficacy_values is not between 0 and 1.

    Example:

    .. code-block:: python

        camp.set_schema("path/to/schema.json")
        times = [1, 2, 3, 4, 5, 6, 7]
        values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        event = new_intervention_event(camp, times, values, start_day=730, coverage=0.33, node_ides[ 1, 4, 5 ])
    
    """
    new_iv = new_intervention( camp, efficacy_times, efficacy_values, intervention_name=intervention_name,
                                disqualifying_properties=disqualifying_properties,
                                new_property_value=new_property_value)

    # Coordinator
    coordinator = s2c.get_class_with_defaults( "StandardEventCoordinator", camp.schema_path )
    coordinator.Intervention_Config = new_iv
    coordinator.Demographic_Coverage = coverage

    # Event
    event = s2c.get_class_with_defaults( "CampaignEvent", camp.schema_path ) 
    event.Event_Coordinator_Config = coordinator
    event.Start_Day = float(start_day)
    event.Nodeset_Config = utils.do_nodes( camp.schema_path, node_ids )
    from . import utils as hiv_utils
    hiv_utils.declutter( event )

    return event

def new_intervention_as_file( camp, start_day, filename=None ):
    import emod_api.campaign as camp
    camp.add( new_intervention_event( camp, efficacy_times=[0, 365], efficacy_values=[0.8, 0.9], start_day=start_day ), first=True )
    if filename is None:
        filename = "PrEP.json"
    camp.save( filename )
    return filename
