from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from . import utils as hiv_utils
from emodpy_hiv.interventions.utils import set_intervention_properties

from typing import List

def new_diagnostic(
        camp,
        Positive_Event,
        Negative_Event,
        Threshold_TVMap,
        IP_TVMap,
        IAT_TVMap,
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
    ):
    """
        Wrapper function to create and return a HIVARTStagingByCD4Diagnostic intervention. 

        Args:
            camp: emod_api.campaign object with schema_path set.
            

        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new
    """
    intervention = s2c.get_class_with_defaults( "HIVARTStagingByCD4Diagnostic", camp.schema_path )
    intervention.Positive_Diagnosis_Event = camp.get_send_trigger( Positive_Event, True )
    intervention.Negative_Diagnosis_Event = camp.get_send_trigger( Negative_Event, True )

    hiv_utils.set_tvmap_lists_from_map( IP_TVMap, intervention.If_Pregnant )
    hiv_utils.set_tvmap_lists_from_map( IAT_TVMap, intervention.If_Active_TB )
    hiv_utils.set_tvmap_lists_from_map( Threshold_TVMap, intervention.Threshold )

    set_intervention_properties(intervention,
                                intervention_name=intervention_name,
                                disqualifying_properties=disqualifying_properties,
                                new_property_value=new_property_value)

    return intervention


def new_intervention_event( 
        camp,
        pos_event,
        neg_event,
        thresh_tvmap,
        pregnant_tvmap,
        tb_tvmap,
        start_day=1, 
        coverage=1.0, 
        node_ids=None,
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
    ):
    """
    Diagnostic as scheduled event.
    """
    diag = new_diagnostic( camp, pos_event, neg_event, thresh_tvmap, pregnant_tvmap, tb_tvmap,
                           intervention_name=intervention_name, disqualifying_properties=disqualifying_properties,
                           new_property_value=new_property_value)

    # Coordinator
    coordinator = s2c.get_class_with_defaults( "StandardEventCoordinator", camp.schema_path )
    coordinator.Intervention_Config = diag
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
    camp.add( new_intervention_event( camp, pos_event="HIVTestedPositive", neg_event="HIVTestedNegative", thresh_tvmap={}, pregnant_tvmap={}, tb_tvmap={}, start_day =start_day ), first=True )
    if filename is None:
        filename = "HIVARTStagingByCD4Diagnostic.json"
    camp.save( filename )
    return filename
