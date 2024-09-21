from emod_api import schema_to_class as s2c
from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emod_api.interventions import common as comm
from . import utils as hiv_utils
import json

    
def DistributeIVByRefTrack(
        camp,
        Start_Day,
        Intervention,
        TVMap,
        node_ids=None,
        Event_Name="Scheduled_Campaign_Event",
        Property_Restrictions=None,
        Target_Age_Min=0,
        Target_Age_Max=125*365,
        Target_Gender="All",
        Update_Period=None,
        IV_Tracking_Name=None,
        Target_Disease_State=None):

    """
    Wrapper function to create and return a ScheduledCampaignEvent intervention.
    The alternative to a ScheduledCampaignEvent is a TriggeredCampaignEvent.

    Args:
        camp: emod_api.campaign object with schema_path set.
        Start_Day: When to start.
        Intervention: Valid intervention to be distributed together as necessary to track coverage targets. Can be single intervention or list (list is useful where you want a co-event). If list, actual intervention should be first.
        Event_Name: Name for overall campaign event, of not functional meaning.
        node_ids: Nodes to target with this intervention, return from utils.do_nodes().
        Property_Restrictions: Individual Properties a person must have to receive the intervention(s).
        Number_Repetitions: N/A
        Timesteps_Between_Repetitions: N/A
        Target_Demographic: Everyone, ExplicitAgeRanges, etc.
        Target_Age_Min: Minimum age (in years).
        Target_Age_Max: Maximum age (in years).
        Target_Gender: All, Male, or Female.
        Update_Period: Number representing how frequently the distributions are done.
        IV_Tracking_Name: Optional string parameter to distinguish one intervention from another if you're doing multiple campaigns with the same underlying intervention.
        Target_Disease_State: Optional string parameter to specify the disease state to target with this
            intervention. Default to None which means Everyone. Possible values are: "Everyone", "HIV_Positive",
            "HIV_Negative", "Tested_Positive", "Tested_Negative", "Not_Tested_Or_Tested_Negative".

    Returns:
        ReadOnlyDict: Schema-based smart dictionary representing a new
        ScheduledCampaignEvent intervention ready to be added to a campaign.

    """
    global schema_path
    schema_path = ( camp.schema_path if camp is not None else schema_path )

    event = s2c.get_class_with_defaults( "CampaignEvent", schema_path )
    coordinator = s2c.get_class_with_defaults( "ReferenceTrackingEventCoordinatorHIV", schema_path )

    # Second, hook them up
    event.Event_Coordinator_Config = coordinator
    event.Start_Day = float(Start_Day)

    # Intervention can be single or list. If list, we bundle into a M.I.D.
    if IV_Tracking_Name is not None:
        if type(Intervention) is list:
            Intervention[0]["Intervention_Name"] = IV_Tracking_Name 
        else:
            Intervention["Intervention_Name"] = IV_Tracking_Name

    if type(Intervention) is list:
        mid = comm.MultiInterventionDistributor( camp, Intervention )
        Intervention = mid
    coordinator.Intervention_Config = Intervention 
    prs = utils._convert_prs( Property_Restrictions )
    if len(prs)>0 and type(prs[0]) is dict:
        coordinator.Property_Restrictions_Within_Node = prs
        coordinator.pop( "Property_Restrictions" )
    else:
        coordinator.Property_Restrictions = prs
        coordinator.pop( "Property_Restrictions_Within_Node" )
    
    if Target_Age_Min > 0 or Target_Age_Max < 125*365:
        coordinator.Target_Age_Min = Target_Age_Min 
        coordinator.Target_Age_Max = Target_Age_Max
    if Target_Gender != "All":
        coordinator.Target_Gender = Target_Gender 
        coordinator.Target_Demographic = "ExplicitAgeRangesAndGender"

    hiv_utils.set_tvmap_lists_from_map( TVMap, coordinator.Time_Value_Map )

    if Update_Period is not None:
        coordinator.Update_Period = Update_Period

    if Target_Disease_State is not None:
        coordinator.Target_Disease_State = Target_Disease_State

    event.Nodeset_Config = utils.do_nodes( camp.schema_path, node_ids )
    hiv_utils.declutter( event )

    return event

def new_intervention_as_file( camp, actual_intervention, start_day=1, filename=None ):
    import emod_api.campaign as camp
    camp.add( DistributeIVByRefTrack( camp, start_day, actual_intervention, { 0: 0, 365: 1, 730: 0 }  ), first=True )
    if filename is None:
        filename = "RefTracker.json"
    camp.save( filename )
    return filename

