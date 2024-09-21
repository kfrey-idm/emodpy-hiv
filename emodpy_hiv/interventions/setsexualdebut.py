from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emodpy_hiv.interventions.reftrackercoord import DistributeIVByRefTrackCoord
from emodpy_hiv.interventions.utils import set_intervention_properties

from typing import List


def track_sexual_debut_intervention(
        camp,
        YearSexualDebutRatios,
        Start_Year = 1960.5,
        End_Year = 2050,
        node_ids = None,
        Target_Age_Max = 125,
        Target_Age_Min = 0,
        Target_Demographic = "Everyone",
        Target_Gender = "All",
        Update_Period = 30.416667,
        Distributed_Event_Trigger = "Setting_Age_Sexual_Debut",
        Setting_Type = "CURRENT_AGE",
        Age_Years = None,
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
):
    """
        Return a campaign event with an intervention that sets target values for sexual debuts for different points in time.

        Args:
            camp: emod_api.campaign object with schema_path set.
            YearSexualDebutRatios: A map that maps time to values e.g.  {"1960": 0.1, "1970": 0.2, "1980": 0.3}
            Start_Year: When to start.
            End_Year: When to end.
            node_ids: Nodes to target with this intervention, return from utils.do_nodes().
            Target_Age_Max: Maximum age (in years).
            Target_Age_Min: Minimum age (in years).
            Target_Demographic: Everyone, ExplicitAgeRanges, etc.
            Target_Gender: All, Male, or Female.
            Update_Period: Number representing how frequently the distributions are done.
            Distributed_Event_Trigger: Event that is broadcasted when the intervention is distributed to the individual.
            Setting_Type: "CURRENT_AGE" lets individuals debut at their current age, "USER_SPECIFIED" uses Age_Years to set the age of sexual debut.
            Age_Years: Age of sexual debut.

        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new
            ReferenceTrackingEventCoordinatorTrackingConfig intervention ready to be added to a campaign.
    """

    event = _new_intervention(camp=camp, Setting_Type=Setting_Type, Age_Years=Age_Years,
                              Distributed_Event_Trigger=Distributed_Event_Trigger,
                              intervention_name=intervention_name,
                              disqualifying_properties=disqualifying_properties,
                              new_property_value=new_property_value
                              )
    tracking_config = s2c.get_class_with_defaults("IsPostDebut", camp.schema_path)  # default, "Is_Equal_To": 1
    return DistributeIVByRefTrackCoord(camp, Start_Year, event, YearSexualDebutRatios,
                                       End_Year=End_Year, node_ids=node_ids,
                                       Target_Age_Max=Target_Age_Max, Target_Age_Min=Target_Age_Min,
                                       Target_Demographic=Target_Demographic, Target_Gender=Target_Gender,
                                       Tracking_Config=tracking_config, Update_Period=Update_Period)


def _new_intervention(camp, Setting_Type=None, Age_Years=None, Distributed_Event_Trigger=None,
                      intervention_name: str = None, disqualifying_properties: List[str] = None,
                      new_property_value: str = None):
    """
        The SetSexualDebutAge intervention sets the age of sexual debut - i.e. when the person starts seeking sexual relationships.
        Args:
            camp: emod_api.campaign object with schema_path set.
            Setting_Type: "USER_SPECIFIED" or "CURRENT_AGE". "USER_SPECIFIED" needs Age_Years to be set.
            Age_Years: Age at what on individuals will debut.
            Distributed_Event_Trigger: Event that is distributed when the intervention is given to the individual.
        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new SetSexualDebutAge intervention
    """
    intervention = s2c.get_class_with_defaults("SetSexualDebutAge", camp.schema_path)
    camp.implicits.append(_enable_debut_age_as_intervention)

    if Setting_Type is not None:
        intervention.Setting_Type = Setting_Type
        if intervention.Setting_Type == "USER_SPECIFIED":
            if Age_Years is None:
                raise ValueError("If 'Setting_Type' == 'USER_SPECIFIED', 'Age_Years' must be set")
            intervention.Age_Years = Age_Years
        if intervention.Setting_Type == "CURRENT_AGE" and Age_Years is not None:
            raise ValueError("'Setting_Type' == 'CURRENT_AGE', sets the age of sexual debut to the current age of the"
                             " individual when the intervention is received. 'Age_Years' will not be used, please set to None")



    if Distributed_Event_Trigger is not None:
        intervention.Distributed_Event_Trigger = Distributed_Event_Trigger

    set_intervention_properties(intervention,
                                intervention_name=intervention_name,
                                disqualifying_properties=disqualifying_properties,
                                new_property_value=new_property_value)

    return intervention


