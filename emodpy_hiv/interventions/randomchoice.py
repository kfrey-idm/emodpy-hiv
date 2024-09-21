from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emodpy_hiv.interventions.utils import set_intervention_properties

from typing import List

def new_diagnostic(
        camp,
        choices,
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
    ):
    """
        Wrapper function to create and return a HIVRandomChoice intervention. 

        Args:
            camp: emod_api.campaign object with schema_path set.
            choices: dict of events:probability, with probs summing up to 1.0
            intervention_name (str): The name of the intervention.
            disqualifying_properties (list of str): A list of IndividualProperty key:value pairs that cause an intervention to be aborted
            new_property_value (str): An optional IndividualProperty key:value pair that will be assigned when the intervention is distributed.
            

        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new
    """
    intervention = s2c.get_class_with_defaults( "HIVRandomChoice", camp.schema_path )
    # We should probably check that choices is correctly formatted.
    choice_names = []
    choice_probabilities = []
    for key, value in choices.items():
        choice_names.append(camp.get_send_trigger(key, old=True))
        choice_probabilities.append(value)
    intervention.Choice_Names = choice_names
    intervention.Choice_Probabilities = choice_probabilities
    set_intervention_properties(intervention,
                                intervention_name=intervention_name,
                                disqualifying_properties=disqualifying_properties,
                                new_property_value=new_property_value)

    return intervention


def new_intervention_event( 
        camp,
        choices,
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
    diag = new_diagnostic( camp, choices, intervention_name=intervention_name,
                           disqualifying_properties=disqualifying_properties,
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

def new_intervention_as_file( camp, start_day, choices, filename=None ):
    camp.add( new_intervention_event( camp, choices, start_day ), first=True )
    if filename is None:
        filename = "HIVRandomChoice.json"
    camp.save( filename )
    return filename
