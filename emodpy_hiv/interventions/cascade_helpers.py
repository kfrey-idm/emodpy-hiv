import emod_api.campaign as camp
import emodpy_hiv.interventions.outbreak as ob 
import emod_api.interventions.common as comm
import emod_api.interventions.utils as utils
from emodpy_hiv import *

def reset( camp ):
    """
        Utility function to clear out the campaign object, mostly useful to test. This function is not auto-imported
        with the module like the rest of the functions in this submodule. Caller has to explicitly import 
        emodpy_hiv.interventions.cascade_helpers.
        Args:
            camp: emod_api.campaign object.
        Returns:
            None.
    """
    del( camp.campaign_dict["Events"][:] )

def seed_infection( camp, timestep, coverage ):
    """
        Seed an infection by time and %age of population infected.
    """
    event = ob.new_intervention( timestep=timestep, camp=camp, coverage=coverage )
    # have to be careful with having first in a wrapped function. This removes all other events.
    camp.add( event )

def add_triggered_event( camp, in_trigger, out_iv, coverage=1.0, target_sex="All", target_risk="", event_name="" ):
    """
    An alias for triggered_event_common. Naming things well is hard.
    """
    return triggered_event_common( camp, in_trigger, out_iv, coverage, target_sex, target_risk, event_name )

def triggered_event_common( camp, in_trigger, out_iv, coverage=1.0, target_sex="All", target_risk="", event_name="" ):
    """
        Parameterized utility function used by rest of functions in this submodule that listen for a trigger
        and distribute an intervention (or list thereof) as a result.
    """
    out_ivs = list()
    if isinstance( out_iv, list ):
        out_ivs = out_iv
    else:
        out_ivs.append( out_iv )
    event = comm.TriggeredCampaignEvent( camp, Start_Day=1, Event_Name=event_name, Nodeset_Config=utils.do_nodes(camp.schema_path, node_ids=[]), Triggers=[in_trigger], Intervention_List=out_ivs, Demographic_Coverage=coverage, Target_Gender=target_sex, Property_Restrictions=target_risk )
    event.Event_Coordinator_Config.pop( "Targeting_Config" )
    event.Event_Coordinator_Config.Intervention_Config.pop( "Targeting_Config" )
    camp.add( event )

def add_choice( camp, sympto_signal="HIVSymptomatic", get_tested_signal="GetTested" ):
    """
        Listen for HIVSymptomatic trigger. Then toss a coin (Random Choice), heads get tested, tails maybe it's just a cold.
    """
    actual_iv = random.new_diagnostic( camp, choices={ get_tested_signal: 0.5, "Ignore": 0.5 } )
    triggered_event_common( camp, in_trigger=sympto_signal, out_iv=actual_iv, event_name="Decide_On_Testing" )
 
def add_test( camp, get_tested_signal="GetTested" ):
    """
        Listen for GetTested signal. Then get HIV RapidDiagnostic test after a delay of 30 days.
    """
    actual_iv = rapiddiag.new_diagnostic( camp, Positive_Event="HIVPositiveTest", Negative_Event="HIVNegativeTest" )
    delayed_iv = comm.DelayedIntervention( camp, [ actual_iv ], Delay_Dict={ "Delay_Period": 30 } )
    triggered_event_common( camp, get_tested_signal, delayed_iv, event_name="Test" )

def trigger_art_from_pos_test( camp, input_signal="HIVPositiveTest", output_signal="StartTreatment", lag_time=30 ):
    """
        Listen for HIVPositiveTest trigger. Then Trigger ART. Note that Trigger ART isn't same as starting it.
    """
    actual_iv = comm.BroadcastEvent( camp, output_signal )
    delayed_iv = comm.DelayedIntervention( camp, [ actual_iv ], Delay_Dict={ "Delay_Period": lag_time } )
    triggered_event_common( camp, input_signal, delayed_iv, event_name="NeedTreatment" )

def add_art_from_trigger( camp, signal="StartTreatment" ):
    """
        Actually distribute ART if a StartTreatment signal/trigger is observed. Broadcast a StartedART signal synchronously.
    """
    actual_iv = art.new_intervention(camp)
    triggered_event_common( camp, signal, [ actual_iv ], event_name="ART on trigger" )

def trigger_art( camp, timestep, coverage, trigger="StartTreatment" ):
    """
        Schedule a broadcast of StartTreatment (or equivalent), not based on any observed signals.
    """
    trigger_event = comm.ScheduledCampaignEvent( camp, Start_Day=timestep, Demographic_Coverage=coverage, Event_Name="ART trigger", Nodeset_Config=utils.do_nodes(camp.schema_path, node_ids=[]), Intervention_List=[ comm.BroadcastEvent( camp, trigger ) ] )
    trigger_event.Event_Coordinator_Config.pop( "Targeting_Config" )
    camp.add( trigger_event )

