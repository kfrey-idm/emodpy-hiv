from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
import json

def new_delay(
        camp,
        Bcast_Event,
        Expire_Event="",
        Coverage=1,
        Delay=1,
        Shelf_Life=36500,
        Name=""
    ):
    """
        Wrapper function to create and return a HIVDelayedIntervention intervention. 

        Args:
            camp: emod_api.campaign object with schema_path set.
            

        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new
    """
    intervention = s2c.get_class_with_defaults( "HIVDelayedIntervention", camp.schema_path )
    intervention.Broadcast_Event = Bcast_Event 
    intervention.Broadcast_On_Expiration_Event =  Expire_Event
    intervention.Coverage = Coverage
    intervention.Delay_Period = Delay
    intervention.Expiration_Period = Shelf_Life
    if Name=="":
        Name = "HIVDelayedIntervention"
    intervention.Intervention_Name = Name
    intervention.Dont_Allow_Duplicates = 1

    return intervention


def new_intervention_event( 
        camp,
        bcast_event,
        expire_event="",
        coverage=1,
        delay=1,
        shelf_life=0
    ):
    """
    Delay as scheduled event.
    """
    diag = new_delay( camp, bcast_event, expire_event, coverage, delay, shelf_life )

    # Coordinator
    coordinator = s2c.get_class_with_defaults( "StandardEventCoordinator", camp.schema_path )
    coordinator.Intervention_Config = diag
    coordinator.Demographic_Coverage = coverage

    # Event
    event = s2c.get_class_with_defaults( "CampaignEvent", camp.schema_path ) 
    event.Event_Coordinator_Config = coordinator
    event.Start_Day = 1 # float(start_day)
    event.Nodeset_Config = utils.do_nodes( camp.schema_path, [] )
    from . import utils as hiv_utils
    hiv_utils.declutter( event )

    return event

def new_intervention_as_file( camp, start_day, filename=None ):
    import emod_api.campaign as camp
    camp.add( new_intervention_event( camp, bcast_event="HIVTestedPositive" ), first=True )
    if filename is None:
        filename = "HIVDelayedIntervention.json"
    camp.save( filename )
    return filename
