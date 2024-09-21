from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
import json

def new_diagnostic(
        camp,
        Positive_Event,
        Base_Sensitivity=1,
        Base_Specificity=1,
        Days_To_Diagnosis=0,
        Treatment_Fraction=1
    ):
    """
        Wrapper function to create and return a HIVDrawBlood intervention. 

        Args:
            camp: emod_api.campaign object with schema_path set.
            

        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new
    """
    intervention = s2c.get_class_with_defaults( "HIVDrawBlood", camp.schema_path )
    intervention.Base_Sensitivity = Base_Sensitivity 
    intervention.Base_Specificity = Base_Specificity 
    intervention.Positive_Diagnosis_Event = camp.get_event( Positive_Event, True )
    # Schema is wrong here due to convenient inheritance. No choice but to hardcode this special knowledge
    intervention.pop( "Negative_Diagnosis_Event" )

    return intervention


def new_intervention_event( 
        camp,
        pos_event,
        start_day=1, 
        coverage=1.0, 
        node_ids=None
    ):
    """
    Diagnostic as scheduled event.
    """
    diag = new_diagnostic( camp, pos_event )

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
    camp.add( new_intervention_event( camp, pos_event="HIVTestedPositive", start_day =start_day ), first=True )
    if filename is None:
        filename = "HIVDrawBlood.json"
    camp.save( filename )
    return filename
