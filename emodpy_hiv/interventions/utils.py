from typing import List


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
    # if "Disqualifying_Properties" in event.Event_Coordinator_Config.Intervention_Config:
    #     event.Event_Coordinator_Config.Intervention_Config.pop( "Disqualifying_Properties" )
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


def set_intervention_properties(iv, intervention_name: str = None, disqualifying_properties: List[str] = None,
                                new_property_value: str = None):
    """
    Set properties of an intervention.

    Args:
        iv: an intervention object.
        intervention_name (str): The optional name used to refer to this intervention as a means to differentiate it
            from others that use the same class. The default name is the name of the class, but providing a unique name
            allows for distinguishing different configurations. For example, if you were distributing two vaccines where
            one had a higher efficacy than the other, you could use this parameter to call one 'HighEfficacyVaccine'
            and the other 'LowEfficacyVaccine'. Doing this would allow you to collect data in reports on each version.
        disqualifying_properties (List[str]): A list of IndividualProperty key:value pairs that cause an intervention
            to be aborted. Right before an intervention is updated, it will check to see if the individual has one of
            the property values defined in this list. If it does, the intervention will not update and immediately
            expire.
        new_property_value (str): An optional IndividualProperty key:value pair that will be assigned when the
            intervention is first updated. After the individual gets the intervention and goes to update/apply it for
            the first time, the intervention first checks to see if the individual has any disqualifying properties.
            If they do not, then this property value will be assigned.

    Returns:
        None, but the intervention object is modified in place.

    """
    if intervention_name is not None:
        iv.Intervention_Name = intervention_name
    if disqualifying_properties is not None:
        iv.Disqualifying_Properties = disqualifying_properties.copy()
    if new_property_value is not None:
        iv.New_Property_Value = new_property_value