def new_intervention_event(
        camp,
        Event_Start_Day=1,
        Coverage=1.0,
        Target_Age_Max=None,
        Target_Age_Min=None,
        Target_Gender="All",
        Target_Demographic="Everyone",
        node_ids=None,
        Setting_Type=None,
        Age_Years=None,
        Distributed_Event_Trigger=None,
        intervention_name: str = None,
        disqualifying_properties: List[str] = None,
        new_property_value: str = None
):
    """
        SetSexualDebutAge campaign event to set the age of sexual debut.
        Args:
            camp: emod_api.campaign object with schema_path set.camp ():
            Event_Start_Day: When to start.
            Coverage: Coverage of the intervention.
            Target_Age_Max: Maximum age (in years).
            Target_Age_Min: Minimum age (in years).
            Target_Gender: All, Male, or Female.
            Target_Demographic: Everyone, ExplicitAgeRanges, etc.
            node_ids: Nodes to target with this intervention, return from utils.do_nodes().
            Setting_Type: "USER_SPECIFIED" or "CURRENT_AGE". "USER_SPECIFIED" needs Age_Years to be set.
            Age_Years: Age at what on individuals will debut.
            Distributed_Event_Trigger: Event that is distributed when the intervention is applied.
            intervention_name (str): The name of the intervention.
            disqualifying_properties (list of str): A list of IndividualProperty key:value pairs that cause an intervention to be aborted
            new_property_value (str): An optional IndividualProperty key:value pair that will be assigned when the intervention is distributed.


        Returns:
            ReadOnlyDict: Schema-based smart dictionary representing a new SetSexualDebutAge event
            that can be added to a campaign.
    """
    iv = _new_intervention(camp, Setting_Type, Age_Years, Distributed_Event_Trigger,
                           intervention_name=intervention_name,
                           disqualifying_properties=disqualifying_properties,
                           new_property_value=new_property_value)

    # Coordinator
    coordinator = s2c.get_class_with_defaults("StandardEventCoordinator", camp.schema_path)
    coordinator.Intervention_Config = iv
    coordinator.Demographic_Coverage = Coverage

    if Target_Demographic == "ExplicitGenderAndAgeRanges":
        if Target_Gender == "All":
            raise ValueError("If 'Target_Demographic' == 'ExplicitGenderAndAgeRanges', 'Target_Gender' must be set")
        if Target_Age_Min is None or Target_Age_Max is None:
            raise ValueError("If 'Target_Demographic' == 'ExplicitGenderAndAgeRanges', 'Target_Age_Min' and 'Target_Age_Max' must be set")

    elif Target_Demographic == "ExplicitAgeRanges":
        if Target_Age_Min is None or Target_Age_Max is None:
            raise ValueError("If 'Target_Demographic' == 'ExplicitAgeRanges', 'Target_Age_Min' and 'Target_Age_Max' must be set")

    coordinator.Target_Age_Min = Target_Age_Min
    coordinator.Target_Age_Max = Target_Age_Max
    coordinator.Target_Demographic = Target_Demographic
    coordinator.Target_Gender = Target_Gender

    # Event
    event = s2c.get_class_with_defaults("CampaignEvent", camp.schema_path)
    event.Event_Coordinator_Config = coordinator
    event.Start_Day = float(Event_Start_Day)
    event.Nodeset_Config = utils.do_nodes(camp.schema_path, node_ids)
    from . import utils as hiv_utils
    hiv_utils.declutter(event)

    return event


def new_intervention_as_file(camp, start_day, filename="SexualDebut.json"):
    """
    Adds the SetSexualDebutAge event to the emod_api.campaign object and saves the campaign to a file.
    Args:
        camp: emod_api.campaign object
        start_day: start day of the event
        filename: output file name

    Returns:
        filename: name of the file
    """
    camp.add(new_intervention_event(camp, Event_Start_Day=start_day), first=True)
    camp.save(filename)
    return filename


def _enable_debut_age_as_intervention(config):
    config.parameters.Sexual_Debut_Age_Setting_Type = "FROM_INTERVENTION"
    return config
