from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
import json

def new_diagnostic(
        camp,
        choices
    ):
    """
        Wrapper function to create and return a HIVRandomChoice intervention. 

        Args:
            camp: emod_api.campaign object with schema_path set.
            choices: dict of events:probability, with probs summing up to 1.0
            

        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new
    """
    intervention = s2c.get_class_with_defaults( "HIVRandomChoice", camp.schema_path )
    # We should probably check that choices is correctly formatted. 
    e2p = s2c.get_class_with_defaults( "idmType:Event2ProbabilityType", camp.schema_path )
    new_choices = {}
    for key, value in choices.items():
        e2p.Event = camp.get_event( key, old=True )
        e2p.Probability = value 
        new_choices.update( { key: value } )
    intervention.Choices = new_choices

    return intervention


def new_intervention_event( 
        camp,
        choices,
        start_day=1, 
        coverage=1.0, 
        node_ids=None
    ):
    """
    Diagnostic as scheduled event.
    """
    diag = new_diagnostic( camp, choices )

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

def new_intervention_as_file( camp, start_day, choices, filename=None ):
    camp.add( new_intervention_event( camp, choices, start_day ), first=True )
    if filename is None:
        filename = "HIVRandomChoice.json"
    camp.save( filename )
    return filename
