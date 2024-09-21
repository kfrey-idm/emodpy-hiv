from typing import List

import emod_api.campaign as camp
import emodpy_hiv.interventions.outbreak as ob 
import emodpy_hiv.interventions.reftracker as rt
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


# TODO: need to decide: use kwargs or custom pass-through params that go to TriggerdCampaignEvent (e.g. target_age_max)
def triggered_event_common(camp, in_trigger, out_iv, coverage=1.0, target_sex="All",
                           property_restrictions: List[str] = None, event_name="", node_ids: List[int] = None,
                           start_day: int = 1, target_age_min: float = 0, target_age_max: float = 365*200, delay: float = None):
    """
        Parameterized utility function used by rest of functions in this submodule; listens for a trigger (signal)
        and distributes an intervention (or list thereof) as a result, based on coverage and targeting. 

        Args: 
            camp: The central campaign accumulator, from emod_api.campaign.  
            in_trigger: The trigger aka signal for the event. E.g., "NewInfection"
            out_iv: The output intervention of the event.  
            coverage (float): The coverage of the event (default is 1.0).  
            target_sex (str): The target sex for the event (default is "All").  
            property_restrictions (list[str]): A list of IP restrictions in "Risk:HIGH" format.
                None means no restrictions.
            event_name (str): The name of the event (default is an empty string).
            node_ids: (list[int]) A list of node ids to apply the event to. None means all nodes.
            start_day: (int) The model simulation time to start the event.
        Returns:
            New campaign event.
    """

    out_ivs = out_iv if isinstance(out_iv, list) else [out_iv]
    in_triggers = in_trigger if isinstance(in_trigger, list) else [in_trigger]
    event = comm.TriggeredCampaignEvent(camp, Start_Day=start_day, Event_Name=event_name,
                                        Nodeset_Config=utils.do_nodes(camp.schema_path, node_ids=node_ids),
                                        Triggers=in_triggers, Intervention_List=out_ivs, Demographic_Coverage=coverage,
                                        Target_Gender=target_sex, Property_Restrictions=property_restrictions,
                                        Target_Age_Min=target_age_min, Target_Age_Max=target_age_max, Delay=delay)
    # TODO: ask, should we ALWAYS pop these targeting configs? I think not, once they are implemented...
    event.Event_Coordinator_Config.pop("Targeting_Config", None)
    event.Event_Coordinator_Config.Intervention_Config.pop("Targeting_Config", None)
    event['Event_Name'] = event_name  # TODO: This should be in emod-api comm.TriggeredCampaignEvent, right?
    camp.add(event)


# An alias for triggered_event_common.
add_triggered_event = triggered_event_common


def add_scheduled_event(camp, out_iv, coverage=1.0, target_sex="All",
                        property_restrictions: List[str] = None, event_name="", node_ids: List[int] = None,
                        start_day: int = 1):
    out_ivs = out_iv if isinstance(out_iv, list) else [out_iv]
    event = comm.ScheduledCampaignEvent(camp, Start_Day=start_day, Event_Name=event_name,
                                        Nodeset_Config=utils.do_nodes(camp.schema_path, node_ids=node_ids),
                                        Intervention_List=out_ivs, Demographic_Coverage=coverage,
                                        Target_Gender=target_sex, Property_Restrictions=property_restrictions)
    # TODO: ck4, needed? (following two lines)
    event.Event_Coordinator_Config.pop("Targeting_Config", None)
    event.Event_Coordinator_Config.Intervention_Config.pop("Targeting_Config", None)
    event['Event_Name'] = event_name  # TODO: This should be in emod-api comm.TriggeredCampaignEvent, right?
    camp.add(event)


def add_reference_tracked_event(camp,
                                out_iv,
                                time_value_map: dict,
                                event_name: str = '',
                                target_min_age: float = 0,
                                target_max_age: float = 200,
                                target_sex: str = 'All',
                                target_disease_state: str = None,
                                update_period: float = 30.4166666666667,
                                start_day: float = 1960.5,
                                node_ids: List[int] = None):
    # out_ivs = out_iv if isinstance(out_iv, list) else [out_iv]
    event = rt.DistributeIVByRefTrack(camp=camp,
                                      Start_Day=start_day,
                                      Intervention=out_iv,
                                      TVMap=time_value_map,
                                      node_ids=node_ids,
                                      Target_Age_Min=target_min_age,
                                      Target_Age_Max=target_max_age,
                                      Target_Gender=target_sex,
                                      Update_Period=update_period,
                                      Event_Name=event_name,
                                      Target_Disease_State=target_disease_state)
    # event.Event_Name = event_name
    event['Event_Name'] = event_name  # TODO: This should be in emodpy-hiv rt.DistributeIVByRefTrack, right?
    camp.add(event)


def add_choice( camp, sympto_signal="NewlySymptomatic", get_tested_signal="GetTested" ):
    """
        Listen for a trigger. Defaults to 'NewlySymptomatic'. Then toss a fair coin; in case of heads,
        Distribute diagnostic (and publish signal -- default is 'GetTested'; tails maybe it's just a cold ('Ignore').

        Args:
            camp: The central campaign accumulator, from emod_api.campaign.
            sympto_signal (str): The signal or trigger we are listening for. Doesn't have to be anything to do with 
        symptomaticity but defaults to "NewlySymptomatic".  
            get_tested_signal (str): The signal/trigger published if coin toss is heads and person gets tested.  
    """
    actual_iv = randomchoice.new_diagnostic( camp, choices={ get_tested_signal: 0.5, "Ignore": 0.5 } )
    triggered_event_common( camp, in_trigger=sympto_signal, out_iv=actual_iv, event_name="Decide_On_Testing" )
 
def add_test( camp, get_tested_signal="GetTested" ):
    """
        Listen for get_tested_signal signal (defaults to "GetTested"). Then give HIV RapidDiagnostic test after a delay of 30 days.
        Publish 'HIVPositiveTest' on +ve or 'HIVNegativeTest' on -ve.
    """
    actual_iv = rapiddiag.new_diagnostic( camp, Positive_Event="HIVPositiveTest", Negative_Event="HIVNegativeTest" )
    delayed_iv = comm.DelayedIntervention( camp, [ actual_iv ], Delay_Dict={ "Delay_Period_Constant": 30 } )
    triggered_event_common( camp, get_tested_signal, delayed_iv, event_name="Test" )

def trigger_art_from_pos_test( camp, input_signal="HIVPositiveTest", output_signal="StartTreatment", lag_time=30 ):
    """
        Listen for HIVPositiveTest trigger. Then Trigger ART. Note that Trigger ART isn't same as starting it.
    """
    actual_iv = comm.BroadcastEvent( camp, output_signal )
    delayed_iv = comm.DelayedIntervention( camp, [ actual_iv ], Delay_Dict={ "Delay_Period_Constant": lag_time } )
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

