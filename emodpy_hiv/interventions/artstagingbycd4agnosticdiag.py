from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from . import utils as hiv_utils
from emodpy_hiv.interventions.utils import set_intervention_properties

from typing import List


def new_diagnostic(
        camp,
        Positive_Event,
        Negative_Event,
        abp_tvmap,
        abt_tvmap,
        abw_tvmap,
        cua_tvmap,
        cbt_tvmap,
        cbw_tvmap,
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
    ):
    """
        Wrapper function to create and return a HIVARTStagingCD4AgnosticDiagnostic intervention. 

        Args:
            camp: emod_api.campaign object with schema_path set.
            

        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new
    """
    intervention = s2c.get_class_with_defaults( "HIVARTStagingCD4AgnosticDiagnostic", camp.schema_path ) 
    intervention.Positive_Diagnosis_Event = camp.get_send_trigger( Positive_Event, True )
    intervention.Negative_Diagnosis_Event = camp.get_send_trigger( Negative_Event, True )

    hiv_utils.set_tvmap_lists_from_map( abp_tvmap, intervention.Adult_By_Pregnant )
    hiv_utils.set_tvmap_lists_from_map( abt_tvmap, intervention.Adult_By_TB )
    hiv_utils.set_tvmap_lists_from_map( abw_tvmap, intervention.Adult_By_WHO_Stage )
    hiv_utils.set_tvmap_lists_from_map( cua_tvmap, intervention.Child_Treat_Under_Age_In_Years_Threshold )
    hiv_utils.set_tvmap_lists_from_map( cbt_tvmap, intervention.Child_By_TB )
    hiv_utils.set_tvmap_lists_from_map( cbw_tvmap, intervention.Child_By_WHO_Stage )
    set_intervention_properties(intervention,
                                intervention_name=intervention_name,
                                disqualifying_properties=disqualifying_properties,
                                new_property_value=new_property_value)
    return intervention


def new_intervention_event( 
        camp,
        pos_event,
        neg_event,
        abp_tvmap,
        abt_tvmap,
        abw_tvmap,
        cua_tvmap,
        cbt_tvmap,
        cbw_tvmap,
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
    diag = new_diagnostic( camp, pos_event, neg_event, abp_tvmap, abt_tvmap, abw_tvmap, cua_tvmap, cbt_tvmap, cbw_tvmap,
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
    hiv_utils.declutter( event )

    return event

def new_intervention_as_file( camp, start_day, filename=None ):
    import emod_api.campaign as camp
    camp.add( new_intervention_event( camp, "HIVTestedPositive", "HIVTestedNegative", { 1972: 0.44 }, { 1972: 0.44 }, { 1972: 0.44 }, { 1972: 0.44 }, { 1972: 0.44 }, { 1972: 0.44 }, start_day =start_day ), first=True )
    if filename is None:
        filename = "HIVARTStagingCD4AgnosticDiagnostic.json"
    camp.save( filename )
    return filename
