from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emod_api.interventions import common as comm


def DistributeIVByRefTrackCoord(
        camp,
        Start_Year,
        Intervention_Config,
        Time_Value_Map,
        Tracking_Config,
        Targeting_Config = None,
        End_Year = None,
        node_ids = None,
        Node_Property_Restrictions = None,
        Property_Restrictions = None,
        Property_Restrictions_Within_Node = None,
        Target_Age_Max = None,
        Target_Age_Min = None,
        Target_Demographic = "Everyone",
        Target_Gender = "All",
        Target_Residents_Only = None,
        Update_Period = 365
):
    """
        Create and return a ReferenceTrackingEventCoordinatorTrackingConfig EventCoordinator.

        Args:
            camp: emod_api.campaign object with schema_path set.
            Start_Year: When to start.
            Intervention_Config: Valid intervention to be distributed together as necessary to track coverage targets. Can be single intervention or list (list is useful where you want a co-event). If list, actual intervention should be first.
            Time_Value_Map: A pairing of time (in years) and the fraction of the targeted group to have the attribute specified by Tracking_Config at that time. E.g.  {"1960": 0.1, "1970": 0.2, "1980": 0.3}
            Tracking_Config: Defines the attribute to be tracked within the targeted group; the intervention will be distributed to people without the attribute, if coverage is below the target level the time of polling.
            Targeting_Config: Allows you to specify more detail on the targeted group that you want to have the given attribute.
            End_Year: When to end.
            node_ids: Nodes to target with this intervention, return from utils.do_nodes().
            Node_Property_Restrictions: A list of NodeProperty key:value pairs. A node must have the value for the given key in order for its humans to be considered.
            Property_Restrictions: Individual Properties a person must have to receive the intervention(s).
            Property_Restrictions_Within_Node: A list of the IndividualProperty key:value pairs, as defined in the demographics file, that individuals must have to be targeted by this intervention.
            Target_Age_Max: Maximum age (in years).
            Target_Age_Min: Minimum age (in years).
            Target_Demographic: Everyone, ExplicitAgeRanges, ExplicitAgeRangesAndGender, etc.
            Target_Gender: All, Male, or Female.
            Target_Residents_Only: Distribute intervention only to individuals that began the simulation in the node.
            Update_Period: This duration between distributions is used to calculate the number of timesteps between distributions (= lower_bound ( Update_Period / dt )).
                            Values < 2*dt result in one distribution per time step, to get one distribution every two timesteps set 3*dt > Update_Period > 2*dt.
        Returns:
            ReadOnlyDict: ReferenceTrackingEventCoordinatorTrackingConfig EventCoordinator ready to be added to a campaign.
    """

    if Property_Restrictions and Property_Restrictions_Within_Node:
        raise ValueError("Cannot set both Property_Restrictions and Property_Restrictions_Within_Node")

    if Target_Demographic == "ExplicitAgeRanges" or Target_Demographic == "ExplicitAgeRangesAndGender":
        if Target_Age_Min is None or Target_Age_Max is None:
            raise ValueError(
                "Target_Age_Min and Target_Age_Max need to be set when setting Target_Demographic == 'ExplicitAgeRanges' or 'ExplicitAgeRangesAndGender'")

    global schema_path
    schema_path = (camp.schema_path if camp is not None else schema_path)

    event = s2c.get_class_with_defaults("CampaignEventByYear", schema_path)
    coordinator = s2c.get_class_with_defaults("ReferenceTrackingEventCoordinatorTrackingConfig", schema_path)
    event.Event_Coordinator_Config = coordinator

    event.Start_Year = float(Start_Year)

    # create two lists from TimeValueMap, one for keys and one for values
    k, v = [list(elem) for elem in zip(*Time_Value_Map.items())]
    coordinator.Time_Value_Map.Times, coordinator.Time_Value_Map.Values = [float(k) for k in k], v
    coordinator.Tracking_Config = Tracking_Config
    coordinator.Targeting_Config = Targeting_Config

    # Intervention can be single or list. If list, we bundle into a M.I.D.
    if type(Intervention_Config) is list:
        mid = comm.MultiInterventionDistributor(camp, Intervention_Config)
        Intervention_Config = mid
    coordinator.Intervention_Config = Intervention_Config

    if Property_Restrictions is not None:
        coordinator.Property_Restrictions = Property_Restrictions
    elif Property_Restrictions_Within_Node is not None:
        coordinator.Property_Restrictions_Within_Node = Property_Restrictions_Within_Node

    prs = utils._convert_prs(Property_Restrictions)
    if len(prs) > 0 and type(prs[0]) is dict:
        coordinator.Property_Restrictions_Within_Node = prs
        coordinator.pop("Property_Restrictions")
    else:
        coordinator.Property_Restrictions = prs
        coordinator.pop("Property_Restrictions_Within_Node")

    coordinator.End_Year = End_Year
    coordinator.Node_Property_Restrictions = Node_Property_Restrictions
    coordinator.Target_Age_Min = Target_Age_Min     # if None, defaults from schema are used
    coordinator.Target_Age_Max = Target_Age_Max
    coordinator.Target_Gender = Target_Gender
    coordinator.Target_Demographic = Target_Demographic
    coordinator.Target_Residents_Only = Target_Residents_Only
    coordinator.Update_Period = Update_Period

    event.Nodeset_Config = utils.do_nodes(camp.schema_path, node_ids)
    return event
