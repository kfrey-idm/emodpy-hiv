def _convert_map_to_lists( tvmap ):
    times = []
    values = []
    # TBD: Find way to use schema to enforce datatypes...
    # t2v = s2c.get_class_with_defaults( "idmType:InterpolatedValueMap", camp.schema_path )
    for key, value in tvmap.items():
        times.append( float(key) )
        values.append( value )
    return times, values

def set_tvmap_lists_from_map( tvmap, param ):
    t, v = _convert_map_to_lists( tvmap )
    param.Times = t 
    param.Values = v 

def declutter( event ):
    """
    These are mostly temporary hacks that clean up the output json; should go away with subsequent
    cherry-picks of schema enhancements from other branches. 
    """
    if "Disqualifying_Properties" in event.Event_Coordinator_Config.Intervention_Config:
        event.Event_Coordinator_Config.Intervention_Config.pop( "Disqualifying_Properties" )
    if "Dont_Allow_Duplicates" in event.Event_Coordinator_Config.Intervention_Config:
        event.Event_Coordinator_Config.Intervention_Config.pop( "Dont_Allow_Duplicates" )
    if "Positive_Diagnosis_Config" in event.Event_Coordinator_Config.Intervention_Config:
        event.Event_Coordinator_Config.Intervention_Config.pop( "Positive_Diagnosis_Config" )
    if "Negative_Diagnosis_Config" in event.Event_Coordinator_Config.Intervention_Config:
        event.Event_Coordinator_Config.Intervention_Config.pop( "Negative_Diagnosis_Config" )
    if "Event_Or_Config" in event.Event_Coordinator_Config.Intervention_Config:
        event.Event_Coordinator_Config.Intervention_Config.Event_Or_Config = "Event"
    event.Event_Coordinator_Config.pop( "Targeting_Config" )
    event.Event_Coordinator_Config.pop( "Node_Property_Restrictions" )

def broadcast_event_immediate( camp, event_trigger:str='Births' ):
    import emod_api.interventions.common as common
    return common.BroadcastEvent( camp, event_trigger )

def broadcast_event_delayed( camp, event_trigger, delay=None ):
    import emod_api.interventions.common as comm
    if delay is None:
        raise ValueError( "broadcast_event_delayed called with no delay." )
    be = comm.BroadcastEvent( camp, event_trigger )
    di = comm.DelayedIntervention( camp, [ be ], Delay_Dict=delay )
    return di
