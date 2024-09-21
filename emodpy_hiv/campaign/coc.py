# QUESTION: verify dead-labeled code is dead
import pandas as pd
import decimal

from emodpy_hiv.interventions.cascade_helpers import *
import emodpy_hiv.interventions.utils as hiv_utils
from emodpy_hiv.interventions import (outbreak, sigmoiddiag, randomchoice, yearandsexdiag, rapiddiag, modcoinf, pmtct,
                                      malecirc, stipostdebut, nchooser, hivmuxer)
from emod_api.interventions.common import PropertyValueChanger
import emod_api.campaign

from typing import List, Tuple, Dict, Union


class CustomEvent:  # consider moving this to a separate file or make it a private class.
    ART_STAGING = 'ARTStaging'
    ART_STAGING_0 = 'ARTStaging0'  # immediate ART staging, rename this to ImmediateARTStaging?
    ART_STAGING_1 = 'ARTStaging1'  # ART staging diagnostic test, rename this to ARTStagingDiagnosticTest?
    ART_STAGING_2 = 'ARTStaging2'
    ART_STAGING_3 = 'ARTStaging3'
    ART_STAGING_4 = 'ARTStaging4'
    ART_STAGING_5 = 'ARTStaging5'
    ART_STAGING_6 = 'ARTStaging6'
    # ART_STAGING_7 = 'ARTStaging7' # not used
    ART_STAGING_8 = 'ARTStaging8'
    ART_STAGING_9 = 'ARTStaging9'

    STI_DEBUT = "STIDebut"
    COMMERCIAL_UPTAKE = "Commercial_Uptake"
    COMMERCIAL_DROPOUT = "Commercial_Dropout"
    COMMERCIAL_DELAY_FROM_DEBUT_UPTAKE = "Commercial_DelayFromDebutToUptake"

    HCT_TESTING_LOOP = 'HCTTestingLoop'
    HCT_TESTING_LOOP_0 = 'HCTTestingLoop0'
    HCT_TESTING_LOOP_1 = 'HCTTestingLoop1'
    HCT_TESTING_LOOP_2 = 'HCTTestingLoop2'

    HCT_UPTAKE_POST_DEBUT_0 = 'HCTUptakePostDebut0'
    HCT_UPTAKE_POST_DEBUT_1 = 'HCTUptakePostDebut1'
    HCT_UPTAKE_POST_DEBUT_2 = 'HCTUptakePostDebut2'
    HCT_UPTAKE_POST_DEBUT_3 = 'HCTUptakePostDebut3'
    # HCT_UPTAKE_POST_DEBUT_4 = 'HCTUptakePostDebut4'  # not used
    # HCT_UPTAKE_POST_DEBUT_5 = 'HCTUptakePostDebut5'  # not used
    # HCT_UPTAKE_POST_DEBUT_6 = 'HCTUptakePostDebut6'  # not used
    HCT_UPTAKE_POST_DEBUT_7 = 'HCTUptakePostDebut7'
    HCT_UPTAKE_POST_DEBUT_8 = 'HCTUptakePostDebut8'
    HCT_UPTAKE_POST_DEBUT_9 = 'HCTUptakePostDebut9'

    LINKING_TO_ART_0 = 'LinkingToART0'
    LINKING_TO_PRE_ART_0 = 'LinkingToPreART0'

    LOST_FOREVER_0 = "LostForever0"
    LOST_FOREVER_9 = "LostForever9"

    ON_ART_0 = 'OnART0'
    ON_ART_1 = 'OnART1'

    ON_PRE_ART = 'OnPreART'
    ON_PRE_ART_0 = 'OnPreART0'
    ON_PRE_ART_1 = 'OnPreART1'
    ON_PRE_ART_2 = 'OnPreART2'
    ON_PRE_ART_3 = 'OnPreART3'
    ON_PRE_ART_4 = 'OnPreART4'


BIRTH = 'Births'
HIV_NEGATIVE = 'HIV_Negative'
NEWLY_SYMPTOMATIC = 'NewlySymptomatic'  # 'HIVSymptomatic' is replaced by 'NewlySymptomatic'
SIX_WEEKS_OLD = 'SixWeeksOld'
TWELVE_WEEKS_PREGNANT = 'TwelveWeeksPregnant'
NOT_HAS_INTERVENTION = 'Not_Have_Intervention'
MALE = 'Male'
FEMALE = 'Female'
EPSILON = 1e-3
ANY_MC = 'Any_MC'
PROGRAM_VMMC = 'Program_VMMC'


# These are the Event triggers for the Cascade states.
HCT_UPTAKE_POST_DEBUT_TRIGGER_1 = CustomEvent.HCT_UPTAKE_POST_DEBUT_1  # directly go to HIVMuxer delay in HCTUptakePostDebut state without going through STIIsPostDebut
HCT_UPTAKE_POST_DEBUT_TRIGGER_2 = CustomEvent.HCT_UPTAKE_POST_DEBUT_3
HCT_UPTAKE_POST_DEBUT_TRIGGER_3 = CustomEvent.HCT_UPTAKE_POST_DEBUT_9  # lost to follow-up
HCT_TESTING_LOOP_TRIGGER = CustomEvent.HCT_TESTING_LOOP_0
LINKING_TO_PRE_ART_TRIGGER = CustomEvent.LINKING_TO_PRE_ART_0
ON_PRE_ART_TRIGGER = CustomEvent.ON_PRE_ART_0
ON_ART_TRIGGER_1 = CustomEvent.ON_ART_0  # go to randomchoice with choices to a HIVMuxer delay or ON_ART_TRIGGER_2 in OnART stage
ON_ART_TRIGGER_2 = CustomEvent.ON_ART_1  # directly go to ARTBasic in OnART stage without going through randomchoice
LINKING_TO_ART_TRIGGER = CustomEvent.LINKING_TO_ART_0
ART_STAGING_DIAGNOSTIC_TEST_TRIGGER = CustomEvent.ART_STAGING_0
ART_STAGING_TRIGGER_1 = CustomEvent.ART_STAGING_1    # go to randomchoice in ARTStaging
ART_STAGING_TRIGGER_2 = CustomEvent.ART_STAGING_2    # directly go to hivmuxer in ARTStaging without going through randomchoice
DUMMY_TRIGGER = 'DummyTrigger'  # a DoNothingTrigger
LOST_FOREVER_TRIGGER = CustomEvent.LOST_FOREVER_0

class CascadeState:
    LOST_FOREVER = "CascadeState:LostForever"
    ON_ART = "CascadeState:OnART"
    LINKING_TO_ART = "CascadeState:LinkingToART"
    ON_PRE_ART = "CascadeState:OnPreART"
    LINKING_TO_PRE_ART = "CascadeState:LinkingToPreART"
    ART_STAGING = "CascadeState:ARTStaging"
    ART_STAGING_DIAGNOSTIC_TEST = 'CascadeState:ARTStagingDiagnosticTest'
    TESTING_ON_SYMPTOMATIC = "CascadeState:TestingOnSymptomatic"
    TESTING_ON_ANC = "CascadeState:TestingOnANC"
    TESTING_ON_CHILD_6W = "CascadeState:TestingOnChild6w"
    HCT_TESTING_LOOP = "CascadeState:HCTTestingLoop"
    HCT_UPTAKE_AT_DEBUT = "CascadeState:HCTUptakeAtDebut"
    HCT_UPTAKE_POST_DEBUT = "CascadeState:HCTUptakePostDebut"


def timestep_from_year(year: Union[float, int], base_year: Union[float, int]) -> int:
    """
    Converts a year into a timestep based on a base year.

    Args:
        year (Union[float, int]): The year to be converted.
        base_year (Union[float, int]): The base year for the conversion.

    Returns:
        int: The timestep corresponding to the given year.
    """
    return int((year - base_year) * 365)


def convert_time_value_map(time_value_map) -> dict:
    """
    Converts a time-value map into a dictionary where each time is a key and its corresponding value is the value. This
    is the expected format for the TVMap in the current emodpy-hiv interventions code, ex. yearandsexdiag.new_diagnostic
    function.

    Args:
        time_value_map (dict): A dictionary containing two lists, "Times" and "Values".
                               "Times" is a list of times (years) and "Values" is a list of corresponding values.

    Returns:
        dict: A dictionary where each time from "Times" is a key and its corresponding value from "Values" is the value.

    Example:
        >>> time_value_map = {"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 500]}
        >>> convert_time_value_map(time_value_map)
        {2002: 200, 2010.5: 350, 2013.95: 500}
    """
    time_value_map_convert = {}
    for time, value in zip(time_value_map["Times"], time_value_map["Values"]):
        time_value_map_convert[time] = value
    return time_value_map_convert


# This is the time value map that used in multiple HIVPiecewiseByYearAndSexDiagnostic interventions in the Zambia model
# which we used as the default time value map for convenience. Please note that the Values in this time value map are
# all 0s, which means the intervention will return all negative result(zero possibility of positive test results).
all_negative_time_value_map = convert_time_value_map({"Times": [1990, 2016], "Values": [0, 0]})


def seed_infections(campaign: emod_api.campaign,
                    seeding_node_ids: Union[List[int], None] = None,
                    seeding_start_year: float = 1982,
                    seeding_coverage: float = 0.075,
                    seeding_target_min_age: float = 0,
                    seeding_target_max_age: float = 200,
                    seeding_target_gender: str = "All",
                    seeding_target_property_restrictions: list = None) -> None:
    """
    Add a OutbreakIndividual intervention with StandardEventCoordinator to the campaign object.
    Args:
        campaign: emod_api.campaign object
        seeding_node_ids: List of node IDs to seed infections in. Defaults to None, which seeds infections in all nodes.
        seeding_start_year: The year to start seeding infections. Defaults to 1982.
        seeding_coverage: The coverage of the seeding infections. Defaults to 0.075.
        seeding_target_min_age: The minimum age of the target population. Defaults to 0.
        seeding_target_max_age: The maximum age of the target population. Defaults to 200.
        seeding_target_gender: The gender of the target population. Defaults to "All". Options are "Male", "Female", or "All".
        seeding_target_property_restrictions: List of property restrictions. Defaults to None.

    Returns:
        None

    """
    event_name = f"Epidemic seeding in node(s) {str(seeding_node_ids)}"
    event = outbreak.seed_infections(campaign,
                                     node_ids=seeding_node_ids,
                                     event_name=event_name,
                                     start_day=timestep_from_year(seeding_start_year, campaign.base_year),
                                     coverage=seeding_coverage,
                                     target_min_age=seeding_target_min_age,
                                     target_max_age=seeding_target_max_age,
                                     target_gender=seeding_target_gender,
                                     target_properties=seeding_target_property_restrictions)
    campaign.add(event)


# property restrictions/disqualifying properties/new property values checked
def add_csw(campaign: emod_api.campaign,
            node_ids: Union[List[int], None] = None,
            male_uptake_coverage: float = 0.03,
            female_uptake_coverage: float = 0.03):
    """
    Manages commercial sex worker (CSW) uptake and dropout (with delays) for men and women.

    Setting a few women to Risk=HIGH and significantly more men to Risk=HIGH makes the women the sex workers and the
    men the sex clients. Supply and demand cause the females to have lots of relationships with the men that are also
    Risk=HIGH. The women have lots of relationships because so many men want them, but the scarcity of the women allow
    the men to have only a few.

    Args:
        campaign (emod_api.campaign): The campaign to which the CSW management is to be added.
        node_ids (List[int], optional): A list of node IDs where the CSW management is to be applied.
                                            Defaults to None, which applies to all nodes.
        male_uptake_coverage (float, optional): The coverage of CSW uptake among males. Defaults to 0.03.
        female_uptake_coverage (float, optional): The coverage of CSW uptake among females. Defaults to 0.03.

    Returns:
        None

    Example:
        >>> add_csw(campaign, node_ids=[1, 2, 3], male_uptake_coverage=0.05, female_uptake_coverage=0.04)
    """
    # manages commercial sex worker uptake and dropout (with delays) for men and women
    initial_trigger = CustomEvent.STI_DEBUT
    uptake_event = CustomEvent.COMMERCIAL_UPTAKE  # also serves as the dropout_delay_event
    dropout_event = CustomEvent.COMMERCIAL_DROPOUT
    uptake_delay_event = CustomEvent.COMMERCIAL_DELAY_FROM_DEBUT_UPTAKE

    # determine if women will become sex FSW
    time_value_map = {campaign.base_year: female_uptake_coverage}
    # time_value_map = {"Times": [campaign.base_year], "Values": [female_uptake_coverage]}
    will_become_FSW = yearandsexdiag.new_diagnostic(campaign,
                                                    Positive_Event=uptake_delay_event,
                                                    Negative_Event='None',
                                                    TVMap=time_value_map,
                                                    interpolation_order=1)
    add_triggered_event(campaign, event_name=f"Female: Will ever become FSW in node(s) {str(node_ids)}",
                        in_trigger=initial_trigger, out_iv=[will_become_FSW],
                        target_sex=FEMALE, node_ids=node_ids)

    # Female delay to uptake
    female_delay_to_uptake = hiv_utils.broadcast_event_delayed(campaign,
                                                               event_trigger=uptake_event,
                                                               delay={"Delay_Period_Min": 0, "Delay_Period_Max": 1825})
    add_triggered_event(campaign, event_name=f"Commercial Sex (Female): Delay to Uptake in node(s) {str(node_ids)}",
                        in_trigger=uptake_delay_event, out_iv=[female_delay_to_uptake],
                        target_sex=FEMALE, node_ids=node_ids)

    # Female delay to dropout
    # QUESTION: campaign json indicates this is a different distribution from men (and from men/women uptake). Ok?
    female_dropout_delay = {"Delay_Period_Lambda": 2215, "Delay_Period_Kappa": 3.312}
    female_delay_to_dropout = hiv_utils.broadcast_event_delayed(campaign,
                                                                event_trigger=dropout_event,
                                                                delay=female_dropout_delay)
    add_triggered_event(campaign, event_name=f"Commercial Sex (Female): Delay to Dropout in node(s) {str(node_ids)}",
                        in_trigger=uptake_event, out_iv=[female_delay_to_dropout],
                        target_sex=FEMALE, node_ids=node_ids)

    # determine if men will become FSW clients
    # Use start_year + 0.5 to make sure it happens after setting Risk=HIGH
    time_value_map = {campaign.base_year + 0.5: male_uptake_coverage}
    will_become_FSW_client = yearandsexdiag.new_diagnostic(campaign,
                                                           Positive_Event=uptake_delay_event,
                                                           Negative_Event='None',
                                                           TVMap=time_value_map,
                                                           interpolation_order=1)
    add_triggered_event(campaign, event_name=f"Male: Will ever become FSW client in node(s) {str(node_ids)}",
                        in_trigger=initial_trigger, out_iv=[will_become_FSW_client],
                        target_sex=MALE, node_ids=node_ids)

    # Male delay to uptake
    male_delay_to_uptake = hiv_utils.broadcast_event_delayed(campaign,
                                                             event_trigger=uptake_event,
                                                             delay={"Delay_Period_Min": 0, "Delay_Period_Max": 3650})
    add_triggered_event(campaign, event_name=f"Commercial Sex (Male): Delay to Uptake in node(s) {str(node_ids)}",
                        in_trigger=uptake_delay_event, out_iv=[male_delay_to_uptake],
                        target_sex=MALE, node_ids=node_ids)

    # Male delay to dropout
    male_dropout_delay = {"Delay_Period_Min": 730, "Delay_Period_Max": 10950}
    male_delay_to_dropout = hiv_utils.broadcast_event_delayed(campaign,
                                                              event_trigger=dropout_event,
                                                              delay=male_dropout_delay)
    add_triggered_event(campaign, event_name=f"Commercial Sex (Male): Delay to Dropout in node(s) {str(node_ids)}",
                        in_trigger=uptake_event, out_iv=[male_delay_to_dropout],
                        target_sex=MALE, node_ids=node_ids)

    # commercial uptake, all genders
    risk_to_high = PropertyValueChanger(campaign,
                                        Target_Property_Key='Risk', Target_Property_Value='HIGH')
    add_triggered_event(campaign, event_name=f"Commercial Sex: Uptake in node(s) {str(node_ids)}",
                        in_trigger=uptake_event, out_iv=[risk_to_high],
                        node_ids=node_ids)

    # commercial dropout, all genders
    risk_to_medium = PropertyValueChanger(campaign,
                                          Target_Property_Key='Risk', Target_Property_Value='MEDIUM')
    add_triggered_event(campaign, event_name=f"Commercial Sex: Dropout in node(s) {str(node_ids)}",
                        in_trigger=dropout_event, out_iv=[risk_to_medium],
                        node_ids=node_ids)


# property restrictions/disqualifying properties/new property values checked
def add_post_debut_coinfection(campaign: emod_api.campaign,
                               coinfection_node_ids: List[int] = None,
                               coinfection_coverage: float = 0.3,
                               coinfection_gender: str = 'All',
                               coinfection_IP: Union[List[str], str] = "Risk:HIGH"):
    """
    Manages the addition of co-infections post sexual debut in the campaign.

    Args:
        campaign (emod_api.campaign): The campaign to which the co-infection management is to be added.
        coinfection_node_ids (List[int], optional): A list of node IDs where the co-infection management is to be applied.
                                                    Defaults to None, which applies to all nodes.
        coinfection_coverage (float, optional): The coverage of co-infection among the population. Defaults to 0.3.
        coinfection_gender (str, optional): The gender to which the co-infection management is to be applied.
                                             Defaults to 'All', which applies to all genders.
        coinfection_IP (Union[List[str], str], optional): The individual properties to which the co-infection management is to be applied.
                                                          Defaults to "Risk:HIGH".

    Returns:
        None

    Example:
        >>> add_post_debut_coinfection(campaign, coinfection_node_ids=[1, 2, 3], coinfection_coverage=0.4, coinfection_gender='Male', coinfection_IP="Risk:MEDIUM")
    """
    post_debut_trigger = 'initial_coinfection_post_debut'
    at_debut_trigger = CustomEvent.STI_DEBUT
    if not isinstance(coinfection_IP, list):
        coinfection_IP = [coinfection_IP]
    # intervention object setup
    modify_coinfection_status_iv = modcoinf.new_intervention(campaign)
    is_post_debut_check = stipostdebut.new_diagnostic(campaign,
                                                      Positive_Event=post_debut_trigger,
                                                      Negative_Event='None')

    # seed co-infections in the initial target post-debut population
    add_scheduled_event(campaign,
                        event_name=f"Identifying initial {coinfection_IP} post-debut population to target for coinfections",
                        out_iv=[is_post_debut_check], target_sex=coinfection_gender,
                        property_restrictions=coinfection_IP, node_ids=coinfection_node_ids,
                        start_day=1 + EPSILON)  # this must start AFTER the distribution event to distribute properly
    # distribute co-infections at sexual debut, ongoing
    add_triggered_event(campaign,
                        event_name=f"Distributing coinfections to {coinfection_IP} population at sexual debut and post debut.",
                        in_trigger=[post_debut_trigger, at_debut_trigger], out_iv=[modify_coinfection_status_iv],
                        coverage=coinfection_coverage,
                        target_sex=coinfection_gender,
                        property_restrictions=coinfection_IP, node_ids=coinfection_node_ids,
                        start_day=1)  # the default start day, but being explicit due to ordering issue


# property restrictions/disqualifying properties/new property values checked
def add_pmtct(campaign: emod_api.campaign,
              child_testing_time_value_map: dict,
              child_testing_start_year: float = 2004,
              node_ids: Union[List[int], None] = None,
              coverage: float = 1.0,
              start_year: float = 1990,
              sigmoid_ramp_min: float = 0,
              sigmoid_ramp_max: float = 0.975,
              sigmoid_ramp_midyear: float = 2005.87,
              sigmoid_ramp_rate: float = 0.7136,
              link_to_ART_rate: float = 0.8,
              treatment_a_efficacy: float = 0.9,
              treatment_b_efficacy: float = 0.96667,
              sdNVP_efficacy: float = 0.66):
    """
    Manages the addition of prevention of mother-to-child transmission (PMTCT) in the campaign.

    Args:
        campaign (emod_api.campaign): The campaign to which the PMTCT management is to be added.
        child_testing_time_value_map (dict): A dictionary containing time-value map for child testing.
        child_testing_start_year (float, optional): The start year for child testing. Defaults to 2004.
        node_ids (List[int], optional): A list of node IDs where the PMTCT management is to be applied.
                                               Defaults to None, which applies to all nodes.
        coverage (float, optional): The coverage of PMTCT among the population. Defaults to 1.0.
        start_year (float, optional): The start year for PMTCT. Defaults to 1990.
        sigmoid_ramp_min (float, optional): The minimum value for the sigmoid ramp. Defaults to 0.
        sigmoid_ramp_max (float, optional): The maximum value for the sigmoid ramp. Defaults to 0.975.
        sigmoid_ramp_midyear (float, optional): The midyear for the sigmoid ramp. Defaults to 2005.87.
        sigmoid_ramp_rate (float, optional): The rate for the sigmoid ramp. Defaults to 0.7136.
        link_to_ART_rate (float, optional): The rate for linking to ART. Defaults to 0.8.
        treatment_a_efficacy (float, optional): The efficacy of treatment A. Defaults to 0.9.
        treatment_b_efficacy (float, optional): The efficacy of treatment B. Defaults to 0.96667.
        sdNVP_efficacy (float, optional): The efficacy of Single-Dose Nevirapine (sdNVP). Defaults to 0.66.

    Returns:
        None

    Example:
        >>> add_pmtct(campaign, child_testing_time_value_map={"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 500]}, node_ids=[1, 2, 3], coverage=0.8, start_year=1995, sigmoid_ramp_min=0.1, sigmoid_ramp_max=0.9, sigmoid_ramp_midyear=2005, sigmoid_ramp_rate=0.7, link_to_ART_rate=0.85, treatment_a_efficacy=0.92, treatment_b_efficacy=0.96, sdNVP_efficacy=0.7)
    """

    start_day = timestep_from_year(start_year, campaign.base_year)
    child_testing_start_day = timestep_from_year(child_testing_start_year, campaign.base_year)
    disqualifying_properties = [CascadeState.LOST_FOREVER,
                                CascadeState.ON_ART,
                                CascadeState.LINKING_TO_ART,
                                CascadeState.ON_PRE_ART,
                                CascadeState.LINKING_TO_PRE_ART,
                                CascadeState.ART_STAGING,
                                CascadeState.TESTING_ON_SYMPTOMATIC]
    property_restrictions = 'Accessibility:Yes'

    add_state_TestingOnANC(campaign=campaign,
                           disqualifying_properties=disqualifying_properties,
                           coverage=coverage,
                           link_to_ART_rate=link_to_ART_rate,
                           node_ids=node_ids,
                           sigmoid_ramp_max=sigmoid_ramp_max,
                           sigmoid_ramp_midyear=sigmoid_ramp_midyear,
                           sigmoid_ramp_min=sigmoid_ramp_min,
                           sigmoid_ramp_rate=sigmoid_ramp_rate,
                           treatment_a_efficacy=treatment_a_efficacy,
                           treatment_b_efficacy=treatment_b_efficacy,
                           sdNVP_efficacy=sdNVP_efficacy,
                           start_day=start_day,
                           property_restrictions=property_restrictions)

    # Testing of children at 6 weeks of age
    add_state_TestingOnChild6w(campaign=campaign,
                               start_day=child_testing_start_day,
                               disqualifying_properties=disqualifying_properties,
                               time_value_map=child_testing_time_value_map,
                               node_ids=node_ids,
                               property_restrictions=property_restrictions)


# TODO from Clark: when doing A-B testing, translate Any_MC in existing json to MaleCircumcision (the new, default name used)??
# ToDo from Ye: the VMMC_Zambia.json file has different traditional_male_circumcision_coverage for HIVRandomChoice for different
#  nodes but one MaleCircumcision for all node since the traditional_male_circumcision_reduced_acquire is the same for
#  all nodes. This is not supported in the current implementation. Should we consider updating this method to support?
def add_traditional_male_circumcision(campaign: emod_api.campaign,
                                      traditional_male_circumcision_start_year: float = 1961,
                                      randomchoice_start_year: float = 1975,
                                      traditional_male_circumcision_coverage: float = 0.054978651,
                                      traditional_male_circumcision_reduced_acquire: float = 0.6,
                                      traditional_male_circumcision_node_ids: Union[List[int], None] = None):
    """
    Manages the addition of traditional male circumcision in the campaign.

    Args:
        campaign (emod_api.campaign): The campaign to which the traditional male_circumcision management is to be added.
        traditional_male_circumcision_start_year (float, optional): The start year for traditional male_circumcision interventions. Defaults to 1961.
        randomchoice_start_year (float, optional): The start year for randomchoice_start_year interventions. Defaults to 1975.
        traditional_male_circumcision_coverage (float, optional): The coverage of traditional male_circumcision among the male population. Defaults to 0.054978651.
        traditional_male_circumcision_reduced_acquire (float, optional): The reduced acquire rate for traditional male_circumcision. Defaults to 0.6.
        traditional_male_circumcision_node_ids (List[int], optional): A list of node IDs where the traditional male_circumcision management is to be applied.
                                                         Defaults to None, which applies to all nodes.

    Returns:
        None

    Example:
        >>> add_traditional_male_circumcision(campaign, traditional_male_circumcision_coverage=0.06, traditional_male_circumcision_reduced_acquire=0.5, traditional_male_circumcision_node_ids=[1, 2, 3])
    """
    # start time is arbitrary; just needs to be pre-epidemic
    start_day = timestep_from_year(randomchoice_start_year, campaign.base_year)
    will_circumcise = 'WillReceiveTraditionalMaleCircumcision'

    # set up circumcision coverage selection
    decimal_places = decimal.Decimal(str(traditional_male_circumcision_coverage)).as_tuple().exponent
    choices = {will_circumcise: traditional_male_circumcision_coverage,
               DUMMY_TRIGGER: round(1 - traditional_male_circumcision_coverage, -decimal_places)}  # to get rid of floating point decimal issues
    decide_traditional_male_circumcision = randomchoice.new_diagnostic(campaign, choices=choices)

    # Initializing historical traditional male circumcision in the population
    add_scheduled_event(campaign, event_name=f"Traditional male circumcision initialization in node(s) "
                                             f"{str(traditional_male_circumcision_node_ids)}",
                        out_iv=[decide_traditional_male_circumcision],
                        target_sex=MALE,
                        node_ids=traditional_male_circumcision_node_ids, start_day=start_day + EPSILON)

    # traditional male circumcision at birth, ongoing
    add_triggered_event(campaign, event_name=f"Traditional male circumcision at birth in node(s) "
                                             f"{str(traditional_male_circumcision_node_ids)}",
                        in_trigger=BIRTH, out_iv=[decide_traditional_male_circumcision],
                        target_sex=MALE,
                        node_ids=traditional_male_circumcision_node_ids, start_day=start_day + EPSILON)

    # NOTE: this creates per-node-set events, which is more 'wasteful' if non-all-nodes are specified. But should work
    # just as well and prevent the user from calling a separate, second TMC function
    # actual traditional male circumcision event
    malecirc_intervention_name = ANY_MC
    male_circumcision_start_day = timestep_from_year(traditional_male_circumcision_start_year, campaign.base_year)
    # this is different from the start_day above, we need to make sure it's before the previous events
    if male_circumcision_start_day > start_day:
        raise ValueError(f"The start year for traditional male circumcision ({traditional_male_circumcision_start_year})"
                         f" should be before the start year for random choice ({randomchoice_start_year}).")
    distribute_circumcision = malecirc.new_intervention(campaign,
                                                        reduced_acquire=traditional_male_circumcision_reduced_acquire,
                                                        intervention_name=malecirc_intervention_name,
                                                        distributed_event='Non_Program_MC')
    add_triggered_event(campaign, event_name=f"Apply traditional male circumcision intervention in node(s)"
                                             f" {str(traditional_male_circumcision_node_ids)}",
                        in_trigger=will_circumcise, out_iv=[distribute_circumcision],
                        target_sex=MALE,
                        node_ids=traditional_male_circumcision_node_ids, start_day=male_circumcision_start_day)
    return malecirc_intervention_name


def add_vmmc_reference_tracking(campaign: emod_api.campaign,
                                vmmc_time_value_map: dict,
                                vmmc_reduced_acquire: float = 0.6,
                                vmmc_target_min_age: float = 15,
                                vmmc_target_max_age: float = 29.999999,
                                vmmc_start_year: float = 2015,
                                vmmc_node_ids: Union[List[int], None] = None,
                                update_period: float = 30.4166666666667,
                                distributed_event_trigger: str = PROGRAM_VMMC,
                                target_disease_state: str = HIV_NEGATIVE):
    """
    Manages the addition of voluntary male medical circumcision (VMMC) reference tracking in the campaign.

    Args:
        campaign (emod_api.campaign): The campaign to which the VMMC reference tracking is to be added.
        vmmc_time_value_map (dict): A dictionary containing time-value map for VMMC.
        vmmc_reduced_acquire (float, optional): The reduced acquire rate for VMMC. Defaults to 0.6.
        vmmc_target_min_age (float, optional): The minimum age for VMMC target. Defaults to 15.
        vmmc_target_max_age (float, optional): The maximum age for VMMC target. Defaults to 29.999999.
        vmmc_start_year (float, optional): The start year for VMMC. Defaults to 2015.
        vmmc_node_ids (List[int], optional): A list of node IDs where the VMMC reference tracking is to be applied.
                                             Defaults to None, which applies to all nodes.
        update_period (float, optional): The update period for VMMC reference tracking. Defaults to 30.4166666666667.
        distributed_event_trigger (str, optional): The trigger for distributed event. Defaults to PROGRAM_VMMC.
        target_disease_state (str, optional): The target disease state for VMMC reference tracking. Defaults to HIV_NEGATIVE.

    Returns:
        str: The intervention name for male circumcision.

    Example:
        >>> add_vmmc_reference_tracking(campaign, vmmc_time_value_map={"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 500]}, vmmc_node_ids=[1, 2, 3], vmmc_reduced_acquire=0.5, vmmc_target_min_age=10, vmmc_target_max_age=30, vmmc_start_year=2010, update_period=30, distributed_event_trigger=PROGRAM_VMMC, target_disease_state=HIV_NEGATIVE)
    """
    start_day = timestep_from_year(vmmc_start_year, campaign.base_year)
    malecirc_intervention_name = ANY_MC
    distribute_circumcision = malecirc.new_intervention(campaign,
                                                        reduced_acquire=vmmc_reduced_acquire,
                                                        intervention_name=malecirc_intervention_name,
                                                        distributed_event=distributed_event_trigger)
    if 'Times' in vmmc_time_value_map:
        vmmc_time_value_map = convert_time_value_map(vmmc_time_value_map)
    add_reference_tracked_event(campaign, event_name='Reference tracking of VMMC',
                                out_iv=distribute_circumcision,
                                target_min_age=vmmc_target_min_age,
                                target_max_age=vmmc_target_max_age,
                                target_sex=MALE,
                                target_disease_state=target_disease_state,
                                time_value_map=vmmc_time_value_map,
                                update_period=update_period,
                                start_day=start_day,
                                node_ids=vmmc_node_ids)
    return malecirc_intervention_name


def add_historical_vmmc_nchooser(campaign: emod_api.campaign,
                                 historical_vmmc_distributions_by_time: pd.DataFrame,
                                 historical_vmmc_reduced_acquire: float = 0.6,
                                 historical_vmmc_property_restrictions: List[str] = None,
                                 historical_vmmc_start_year: float = 2008,
                                 historical_vmmc_node_ids: Union[List[int], None] = None,
                                 has_intervention_name_exclusion: str = ANY_MC,
                                 event_name='nchooser of VMMC'):
    """
    Adds voluntary male medical circumcision (VMMC) with NChooser coordinator to the campaign.
    This is used to add historical VMMC events to the campaign.

    Args:
        campaign (emod_api.campaign): The campaign to which the historical VMMC management is to be added.
        historical_vmmc_distributions_by_time (pd.DataFrame): A DataFrame containing the distributions of historical VMMC by time.
        historical_vmmc_reduced_acquire (float, optional): The reduced acquire rate for historical VMMC. Defaults to 0.6.
        historical_vmmc_property_restrictions (List[str], optional): A list of property restrictions for historical VMMC. Defaults to None.
        historical_vmmc_start_year (float, optional): The start year for historical VMMC. Defaults to 2008.
        historical_vmmc_node_ids (List[int], optional): A list of node IDs where the historical VMMC management is to be applied.
                                                         Defaults to None, which applies to all nodes.
        has_intervention_name_exclusion (str, optional): The name of the intervention to look for in an individual when
                                                         targeting specific disease states. It's also the
                                                         Intervention_Name of the MaleCircumcision intervention. Defaults to ANY_MC,
                                                         to match the intervention name in add_traditional_vmmc() and add_vmmc_reference_tracking().
        event_name (str, optional): The name of the event. Defaults to 'nchooser of VMMC'.

    Returns:
        None

    Example:
        >>> data = {'year': [2010, 2010, 2011, 2011],
        >>>         'min_age': [1, 15, 1, 15],
        >>>         'max_age': [14.999, 49.999, 14.999, 49.999],
        >>>         'n_circumcisions': [200, 1300, 290, 1490]}
        >>> historical_vmmc_distributions_by_time = pd.DataFrame.from_dict(data)
        >>> add_historical_vmmc_nchooser(campaign,
        >>>                              historical_vmmc_distributions_by_time=historical_vmmc_distributions_by_time,
        >>>                              historical_vmmc_reduced_acquire=0.5,
        >>>                              historical_vmmc_property_restrictions=None,
        >>>                              historical_vmmc_start_year=2007,
        >>>                              historical_vmmc_node_ids=[1, 2, 3],
        >>>                              has_intervention_name_exclusion=ANY_MC)
    """

    if historical_vmmc_property_restrictions is None:
        historical_vmmc_property_restrictions = []
    start_day = timestep_from_year(historical_vmmc_start_year, campaign.base_year)
    nchooser.add_nchooser_distributed_circumcision_event(campaign,
                                                         target_disease_state=[[HIV_NEGATIVE, NOT_HAS_INTERVENTION]],
                                                         has_intervention_name_exclusion=has_intervention_name_exclusion,
                                                         distributions=historical_vmmc_distributions_by_time,
                                                         property_restrictions=historical_vmmc_property_restrictions,
                                                         circumcision_reduced_acquire=historical_vmmc_reduced_acquire,
                                                         distributed_event_trigger=PROGRAM_VMMC,
                                                         start_day=start_day,
                                                         event_name=event_name,
                                                         node_ids=historical_vmmc_node_ids)


def add_health_care_testing(campaign: emod_api.campaign,
                            hct_node_ids: Union[List[int], None] = None,
                            hct_start_year: float = 1990,
                            hct_reentry_rate: float = 1,
                            hct_retention_rate: float = 0.95,
                            hct_delay_to_next_test: Union[int, List[int]] = None,
                            hct_delay_to_next_test_node_ids: Union[List[int], None] = None,
                            hct_delay_to_next_test_node_names: Union[List[str], None] = None,
                            tvmap_test_for_enter_HCT_testing_loop: dict = all_negative_time_value_map,
                            tvmap_consider_immediate_ART: dict = all_negative_time_value_map):
    """
    Manages the addition of health care testing in the campaign.

    Args:
      campaign (emod_api.campaign): The campaign to which the health care testing is to be added.
      hct_node_ids (List[int], optional): A list of node IDs where the health care testing is to be applied.
                                           Defaults to None, which applies to all nodes.
      hct_start_year (float, optional): The start year for health care testing. Defaults to 1990.
      hct_reentry_rate (float, optional): The reentry rate for health care testing. Defaults to 1.
      hct_retention_rate (float, optional): The retention rate for health care testing. Defaults to 0.95.
      hct_delay_to_next_test (Union[int, List[int]], optional): The delay to the next test in days. If it's a list, it
        will add different delays(using HIVMuxer) for different node sets which are defined in
        hct_delay_to_next_test_node_ids. If it's a single value, it will apply the same delay to all nodes in
        hct_node_ids. Defaults to None, which will apply the Zambia model default values: [730, 365, 1100].
      hct_delay_to_next_test_node_ids (List[int], optional): A list of node sets where the different delays will be
        applied. It's used when hct_delay_to_next_test is a list. Defaults to None, which will apply the Zambia
        model default values: [[1, 2, 3, 4, 6, 7], [5, 9, 10], [8]].
      hct_delay_to_next_test_node_names (List[str], optional): A list of node set names where the different delays will be
        applied. It's used when hct_delay_to_next_test is a list. Defaults to None, which will apply the Zambia
        model default values: ['Default', 'Lusaka, Southern, Western', 'Northern'].
      tvmap_test_for_enter_HCT_testing_loop (dict, optional): A dictionary containing time-value map for testing for
        entering HCT testing loop in HCTUptakePostDebut state. Defaults to all_negative_time_value_map.
      tvmap_consider_immediate_ART (dict, optional): A dictionary containing time-value map for considering immediate ART
        in HCTTestingLoop state. Defaults to all_negative_time_value_map.

    Returns:
      None

    Example:
        >>> add_health_care_testing(
        >>>     campaign,
        >>>     hct_node_ids=[1, 2, 3],
        >>>     hct_start_year=1995,
        >>>     hct_reentry_rate=0.9,
        >>>     hct_retention_rate=0.85,
        >>>     hct_delay_to_next_test=365
        >>> )
    """
    start_day = timestep_from_year(hct_start_year, campaign.base_year)
    disqualifying_properties = [CascadeState.LOST_FOREVER,
                                CascadeState.ON_ART,
                                CascadeState.LINKING_TO_ART,
                                CascadeState.ON_PRE_ART,
                                CascadeState.LINKING_TO_PRE_ART,
                                CascadeState.ART_STAGING]

    add_state_HCTUptakeAtDebut(campaign=campaign,
                               disqualifying_properties=disqualifying_properties,
                               node_ids=hct_node_ids,
                               start_day=start_day)

    add_state_HCTUptakePostDebut(campaign=campaign,
                                 disqualifying_properties=disqualifying_properties,
                                 node_ids=hct_node_ids,
                                 hct_reentry_rate=hct_reentry_rate,
                                 start_day=start_day,
                                 tvmap_test_for_enter_HCT_testing_loop=tvmap_test_for_enter_HCT_testing_loop)

    if hct_delay_to_next_test is None:
        hct_delay_to_next_test = [730, 365, 1100]  # Default values for Zambia model
    if hct_delay_to_next_test_node_ids is None:
        hct_delay_to_next_test_node_ids = [[1, 2, 3, 4, 6, 7], [5, 9, 10], [8]]  # Default values for Zambia model
    if hct_delay_to_next_test_node_names is None:
        hct_delay_to_next_test_node_names = ['Default', 'Lusaka, Southern, Western', 'Northern']  # Default values for Zambia model
    add_state_HCTTestingLoop(campaign=campaign,
                             disqualifying_properties=disqualifying_properties,
                             node_ids=hct_node_ids,
                             hct_retention_rate=hct_retention_rate,
                             start_day=start_day,
                             tvmap_consider_immediate_ART=tvmap_consider_immediate_ART,
                             hct_delay_to_next_test=hct_delay_to_next_test,
                             hct_delay_to_next_test_node_ids=hct_delay_to_next_test_node_ids,
                             hct_delay_to_next_test_node_names=hct_delay_to_next_test_node_names)


def add_ART_cascade(campaign: emod_api.campaign,
                    art_cascade_node_ids: Union[List[int], None] = None,
                    art_cascade_start_year: float = 1990,
                    art_cascade_pre_staging_retention: float = 0.85,
                    art_cascade_cd4_retention_rate: float = 1,
                    art_cascade_pre_art_retention: float = 0.75,
                    art_cascade_immediate_art_rate: float = 0.1,
                    art_cascade_art_reenrollment_willingness: float = 0.9,
                    tvmap_increased_symptomatic_presentation: dict = all_negative_time_value_map,
                    tvmap_immediate_ART_restart: dict = all_negative_time_value_map,
                    tvmap_reconsider_lost_forever: dict = all_negative_time_value_map):
    """
    Manages the addition of Antiretroviral Therapy (ART) cascade in the campaign.

    Args:
       campaign (emod_api.campaign): The campaign to which the ART cascade is to be added.
       art_cascade_node_ids (List[int], optional): A list of node IDs where the ART cascade is to be applied.
                                                   If None, the ART cascade applies to all nodes. Defaults to None.
       art_cascade_start_year (float, optional): The start year for the ART cascade. Defaults to 1990.
       art_cascade_pre_staging_retention (float, optional): The retention rate before ART staging. Defaults to 0.85.
       art_cascade_cd4_retention_rate (float, optional): The retention rate for CD4 count. Defaults to 1.
       art_cascade_pre_art_retention (float, optional): The retention rate before ART. Defaults to 0.75.
       art_cascade_immediate_art_rate (float, optional): The rate for immediate ART. Defaults to 0.1.
       art_cascade_art_reenrollment_willingness (float, optional): The willingness rate for ART reenrollment. Defaults to 0.9.
       tvmap_increased_symptomatic_presentation (dict, optional): A dictionary containing time-value map for increased
         symptomatic presentation in TestingOnSymptomatic state. Defaults to all_negative_time_value_map.
       tvmap_immediate_ART_restart (dict, optional): A dictionary containing time-value map for immediate ART restart in
         OnART state. Defaults to all_negative_time_value_map.
       tvmap_reconsider_lost_forever (dict, optional): A dictionary containing time-value map for reconsidering lost
         forever in LostForever state. Defaults to all_negative_time_value_map.

    Returns:
       None

    Example:
       >>> add_ART_cascade(campaign, art_cascade_node_ids=[1, 2, 3], art_cascade_start_year=1995, art_cascade_pre_staging_retention=0.8, art_cascade_cd4_retention_rate=0.9, art_cascade_pre_art_retention=0.7, art_cascade_immediate_art_rate=0.15, art_cascade_art_reenrollment_willingness=0.85)
    """
    start_day = timestep_from_year(art_cascade_start_year, campaign.base_year)
    disqualifying_properties = [CascadeState.LOST_FOREVER,
                                CascadeState.ON_ART,
                                CascadeState.LINKING_TO_ART,
                                CascadeState.ON_PRE_ART,
                                CascadeState.LINKING_TO_PRE_ART]

    disqualifying_properties_plus_art_staging = disqualifying_properties + [CascadeState.ART_STAGING]

    add_state_TestingOnSymptomatic(campaign=campaign,
                              node_ids=art_cascade_node_ids,
                              disqualifying_properties=disqualifying_properties_plus_art_staging,
                              start_day=start_day,
                              tvmap_increased_symptomatic_presentation=tvmap_increased_symptomatic_presentation)

    #
    # BEGIN ART STAGING SECTION
    #

    add_state_ARTStagingDiagnosticTest(campaign=campaign,
                                       node_ids=art_cascade_node_ids,
                                       disqualifying_properties=disqualifying_properties,
                                       start_day=start_day)

    add_state_ARTStaging(campaign=campaign,
                         cd4_retention_rate=art_cascade_cd4_retention_rate,
                         pre_staging_retention=art_cascade_pre_staging_retention,
                         node_ids=art_cascade_node_ids,
                         disqualifying_properties=disqualifying_properties,
                         start_day=start_day)

    #
    # END ART STAGING SECTION
    #

    #
    # BEGIN PRE-ART
    #

    # chance of linking to pre-ART
    # QUESTION: should we exclude CascadeState:LinkingToPreART, too?
    disqualifying_properties_pre_art_linking = [CascadeState.LOST_FOREVER,
                                                CascadeState.ON_ART,
                                                CascadeState.LINKING_TO_ART,
                                                CascadeState.ON_PRE_ART]

    add_state_LinkingToPreART(campaign=campaign,
                              node_ids=art_cascade_node_ids,
                              disqualifying_properties=disqualifying_properties_pre_art_linking,
                              start_day=start_day)

    # ensuring each agent continues this cascade once per timestep
    disqualifying_properties_pre_art = [CascadeState.LOST_FOREVER,
                                        CascadeState.ON_ART,
                                        CascadeState.LINKING_TO_ART]
    add_state_OnPreART(campaign=campaign,
                       node_ids=art_cascade_node_ids,
                       pre_art_retention=art_cascade_pre_art_retention,
                       disqualifying_properties=disqualifying_properties_pre_art,
                       start_day=start_day)

    #
    # END PRE-ART
    #

    #
    # BEGIN ART LINKING
    #

    art_linking_disqualifying_properties = [CascadeState.LOST_FOREVER, CascadeState.ON_ART]
    add_state_LinkingToART(campaign=campaign,
                           node_ids=art_cascade_node_ids,
                           disqualifying_properties=art_linking_disqualifying_properties,
                           start_day=start_day)

    # decide to initiate ART now or later
    disqualifying_properties_art = [CascadeState.LOST_FOREVER]
    add_state_OnART(campaign=campaign,
                    art_reenrollment_willingness=art_cascade_art_reenrollment_willingness,
                    immediate_art_rate=art_cascade_immediate_art_rate,
                    node_ids=art_cascade_node_ids,
                    disqualifying_properties=disqualifying_properties_art,
                    start_day=start_day,
                    tvmap_immediate_ART_restart=tvmap_immediate_ART_restart,
                    tvmap_reconsider_lost_forever=tvmap_reconsider_lost_forever)
    #
    add_state_LostForever(campaign=campaign, node_ids=art_cascade_node_ids, start_day=start_day)


def add_state_TestingOnANC(campaign: emod_api.campaign,
                           disqualifying_properties: List[str],
                           coverage: float,
                           link_to_ART_rate: float,
                           node_ids: Union[List[int], None],
                           sigmoid_ramp_max: float,
                           sigmoid_ramp_midyear: float,
                           sigmoid_ramp_min: float,
                           sigmoid_ramp_rate: float,
                           treatment_a_efficacy: float,
                           treatment_b_efficacy: float,
                           sdNVP_efficacy: float,
                           start_day: int,
                           property_restrictions: Union[List[str], str] = 'Accessibility:Yes') -> str:
    """

    Manages the addition of Testing on Antenatal Care (ANC) in the campaign.

    This state is triggered when an individual reaches 'TwelveWeeksPregnant'. At some point in this state, it initiates
    the ARTStaging state. The transition to the ARTStaging state is governed by an event, identified as
    ART_STAGING_TRIGGER_1. The occurrence of this event is determined by a random choice mechanism with a rate equal to
    link_to_ART_rate.

    Args:
        campaign (emod_api.campaign): The campaign object to which the Testing on ANC state is to be added.
        disqualifying_properties (List[str]): A list of disqualifying properties for the Testing on ANC state.
        coverage (float): The coverage of Testing on ANC among the population.
        link_to_ART_rate (float): The rate for linking to ART. This is used to determine the transition to the
            ARTStaging state.
        node_ids (Union[List[int], None]): A list of node IDs where the Testing on ANC state is to be applied. If
            None, the Testing on ANC state applies to all nodes.
        sigmoid_ramp_max (float): The right asymptote for the sigmoid trend over time for the
            HIVSigmoidByYearAndSexDiagnostic intervention.
        sigmoid_ramp_midyear (float): The time of the infection point in the sigmoid trend over time for the
            HIVSigmoidByYearAndSexDiagnostic intervention.
        sigmoid_ramp_min (float): The left asymptote for the sigmoid trend over time for the
            HIVSigmoidByYearAndSexDiagnostic intervention.
        sigmoid_ramp_rate (float): The slope of the inflection point in the sigmoid trend over time for the
            HIVSigmoidByYearAndSexDiagnostic intervention. A Rate of 1 sets the slope to a 25% change in probability
            per year.
        treatment_a_efficacy (float): The efficacy of treatment A.
        treatment_b_efficacy (float): The efficacy of treatment B.
        sdNVP_efficacy (float): The efficacy of Single-Dose Nevirapine (sdNVP).
        start_day (int): The start day for the Testing on ANC state.
        property_restrictions (Union[List[str], str], optional): The property restrictions for the Testing on ANC state.
            Defaults to 'Accessibility:Yes'.

    Returns:
        str: The trigger event name for the ARTStaging state.

    """
    initial_trigger = TWELVE_WEEKS_PREGNANT
    if not isinstance(property_restrictions, list):
        property_restrictions = [property_restrictions]
    testing_on_ANC_pv = CascadeState.TESTING_ON_ANC
    # PMTCT HIV diagnostic test availability by time
    need_pmtct_disgnostic_test_event = 'Needs_PMTCT_Diagnostic_Test'
    diagnostic_availability = sigmoiddiag.new_diagnostic(campaign,
                                                         Positive_Event=need_pmtct_disgnostic_test_event,
                                                         Negative_Event='None',
                                                         ramp_min=sigmoid_ramp_min,
                                                         ramp_max=sigmoid_ramp_max,
                                                         ramp_midyear=sigmoid_ramp_midyear,
                                                         ramp_rate=sigmoid_ramp_rate,
                                                         disqualifying_properties=disqualifying_properties,
                                                         new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='Availability of PMTCT diagnostic test',
                        in_trigger=initial_trigger, out_iv=[diagnostic_availability],
                        coverage=coverage, target_sex=FEMALE, property_restrictions=property_restrictions,
                        node_ids=node_ids, start_day=start_day)
    # distributing PMTCT HIV diagnostic test
    hiv_positive_at_anc_event = 'HIV_Positive_at_ANC'
    pmtct_hiv_test = rapiddiag.new_diagnostic(campaign,
                                              Positive_Event=hiv_positive_at_anc_event,
                                              Negative_Event='None',
                                              disqualifying_properties=disqualifying_properties,
                                              new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='PMTCT diagnostic test',
                        in_trigger=need_pmtct_disgnostic_test_event, out_iv=[pmtct_hiv_test],
                        node_ids=node_ids, start_day=start_day)
    # Chance to enter ART post-positive result during ANC
    # QUESTION: should we send the signal ARTStaging2 instead? We already have a 0.8/0.2 dropout from PMTCT test here. Why double the chance to drop?
    choices = {ART_STAGING_TRIGGER_1: link_to_ART_rate,
               DUMMY_TRIGGER: round(1 - link_to_ART_rate, 7)}  # to get rid of floating point decimal issues
    link_to_ART_decision = randomchoice.new_diagnostic(campaign,
                                                       choices=choices,
                                                       disqualifying_properties=disqualifying_properties,
                                                       new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='Linking from PMTCT positive result to ART',
                        in_trigger=hiv_positive_at_anc_event, out_iv=[link_to_ART_decision],
                        node_ids=node_ids, start_day=start_day)
    # PMTCT treatment selection based on time
    needs_sdnvp_pmtct_event = 'Needs_sdNVP_PMTCT'
    needs_combination_pmtct_event = 'Needs_Combination_PMTCT'
    treatment_selection = sigmoiddiag.new_diagnostic(campaign,
                                                     Positive_Event=needs_sdnvp_pmtct_event,
                                                     Negative_Event=needs_combination_pmtct_event,
                                                     ramp_min=0,
                                                     ramp_max=1,
                                                     ramp_midyear=2008.4,
                                                     ramp_rate=-1,
                                                     disqualifying_properties=disqualifying_properties,
                                                     new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign,
                        event_name='ANC/PMTCT: Choose Single-Dose Nevirapine (sdNVP) or Combination (Option A/B)',
                        in_trigger=hiv_positive_at_anc_event, out_iv=[treatment_selection],
                        node_ids=node_ids, start_day=start_day)
    # PMTCT treatment with sdNVP
    sdNVP_treatment = pmtct.new_intervention(campaign, efficacy=sdNVP_efficacy)
    add_triggered_event(campaign, event_name='ANC/PMTCT: Less Effective PMTCT (sdNVP)',
                        in_trigger=needs_sdnvp_pmtct_event, out_iv=[sdNVP_treatment],
                        node_ids=node_ids, start_day=start_day)
    # PMTCT combination treatment selection
    time_value_map = convert_time_value_map({"Times": [2013.249], "Values": [1]})
    needs_option_a_event = 'Needs_Option_A'
    needs_option_b_event = 'Needs_Option_B'
    combination_treatment_selection = yearandsexdiag.new_diagnostic(campaign,
                                                                    Positive_Event=needs_option_b_event,
                                                                    Negative_Event=needs_option_a_event,
                                                                    TVMap=time_value_map,
                                                                    disqualifying_properties=disqualifying_properties,
                                                                    new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='ANC/PMTCT: Combination Option A or B?',
                        in_trigger=needs_combination_pmtct_event, out_iv=[combination_treatment_selection],
                        node_ids=node_ids, start_day=start_day)

    # PMTCT treatment with combination A
    pmtct_combination_treatment_A = pmtct.new_intervention(campaign, efficacy=treatment_a_efficacy)
    add_triggered_event(campaign, event_name='ANC/PMTCT (Option A)',
                        in_trigger=needs_option_a_event, out_iv=[pmtct_combination_treatment_A],
                        node_ids=node_ids, start_day=start_day)

    # PMTCT treatment with combination B
    pmtct_combination_treatment_B = pmtct.new_intervention(campaign, efficacy=treatment_b_efficacy)
    add_triggered_event(campaign, event_name='ANC/PMTCT (Option B)',
                        in_trigger=needs_option_b_event, out_iv=[pmtct_combination_treatment_B],
                        node_ids=node_ids, start_day=start_day)

    return ART_STAGING_TRIGGER_1  # return the trigger for the ARTStaging state


def add_state_TestingOnChild6w(campaign: emod_api.campaign,
                               start_day: int,
                               disqualifying_properties: List[str],
                               time_value_map: Union[Dict[float, float], Dict[str, List[float]]],
                               node_ids: Union[List[int], None],
                               property_restrictions: Union[List[str], str] = 'Accessibility:Yes'):

    """
    This function adds a state for testing on children at 6 weeks old in the campaign.

    When an individual broadcast the 'SixWeeksOld' event, this state is triggered. If the test result is positive, it
    will then trigger the ARTStagingDiagnosticTest state using the event identified as ART_STAGING_DIAGNOSTIC_TEST_TRIGGER.

    Args:
        campaign (emod_api.campaign): The campaign to which the state is added.
        start_day (int): The start day for the state.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from the state.
        time_value_map (Union[Dict[float, float], Dict[str, List[float]]]): A map of times to values for the
            HIVPiecewiseByYearAndSexDiagnostic intervention.
        node_ids (Union[List[int], None]): A list of node IDs where the state is to be applied. If None, the state is
            applied to all nodes.
        property_restrictions (Union[List[str], str], optional): The property restrictions for the state. Defaults to
            'Accessibility:Yes'.

    Returns:
        str: The trigger event name for the ARTStagingDiagnosticTest state.
    """
    initial_trigger = SIX_WEEKS_OLD
    if not isinstance(property_restrictions, list):
        property_restrictions = [property_restrictions]
    testing_child_pv = CascadeState.TESTING_ON_CHILD_6W
    if 'Times' in time_value_map:
        time_value_map = convert_time_value_map(time_value_map)
    child_hiv_test = yearandsexdiag.new_diagnostic(campaign,
                                                   Positive_Event=ART_STAGING_DIAGNOSTIC_TEST_TRIGGER,
                                                   Negative_Event='None',
                                                   TVMap=time_value_map,
                                                   interpolation_order=1,
                                                   disqualifying_properties=disqualifying_properties,
                                                   new_property_value=testing_child_pv)
    add_triggered_event(campaign, event_name='CHILD 6W TESTING',
                        in_trigger=initial_trigger, out_iv=[child_hiv_test],
                        property_restrictions=property_restrictions,
                        node_ids=node_ids, start_day=start_day)
    return ART_STAGING_DIAGNOSTIC_TEST_TRIGGER  # return the trigger for the ARTStagingDiagnosticTest state


def add_state_HCTUptakeAtDebut(campaign: emod_api.campaign,
                               disqualifying_properties: List[str],
                               node_ids: Union[List[int], None],
                               start_day: int,
                               female_multiplier: float = 1) -> Tuple[str, str]:
    """
    This function manages the addition of Health Care Testing (HCT) uptake at sexual debut in the campaign.

    When an individual receives the 'STIDebut' event, this state is activated. If the test result is positive, it
    triggers the HCTTestingLoop state using the event identified as HCT_TESTING_LOOP_TRIGGER. If the test result is
    negative, it immediately triggers the HCTUpdatePostDebut state using the event identified as
    HCT_UPTAKE_POST_DEBUT_TRIGGER_1.

    Args:
        campaign (emod_api.campaign): The campaign to which the state is added.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from the state.
        node_ids (Union[List[int], None]): A list of node IDs where the state is to be applied. If None, the state is
            applied to all nodes.
        start_day (int): The start day for the state.
        female_multiplier (float, optional): The multiplier for female individuals in the
            HIVSigmoidByYearAndSexDiagnostic intervention. Defaults to 1.

    Returns:
        Tuple[str, str]: The trigger events for the HCTTestingLoop and HCTUpdatePostDebut states.
    """

    initial_trigger = CustomEvent.STI_DEBUT
    hct_upate_at_debut_pv = CascadeState.HCT_UPTAKE_AT_DEBUT
    # set up health care testing uptake at sexual debut by time
    uptake_choice = sigmoiddiag.new_diagnostic(campaign,
                                               Positive_Event=HCT_TESTING_LOOP_TRIGGER,
                                               Negative_Event=HCT_UPTAKE_POST_DEBUT_TRIGGER_1,
                                               ramp_min=-0.005,
                                               ramp_max=0.05,
                                               ramp_midyear=2005,
                                               ramp_rate=1,
                                               female_multiplier=female_multiplier,
                                               disqualifying_properties=disqualifying_properties,
                                               new_property_value=hct_upate_at_debut_pv)
    add_triggered_event(campaign, event_name='HCTUptakeAtDebut: state 0 (decision, sigmoid by year and sex)',
                        in_trigger=initial_trigger, out_iv=[uptake_choice],
                        property_restrictions=['Accessibility:Yes'],
                        node_ids=node_ids, start_day=start_day)
    return (HCT_TESTING_LOOP_TRIGGER,  # return the trigger for the HCTTestingLoop state
            HCT_UPTAKE_POST_DEBUT_TRIGGER_1)  # return the trigger for the HCTUpdatePostDebut state


def add_state_HCTUptakePostDebut(campaign: emod_api.campaign,
                                 disqualifying_properties: List[str],
                                 node_ids: Union[List[int], None],
                                 hct_reentry_rate: float,
                                 start_day: int,
                                 tvmap_test_for_enter_HCT_testing_loop: dict = all_negative_time_value_map) -> str:
    """
    This function manages the addition of Health Care Testing (HCT) uptake post sexual debut in the campaign.

    This state is activated by the events HCT_UPTAKE_POST_DEBUT_TRIGGER_1, HCT_UPTAKE_POST_DEBUT_TRIGGER_2, and
    HCT_UPTAKE_POST_DEBUT_TRIGGER_3. If the test result is positive, it triggers the HCTTestingLoop state using the
    event identified as HCT_TESTING_LOOP_TRIGGER. If the test result is negative, it reverts back to this state using
    the event identified as HCT_UPTAKE_POST_DEBUT_TRIGGER_1.

    Args:
        campaign (emod_api.campaign): The campaign to which the state is added.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from the state.
        node_ids (Union[List[int], None]): A list of node IDs where the state is to be applied. If None, the state is
            applied to all nodes.
        hct_reentry_rate (float): The rate at which individuals reenter the HCT uptake post sexual debut state.
        start_day (int): The start day for the state.
        tvmap_test_for_enter_HCT_testing_loop (dict, optional): Time value map for HIVPiecewiseByYearAndSexDiagnostic
            intervention. Defaults to all_negative_time_value_map which will always trigger the Negative event.

    Returns:
        str: The trigger for the HCTTestingLoop state.

    """
    hct_uptaek_post_debut_pv = CascadeState.HCT_UPTAKE_POST_DEBUT
    # These are the initial trigger of this state:
    hivmuxer_trigger = HCT_UPTAKE_POST_DEBUT_TRIGGER_1
    random_choice_trigger = [HCT_UPTAKE_POST_DEBUT_TRIGGER_2, HCT_UPTAKE_POST_DEBUT_TRIGGER_3]

    # used in this state only
    is_post_debut_trigger = CustomEvent.HCT_UPTAKE_POST_DEBUT_0

    # initialization of health care testing (hct) at specified starting year
    initialize_hct = hiv_utils.broadcast_event_immediate(campaign,
                                                         event_trigger=is_post_debut_trigger)
    hiv_utils.set_intervention_properties(initialize_hct, disqualifying_properties=disqualifying_properties,
                                          new_property_value=hct_uptaek_post_debut_pv)
    add_scheduled_event(campaign, event_name='HCTUptakePostDebut: HCT Uptake Initialization',
                        out_iv=[initialize_hct],
                        node_ids=node_ids, start_day=start_day)

    # reentry into uptake loop from lost-to-followup and ART dropout
    # QUESTION: ask... should this be HCTUptakePostDebut1 **1** ?? (can someone be non-debut and artdropout or ltfu? (maybe exposed children??)
    choices = {is_post_debut_trigger: hct_reentry_rate, DUMMY_TRIGGER: round(1 - hct_reentry_rate, 7)} # to get rid of floating point decimal issues
    reentry_decision = randomchoice.new_diagnostic(campaign,
                                                   choices=choices,
                                                   new_property_value=hct_uptaek_post_debut_pv)
    add_triggered_event(campaign,
                        event_name='HCTUptakePostDebut: state 3 (From LTFU or ART dropout back into HCT uptake loop)',
                        in_trigger=random_choice_trigger, out_iv=[reentry_decision],
                        node_ids=node_ids, start_day=start_day)

    # ensure that everyone who is entering the health care testing system is post-debut (this is a filter: must be
    # post-debut to proceed)
    is_post_debut_check = stipostdebut.new_diagnostic(campaign,
                                                      Positive_Event=hivmuxer_trigger,
                                                      Negative_Event='None')
    add_triggered_event(campaign, event_name='Ensure HCTUptakePostDebut0 agents are post-debut',
                        in_trigger=is_post_debut_trigger, out_iv=[is_post_debut_check],
                        node_ids=node_ids, start_day=start_day)

    # Up-to 1-year delay before an agent makes further decisions on making further hct uptake decisions
    # used in this state only
    sigmoiddiag_trigger = CustomEvent.HCT_UPTAKE_POST_DEBUT_2
    disqualifying_properties_plus_hct_loop = disqualifying_properties + [CascadeState.HCT_TESTING_LOOP]
    delay_to_uptake_decision = hivmuxer.new_intervention(camp,
                                                         muxer_name='HCTUptakePostDebut',
                                                         delay_complete_event=sigmoiddiag_trigger,
                                                         delay_distribution='EXPONENTIAL_DISTRIBUTION',
                                                         delay_period_exponential=365,
                                                         disqualifying_properties=disqualifying_properties_plus_hct_loop,
                                                         new_property_value=hct_uptaek_post_debut_pv)
    add_triggered_event(campaign, event_name=f'{hivmuxer_trigger}: state 1 (1-year delay, reachable)',
                        in_trigger=hivmuxer_trigger, out_iv=[delay_to_uptake_decision],
                        property_restrictions=['Accessibility=Yes'],
                        node_ids=node_ids, start_day=start_day)

    # decision on hct uptake
    # used in this state only
    consider_enter_HCT_testing_loop_trigger = CustomEvent.HCT_UPTAKE_POST_DEBUT_7
    uptake_decision = sigmoiddiag.new_diagnostic(campaign,
                                                 Positive_Event=HCT_TESTING_LOOP_TRIGGER,
                                                 Negative_Event=consider_enter_HCT_testing_loop_trigger,
                                                 ramp_min=-0.01,
                                                 ramp_max=0.15,
                                                 ramp_midyear=2006,
                                                 ramp_rate=1,
                                                 disqualifying_properties=disqualifying_properties_plus_hct_loop,
                                                 new_property_value=hct_uptaek_post_debut_pv
                                                 )
    add_triggered_event(campaign, event_name='HCTUptakePostDebut: state 2 (Decision to uptake HCT)',
                        in_trigger=sigmoiddiag_trigger, out_iv=[uptake_decision],
                        property_restrictions=['Accessibility=Yes'],
                        node_ids=node_ids, start_day=start_day)

    # if test negative in previous step, get an HIVPiecewiseByYearAndSexDiagnostic test and consider entering the hct
    # testing loop if test positive, if test negative, trigger hivmuxer again.
    consider_enter_HCT_testing_loop = yearandsexdiag.new_diagnostic(
        campaign,
        Positive_Event=HCT_TESTING_LOOP_TRIGGER,
        Negative_Event=hivmuxer_trigger,
        TVMap=tvmap_test_for_enter_HCT_testing_loop,
        disqualifying_properties=disqualifying_properties_plus_hct_loop,
        new_property_value=hct_uptaek_post_debut_pv)
    add_triggered_event(campaign, event_name='Consider enter HCT testing loop if test positive post debut, if test '
                                             'negative, trigger hivmuxer again.',
                        in_trigger=consider_enter_HCT_testing_loop_trigger, out_iv=[consider_enter_HCT_testing_loop],
                        node_ids=node_ids, start_day=start_day)
    return HCT_TESTING_LOOP_TRIGGER  # return the trigger for the HCTTestingLoop state


def add_state_HCTTestingLoop(campaign: emod_api.campaign,
                             disqualifying_properties: List[str],
                             node_ids: Union[List[int], None],
                             hct_retention_rate: float,
                             start_day: int,
                             hct_delay_to_next_test: Union[int, List[int]],
                             hct_delay_to_next_test_node_ids: Union[List[List[int]], None] = None,
                             hct_delay_to_next_test_node_names: Union[List[str], None] = None,
                             tvmap_consider_immediate_ART:dict = all_negative_time_value_map) -> (str, str, str):
    """
    This function manages the addition of Health Care Testing (HCT) testing loop in the campaign.

    This state is triggered by the HCT_TESTING_LOOP_TRIGGER event. Initially, it goes through a hivmuxer intervention
    with an exponential delay, the mean of which equals hct_delay_to_next_test. Subsequently, a rapid HIV test is
    conducted. If the test result is positive, a 'consider_immediate_ART' test is triggered. If the test result is
    negative, a random choice intervention is triggered to decide whether the individual should remain in the loop
    (with rate = hct_retention_rate) or drop out and transition to the HCTUptakePostDebut state using the
    HCT_UPTAKE_POST_DEBUT_TRIGGER_1 event. If the 'consider_immediate_ART' test is positive, it triggers the transition
    to the OnART state using the ON_ART_TRIGGER_2 event. If the 'consider_immediate_ART' test is negative, it triggers
    the transition to the ARTStaging state using the ART_STAGING_TRIGGER_1 event.

    Args:
        campaign (emod_api.campaign): The campaign to which the state is added.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from the state.

        node_ids (Union[List[int], None]): A list of node IDs where the state is to be applied. If None, the state is
            applied to all nodes.
        hct_retention_rate (float): The rate at which individuals remain in the HCT testing loop in the random choice
            intervention.
        start_day (int): The start day for the state.
        hct_delay_to_next_test (Union[int, List[int]]): The mean delay for the hivmuxer intervention in the HCT testing
            loop. Can be a single value or a list of values for different nodes.
        hct_delay_to_next_test_node_ids (Union[List[List[int]], None], optional): A 2D list specifying the node IDs for
            each delay period in the hivmuxer intervention. This argument must be provided if hct_delay_to_next_test is
            a list and should have the same length as hct_delay_to_next_test. If None, the node IDs will be the same as
            the previous node_ids argument. Defaults to None.
        hct_delay_to_next_test_node_names (Union[List[str], None], optional): A list of node names for each delay period
            in the hivmuxer intervention. This argument must be provided if hct_delay_to_next_test is a list and should
            have the same length as hct_delay_to_next_test. If None, the node names will be 'Default'. Defaults to None.
        tvmap_consider_immediate_ART (dict, optional): Time value map for considering immediate ART. Defaults to
            all_negative_time_value_map which will always trigger the Negative event and transition to ARTStaging state.

    Returns:
        Tuple[str, str, str]: The triggers for the HCTUptakePostDebut, OnART, and ARTStaging states.

    Examples:
        This example demonstrates how to add the HCTTestingLoop state to the campaign with different delay periods for each
        region/node

        >>> disqualifying_properties = [CascadeState.LOST_FOREVER,
        >>>                             CascadeState.ON_ART,
        >>>                             CascadeState.LINKING_TO_ART,
        >>>                             CascadeState.ON_PRE_ART,
        >>>                             CascadeState.LINKING_TO_PRE_ART,
        >>>                             CascadeState.ART_STAGING]
        >>> hct_retention_rate = 0.95
        >>> hct_delay_to_next_test = [730, 365, 1100]
        >>> hct_delay_to_next_test_node_ids = [[1, 2, 3, 4, 6, 7], [5, 9, 10], [8]]
        >>> hct_delay_to_next_test_node_names = ['Default', 'Lusaka, Southern, Western', 'Northern']
        >>> art_cascade_start_day = 10767
        >>> add_state_HCTTestingLoop(campaign=camp,
        >>>                          disqualifying_properties=disqualifying_properties,
        >>>                          hct_delay_to_next_test=hct_delay_to_next_test,
        >>>                          node_ids=None,
        >>>                          hct_retention_rate=hct_retention_rate,
        >>>                          start_day=art_cascade_start_day,
        >>>                          tvmap_consider_immediate_ART=all_negative_time_value_map,
        >>>                          hct_delay_to_next_test_node_ids=hct_delay_to_next_test_node_ids,
        >>>                          hct_delay_to_next_test_node_names=hct_delay_to_next_test_node_names))

        This example demonstrates how to add the HCTTestingLoop state to the campaign with a single delay period for all
        regions/nodes.
        >>> disqualifying_properties = [CascadeState.LOST_FOREVER,
        >>>                             CascadeState.ON_ART,
        >>>                             CascadeState.LINKING_TO_ART,
        >>>                             CascadeState.ON_PRE_ART,
        >>>                             CascadeState.LINKING_TO_PRE_ART,
        >>>                             CascadeState.ART_STAGING]
        >>> hct_retention_rate = 0.95
        >>> hct_delay_to_next_test = 365
        >>> art_cascade_start_day = 10767
        >>> add_state_HCTTestingLoop(campaign=camp,
        >>>                          disqualifying_properties=disqualifying_properties,
        >>>                          hct_delay_to_next_test=hct_delay_to_next_test,
        >>>                          node_ids=None,
        >>>                          hct_retention_rate=hct_retention_rate,
        >>>                          start_day=art_cascade_start_day,
        >>>                          tvmap_consider_immediate_ART=all_negative_time_value_map)
    """
    hct_testing_loop_pv = CascadeState.HCT_TESTING_LOOP

    initial_trigger = HCT_TESTING_LOOP_TRIGGER
    # testing loop -- delay until next test, please note that this is an exponential delay distribution
    diagnostic_trigger = CustomEvent.HCT_TESTING_LOOP_1
    if isinstance(hct_delay_to_next_test, int):
        hct_delay_to_next_test = [hct_delay_to_next_test]
        if hct_delay_to_next_test_node_ids is None:
            hct_delay_to_next_test_node_ids = [node_ids]
        if hct_delay_to_next_test_node_names is None:
            hct_delay_to_next_test_node_names = ['Default']
    elif isinstance(hct_delay_to_next_test, list):
        if (not isinstance(hct_delay_to_next_test_node_ids, list) or
                not isinstance(hct_delay_to_next_test_node_names, list)):
            raise ValueError("hct_delay_to_next_test_node_ids and hct_delay_to_next_test_node_names must be provided "
                             "if hct_delay_to_next_test is a list.")
        elif (len(hct_delay_to_next_test) != len(hct_delay_to_next_test_node_ids) or
              len(hct_delay_to_next_test) != len(hct_delay_to_next_test_node_names)):
            raise ValueError("hct_delay_to_next_test, hct_delay_to_next_test_node_ids, and "
                             "hct_delay_to_next_test_node_names must have the same length.")
    else:
        raise ValueError("hct_delay_to_next_test must be an int or a list of int.")
    for delay_period, delay_node_ids, node_name in zip(hct_delay_to_next_test, hct_delay_to_next_test_node_ids,
                                                       hct_delay_to_next_test_node_names):
        delay_to_next_hct = hivmuxer.new_intervention(campaign,
                                                      muxer_name='HCTTestingLoop',
                                                      delay_complete_event=diagnostic_trigger,
                                                      delay_distribution='EXPONENTIAL_DISTRIBUTION',
                                                      delay_period_exponential=delay_period,
                                                      disqualifying_properties=disqualifying_properties,
                                                      new_property_value=hct_testing_loop_pv)
        add_triggered_event(campaign, event_name=f'HCTTestingLoop: state 0 (delay to next HCT): {node_name}',
                            in_trigger=initial_trigger, out_iv=[delay_to_next_hct],
                            node_ids=delay_node_ids, start_day=start_day)
    # testing loop -- hct hiv test
    randomchoice_trigger = CustomEvent.HCT_TESTING_LOOP_2
    yearandsexdiag_trigger = CustomEvent.ART_STAGING_9
    hiv_test = rapiddiag.new_diagnostic(campaign,
                                        Positive_Event=yearandsexdiag_trigger,
                                        Negative_Event=randomchoice_trigger,
                                        disqualifying_properties=disqualifying_properties,
                                        new_property_value=hct_testing_loop_pv)
    add_triggered_event(campaign, event_name='HCTTestingLoop: state 1 (HIV rapid diagnostic)',
                        in_trigger=diagnostic_trigger, out_iv=[hiv_test],
                        node_ids=node_ids, start_day=start_day)

    # testing loop -- hct retention -- stay in loop or dropout
    choices = {initial_trigger: hct_retention_rate, HCT_UPTAKE_POST_DEBUT_TRIGGER_1: round(1 - hct_retention_rate, 7)}  # to get rid of floating point decimal issues
    retention_decision = randomchoice.new_diagnostic(campaign,
                                                     choices=choices,
                                                     disqualifying_properties=disqualifying_properties,
                                                     new_property_value=hct_testing_loop_pv)
    add_triggered_event(campaign, event_name='HCTTestingLoop: state 2 (HCT Testing retention/dropout)',
                        in_trigger=randomchoice_trigger, out_iv=[retention_decision],
                        node_ids=node_ids, start_day=start_day)

    # Consider immediate ART in HCT loop, no further testing for eligibility or potential waiting. Or go to ART staging.
    consider_immediate_ART = yearandsexdiag.new_diagnostic(campaign,
                                                           Positive_Event=ON_ART_TRIGGER_2,
                                                           Negative_Event=ART_STAGING_TRIGGER_1,
                                                           TVMap=tvmap_consider_immediate_ART,
                                                           disqualifying_properties=disqualifying_properties,
                                                           new_property_value=hct_testing_loop_pv)
    add_triggered_event(campaign, event_name='Consider immediate ART (after 2016?)',
                        in_trigger=yearandsexdiag_trigger, out_iv=[consider_immediate_ART],
                        node_ids=node_ids, start_day=start_day)
    return (HCT_UPTAKE_POST_DEBUT_TRIGGER_1,  # return the trigger for the HCTUptakePostDebut state
            ON_ART_TRIGGER_2,  # return the trigger for the OnART state
            ART_STAGING_TRIGGER_1)  # return the trigger for the ARTStaging state


def add_state_TestingOnSymptomatic(campaign: emod_api.campaign,
                                   node_ids: Union[List[int], None],
                                   disqualifying_properties: List[str],
                                   start_day: int,
                                   tvmap_increased_symptomatic_presentation: dict = all_negative_time_value_map) -> (
        Tuple)[str, str]:
    """
    This function manages the addition of Testing on Symptomatic individuals in the campaign.

    This state is triggered when an individual becomes 'NewlySymptomatic'. A HIVSigmoidByYearAndSexDiagnostic
    intervention is then applied.
    If the test result is positive, it triggers the ARTStagingDiagnosticTest state using the
    ART_STAGING_DIAGNOSTIC_TEST_TRIGGER event.
    If the test is negative, it triggers a HIVPiecewiseByYearAndSexDiagnostic test. If the result of this test is
    positive, it initiates the ARTStaging state through the ART_STAGING_TRIGGER_2 event. If the test result is negative,
    it does not trigger any further events.

    Args:
        campaign (emod_api.campaign): The campaign to which the state is added.
        node_ids (Union[List[int], None]): A list of node IDs where the state is to be applied. If None, the state is
            applied to all nodes.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from the state.
        start_day (int): The start day for the state.
        tvmap_increased_symptomatic_presentation (dict, optional): Time value map for increased symptomatic presentation
            which is used in the HIVPiecewiseByYearAndSexDiagnostic intervention. Defaults to
            all_negative_time_value_map which will always trigger the Negative event('None').

    Returns:
        Tuple[str, str]: The triggers for the ARTStagingDiagnosticTest and ARTStaging states.
    """
    """
    When the 'NewlySymptomatic' event occurs, this state is initiated. The sigmoiddiag intervention is then applied. If
    the test result is positive, it triggers the ARTStagingDiagnosticTest state via the
    ART_STAGING_DIAGNOSTIC_TEST_TRIGGER event. However, if the sigmoiddiag test is negative, it triggers a
    yearandsexdiag test and if the result is positive, it initiates the ARTStaging state through the ART_STAGING_TRIGGER_2 event.
    """
    # presentation of symptoms leading to HIV testing
    testing_on_symptomatic_pv = CascadeState.TESTING_ON_SYMPTOMATIC
    initial_trigger = NEWLY_SYMPTOMATIC
    yearandsexdiag_trigger = CustomEvent.ART_STAGING_8
    probability_of_symptoms = sigmoiddiag.new_diagnostic(campaign,
                                                         Positive_Event=ART_STAGING_DIAGNOSTIC_TEST_TRIGGER,
                                                         Negative_Event=yearandsexdiag_trigger,
                                                         ramp_min=0.25,
                                                         ramp_max=0.9,
                                                         ramp_midyear=2002,
                                                         ramp_rate=0.5,
                                                         disqualifying_properties=disqualifying_properties,
                                                         new_property_value=testing_on_symptomatic_pv)
    add_triggered_event(campaign, event_name='TestingOnSymptomatic: state 0 (Presentation probability)',
                        in_trigger=initial_trigger, out_iv=[probability_of_symptoms],
                        node_ids=node_ids, start_day=start_day)

    # Consider increased symptomatic presentation at some point
    #  Note: the following yearandsexdiag has 0 values in TVMap in Zambia model, which means the 'ARTStaging8'
    #  that triggers this test which will always return negative. Right now the Negative_event is 'None', which means
    #  it goes nowhere.
    increased_symptomatic_presentation = yearandsexdiag.new_diagnostic(campaign,
                                                                       Positive_Event=ART_STAGING_TRIGGER_2,  # this is the hivmuxer trigger in ARTStaging
                                                                       Negative_Event='None',
                                                                       TVMap=tvmap_increased_symptomatic_presentation,
                                                                       disqualifying_properties=disqualifying_properties,
                                                                       new_property_value=testing_on_symptomatic_pv)
    add_triggered_event(campaign, event_name='Consider increased symptomatic presentation (after 2016?)',
                        in_trigger=yearandsexdiag_trigger, out_iv=[increased_symptomatic_presentation],
                        node_ids=node_ids, start_day=start_day)
    return (ART_STAGING_DIAGNOSTIC_TEST_TRIGGER,  # return the trigger for the ARTStagingDiagnosticTest state
            ART_STAGING_TRIGGER_2)  # return the trigger for the ARTStaging state


def add_state_ARTStagingDiagnosticTest(campaign,
                                       node_ids: Union[List[int], None],
                                       disqualifying_properties: List[str],
                                       start_day: int) -> str:
    """
    This function manages the addition of ART Staging Diagnostic Test in the campaign.

    This state is triggered by the ART_STAGING_DIAGNOSTIC_TEST_TRIGGER event. Upon activation, it conducts an HIV
    rapid diagnostic test on individuals who present with symptoms. If the test result is positive, it triggers the
    transition to the ARTStaging state using the ART_STAGING_TRIGGER_1 event.

    Args:
        campaign: The campaign to which the state is added.
        node_ids (Union[List[int], None]): A list of node IDs where the state is to be applied. If None, the state is
            applied to all nodes.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from the state.
        start_day (int): The start day for the state.

    Returns:
        str: The trigger for the ARTStaging state.
    """
    # HIV testing of those who present with symptoms
    art_staging_diagnostic_test_pv = CascadeState.ART_STAGING_DIAGNOSTIC_TEST

    initial_trigger = ART_STAGING_DIAGNOSTIC_TEST_TRIGGER
    hiv_test = rapiddiag.new_diagnostic(campaign,
                                        Positive_Event=ART_STAGING_TRIGGER_1,
                                        Negative_Event='None',
                                        disqualifying_properties=disqualifying_properties,
                                        # People will left in this state(CascadeState.ART_STAGING_DIAGNOSTIC_TEST) if they are tested negative.
                                        new_property_value=art_staging_diagnostic_test_pv)
    add_triggered_event(campaign, event_name='ART Staging: state 0 (HIV rapid diagnostic)',
                        in_trigger=initial_trigger, out_iv=[hiv_test],
                        node_ids=node_ids, start_day=start_day)
    return ART_STAGING_TRIGGER_1  # return the trigger for the ARTStaging state


def add_state_ARTStaging(campaign: emod_api.campaign,
                         cd4_retention_rate: float,
                         pre_staging_retention: float,
                         node_ids: Union[List[int], None],
                         disqualifying_properties: List[str],
                         start_day: int
                         ):
    """
    This function manages the addition of the ART Staging state in the campaign.

    This state is initially triggered by the ART_STAGING_TRIGGER_1 and ART_STAGING_TRIGGER_2 events. Upon activation,
    it conducts a series of interventions and diagnostics, including blood draw, ART eligibility check, and CD4 count
    check. Depending on the results of these checks, the function can trigger transitions to several different states.

    Args:
        campaign (emod_api.campaign): The campaign to which the state is added.
        cd4_retention_rate (float): The retention rate for CD4.
        pre_staging_retention (float): The retention rate before staging.
        node_ids (Union[List[int], None]): A list of node IDs where the state is to be applied. If None, the state is
            applied to all nodes.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from the state.
        start_day (int): The start day for the state.

    Returns:
        Tuple[str, str, str, str]: The triggers for the LinkingToART, LinkingToPreART, HCTUptakePostDebut states for
        individuals who are not eligible for ART from the randomchoice, and HCTUptakePostDebut state for individuals
        who are lost to follow-up (LTFU).
    """
    art_staging_pv = CascadeState.ART_STAGING

    initial_trigger = ART_STAGING_TRIGGER_1  # 'ARTStaging1'
    hivmuxer_trigger = ART_STAGING_TRIGGER_2  # 'ARTStaging2'

    # these events are used within this function, but not returned
    drawblood_trigger    = CustomEvent.ART_STAGING_3
    cd4diag_trigger      = CustomEvent.ART_STAGING_4
    randomchoice_trigger = CustomEvent.ART_STAGING_5
    cd4_retention_choice = CustomEvent.ART_STAGING_6

    # chance to return for blood draw
    choices = {hivmuxer_trigger: pre_staging_retention,
               HCT_UPTAKE_POST_DEBUT_TRIGGER_2: round(1 - pre_staging_retention, 7)}  # hct_update_post_debut_choice # to get rid of floating point decimal issues
    prestaging_retention = randomchoice.new_diagnostic(campaign,
                                                       choices=choices,
                                                       disqualifying_properties=disqualifying_properties,
                                                       new_property_value=art_staging_pv)
    add_triggered_event(campaign,
                        event_name='ARTStaging: state 1 (random choice: linking from positive diagnostic test)',
                        in_trigger=initial_trigger, out_iv=[prestaging_retention],
                        node_ids=node_ids, start_day=start_day)
    # ensuring each agent continues testing in this cascade once per timestep
    muxer = hivmuxer.new_intervention(campaign,
                                      muxer_name='ARTStaging',
                                      delay_complete_event=drawblood_trigger,
                                      delay_distribution='CONSTANT_DISTRIBUTION',
                                      delay_period_constant=1,
                                      disqualifying_properties=disqualifying_properties,
                                      new_property_value=art_staging_pv)
    add_triggered_event(campaign, event_name='ARTStaging: state 2 (Muxer to make sure only one entry per DT)',
                        in_trigger=hivmuxer_trigger, out_iv=[muxer],
                        node_ids=node_ids, start_day=start_day)
    # perform blood draw
    draw_blood = drawblood.new_diagnostic(campaign,
                                          Positive_Event=cd4diag_trigger,
                                          disqualifying_properties=disqualifying_properties,
                                          new_property_value=art_staging_pv)
    add_triggered_event(campaign, event_name='ARTStaging: state 3 (draw blood)',
                        in_trigger=drawblood_trigger, out_iv=[draw_blood],
                        node_ids=node_ids, start_day=start_day)
    # TODO from Clark: move this into an input data file and read?
    # CD4 agnostic ART eligibility check
    adult_by_pregnant = convert_time_value_map({"Times": [2002, 2013.95], "Values": [0, 1]})
    adult_by_TB = convert_time_value_map({"Times": [2002], "Values": [1]})
    adult_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})
    child_treat_under_age_in_years_threshold = convert_time_value_map({"Times": [2002, 2013.95], "Values": [5, 15]})
    child_by_TB = convert_time_value_map({"Times": [2002, 2010.5], "Values": [0, 1]})
    child_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})
    art_eligibility = artstagingbycd4agnosticdiag.new_diagnostic(campaign,
                                                                 Positive_Event=LINKING_TO_ART_TRIGGER,
                                                                 Negative_Event=randomchoice_trigger,
                                                                 abp_tvmap=adult_by_pregnant,
                                                                 abt_tvmap=adult_by_TB,
                                                                 abw_tvmap=adult_by_WHO_stage,
                                                                 cua_tvmap=child_treat_under_age_in_years_threshold,
                                                                 cbt_tvmap=child_by_TB,
                                                                 cbw_tvmap=child_by_WHO_stage,
                                                                 disqualifying_properties=disqualifying_properties,
                                                                 new_property_value=art_staging_pv)
    add_triggered_event(campaign, event_name='ARTStaging: state 4 (check eligibility for ART, CD4 agnostic)',
                        in_trigger=cd4diag_trigger, out_iv=[art_eligibility],
                        node_ids=node_ids, start_day=start_day)
    # if NOT eligible for ART without checking CD4, decide to return for CD4 test or lost-to-followup (LTFU)
    choices = {cd4_retention_choice: cd4_retention_rate,
               HCT_UPTAKE_POST_DEBUT_TRIGGER_3: round(1 - cd4_retention_rate, 7)}  # lost_to_followup (LTFU) # to get rid of floating point decimal issues
    cd4_retention = randomchoice.new_diagnostic(campaign,
                                                choices=choices,
                                                disqualifying_properties=disqualifying_properties,
                                                new_property_value=art_staging_pv)
    add_triggered_event(campaign, event_name='ARTStaging: state 5 (random choice: Return for CD4 or LTFU)',
                        in_trigger=randomchoice_trigger, out_iv=[cd4_retention],
                        node_ids=node_ids, start_day=start_day)
    # determine if eligible for ART given CD4 counts
    # TODO from Clark: move this into an input data file and read?
    cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 500]})
    pregnant_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 2000]})
    active_TB_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5], "Values": [200, 2000]})
    art_eligibility_by_cd4 = artstagingbycd4diag.new_diagnostic(campaign,
                                                                Positive_Event=LINKING_TO_ART_TRIGGER,
                                                                Negative_Event=LINKING_TO_PRE_ART_TRIGGER,
                                                                Threshold_TVMap=cd4_threshold,
                                                                IP_TVMap=pregnant_cd4_threshold,
                                                                IAT_TVMap=active_TB_cd4_threshold,
                                                                disqualifying_properties=disqualifying_properties,
                                                                new_property_value=art_staging_pv)
    add_triggered_event(campaign, event_name='ARTStaging: state 6 (check eligibility for ART by CD4)',
                        in_trigger=cd4_retention_choice, out_iv=[art_eligibility_by_cd4],
                        node_ids=node_ids, start_day=start_day)

    return (LINKING_TO_ART_TRIGGER,  # return the trigger for the LinkingToART state
            LINKING_TO_PRE_ART_TRIGGER,  # return the trigger for the LinkingToPreART state
            HCT_UPTAKE_POST_DEBUT_TRIGGER_2,  # return the trigger for the HCTUptakePostDebut state from peolpe who are not eligible for ART from the randomchoice
            HCT_UPTAKE_POST_DEBUT_TRIGGER_3)  # return the trigger for the HCTUptakePostDebut state from lost-to-followup (LTFU)


def add_state_LinkingToPreART(campaign: emod_api.campaign,
                              node_ids: Union[List[int], None],
                              disqualifying_properties: List[str],
                              start_day: int) -> Tuple[str, str]:
    """
    This function manages the addition of the LinkingToPreART state in the campaign.

    The function is initially triggered by the LINKING_TO_PRE_ART_TRIGGER event. Upon activation, it conducts a
    HIVSigmoidByYearAndSexDiagnostic test. If the test result is positive, it triggers ON_PRE_ART_TRIGGER which will
    transition to the OnPreART state. If the test result is negative, it triggers HCT_UPTAKE_POST_DEBUT_TRIGGER_3 which
    will transition to the HCTUptakePostDebut state.

    Args:
        campaign (emod_api.campaign): The campaign object to which the state is added.
        node_ids (Union[List[int], None]): A list of node IDs for which the state is applicable. If None, the state is
            applicable to all nodes.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from being in this
            state.
        start_day (int): The day on which the state starts.

    Returns:
        Tuple[str, str]: The triggers for the OnPreART and HCTUptakePostDebut states.

    """
    linking_to_pre_art_pv = CascadeState.LINKING_TO_PRE_ART
    initial_trigger = LINKING_TO_PRE_ART_TRIGGER

    link_decision = sigmoiddiag.new_diagnostic(campaign,
                                               Positive_Event=ON_PRE_ART_TRIGGER,
                                               Negative_Event=HCT_UPTAKE_POST_DEBUT_TRIGGER_3,
                                               ramp_min=0.7572242198,
                                               ramp_max=0.9591484679,
                                               ramp_midyear=2006.8336631523,
                                               ramp_rate=1,
                                               female_multiplier=1.5,
                                               disqualifying_properties=disqualifying_properties,
                                               new_property_value=linking_to_pre_art_pv)
    add_triggered_event(campaign, event_name='LinkingToPreART: state 0 (Linking probability)',
                        in_trigger=initial_trigger, out_iv=[link_decision],
                        node_ids=node_ids, start_day=start_day)
    return (ON_PRE_ART_TRIGGER,  # return the trigger for the OnPreART state
            HCT_UPTAKE_POST_DEBUT_TRIGGER_3)  # return the trigger for the HCTUptakePostDebut state from people who are not eligible for ART


def add_state_OnPreART(campaign: emod_api.campaign,
                       node_ids: Union[List[int], None],
                       pre_art_retention: float,
                       disqualifying_properties: List[str],
                       start_day: int) -> Tuple[str, str]:
    """
    This function manages the addition of the OnPreART state in the campaign.

    The function is initially triggered by the ON_PRE_ART_TRIGGER event. Upon activation, it conducts a series of
    interventions and diagnostics, including a HIVMuxer with a delay period, a random choice for pre-ART retention or
    lost to follow-up, a CD4 agnostic pre-ART eligibility check, a blood draw, and a determination of ART eligibility
    given CD4 counts. Depending on the results of these checks, the function can transit to two different states.
    It could trigger the OnART state if the individual is eligible for ART with ON_ART_TRIGGER_1 event. It could also
    trigger the HCTUptakePostDebut state if the individual is not retained in the pre-ART state with
    HCT_UPTAKE_POST_DEBUT_TRIGGER_3 event.

    Args:
        campaign (emod_api.campaign): The campaign object to which the state is added.
        node_ids (Union[List[int], None]): A list of node IDs for which the state is applicable. If None, the state is
            applicable to all nodes.
        pre_art_retention (float): The retention rate in the pre-ART state.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from being in this
            state.
        start_day (int): The day on which the state starts.

    Returns:
        Tuple[str, str]: The triggers for the OnART and HCTUptakePostDebut states.


    """
    on_pre_art_pv = CascadeState.ON_PRE_ART

    initial_trigger = ON_PRE_ART_TRIGGER

    # these events are used within this function, but not returned
    randomchoice_trigger           = CustomEvent.ON_PRE_ART_1
    art_staging_cd4_diag_trigger   = CustomEvent.ON_PRE_ART_2
    drawblood_trigger              = CustomEvent.ON_PRE_ART_3
    drawblood_positive             = CustomEvent.ON_PRE_ART_4
    muxer = hivmuxer.new_intervention(campaign,
                                      muxer_name='PreART',
                                      delay_complete_event=randomchoice_trigger,
                                      delay_distribution='CONSTANT_DISTRIBUTION',
                                      delay_period_constant=182,
                                      disqualifying_properties=disqualifying_properties,
                                      new_property_value=on_pre_art_pv)
    add_triggered_event(campaign, event_name='OnPreART: state 0 (muxer, 182-day delay)',
                        in_trigger=initial_trigger, out_iv=[muxer],
                        node_ids=node_ids, start_day=start_day)
    # decision to continue to pre-ART or lost to followup (LTFU)
    choices = {art_staging_cd4_diag_trigger: pre_art_retention,
               HCT_UPTAKE_POST_DEBUT_TRIGGER_3: round(1 - pre_art_retention, 7)}  # to get rid of floating point decimal issues
    pre_ART_retention = randomchoice.new_diagnostic(campaign,
                                                    choices=choices,
                                                    disqualifying_properties=disqualifying_properties,
                                                    new_property_value=on_pre_art_pv)
    add_triggered_event(campaign, event_name='OnPreART: state 1 (random choice: pre-ART or LTFU)',
                        in_trigger=randomchoice_trigger, out_iv=[pre_ART_retention],
                        node_ids=node_ids, start_day=start_day)
    # TODO from Clark: move this into an input data file and read?
    # CD4 agnostic pre-ART eligibility check
    adult_by_pregnant = convert_time_value_map({"Times": [2002, 2013.95], "Values": [0, 1]})
    adult_by_TB = convert_time_value_map({"Times": [2002], "Values": [1]})
    adult_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})
    child_treat_under_age_in_years_threshold = convert_time_value_map({"Times": [2002, 2013.95], "Values": [5, 15]})
    child_by_TB = convert_time_value_map({"Times": [2002, 2010.5], "Values": [0, 1]})
    child_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})
    pre_art_eligibility = artstagingbycd4agnosticdiag.new_diagnostic(campaign,
                                                                     Positive_Event=ON_ART_TRIGGER_1,
                                                                     Negative_Event=drawblood_trigger,
                                                                     abp_tvmap=adult_by_pregnant,
                                                                     abt_tvmap=adult_by_TB,
                                                                     abw_tvmap=adult_by_WHO_stage,
                                                                     cua_tvmap=child_treat_under_age_in_years_threshold,
                                                                     cbt_tvmap=child_by_TB,
                                                                     cbw_tvmap=child_by_WHO_stage,
                                                                     disqualifying_properties=disqualifying_properties,
                                                                     new_property_value=on_pre_art_pv)
    add_triggered_event(campaign, event_name='OnPreART: state 2 (check eligibility for ART, CD4 agnostic)',
                        in_trigger=art_staging_cd4_diag_trigger, out_iv=[pre_art_eligibility],
                        node_ids=node_ids, start_day=start_day)
    # perform blood draw, pre-ART
    draw_blood = drawblood.new_diagnostic(campaign,
                                          Positive_Event=drawblood_positive,
                                          disqualifying_properties=disqualifying_properties,
                                          new_property_value=on_pre_art_pv)
    add_triggered_event(campaign, event_name='OnPreART: state 3 (draw blood)',
                        in_trigger=drawblood_trigger, out_iv=[draw_blood],
                        node_ids=node_ids, start_day=start_day)
    # TODO from Clark: note that the ART and pre-ART cascades have a different order for retention, is this right?? Explore/verify then ask.
    # determine if eligible for ART given CD4 counts
    # TODO from Clark: move this into an input data file and read?
    cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 500]})
    pregnant_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 2000]})
    active_TB_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5], "Values": [200, 2000]})
    art_eligibility_by_cd4 = artstagingbycd4diag.new_diagnostic(campaign,
                                                                Positive_Event=ON_ART_TRIGGER_1,
                                                                Negative_Event=initial_trigger,
                                                                Threshold_TVMap=cd4_threshold,
                                                                IP_TVMap=pregnant_cd4_threshold,
                                                                IAT_TVMap=active_TB_cd4_threshold,
                                                                disqualifying_properties=disqualifying_properties,
                                                                new_property_value=on_pre_art_pv)
    add_triggered_event(campaign, event_name='OnPreART: state 4 (check eligibility for ART by CD4)',
                        in_trigger=drawblood_positive, out_iv=[art_eligibility_by_cd4],
                        node_ids=node_ids, start_day=start_day)

    return (ON_ART_TRIGGER_1,  # return the trigger for the OnART state
            HCT_UPTAKE_POST_DEBUT_TRIGGER_3)  # return the trigger for the HCTUptakePostDebut state


def add_state_LinkingToART(campaign: emod_api.campaign,
                           node_ids: Union[List[int], None],
                           disqualifying_properties: List[str],
                           start_day: int,
                           ramp_min: float = 0,
                           ramp_max: float = 0.8507390283,
                           ramp_midyear: float = 1997.4462231708,
                           ramp_rate: float = 1
                           ):
    """
    This function manages the addition of the LinkingToART state in the campaign.

    The function is initially triggered by the LINKING_TO_ART_TRIGGER event. Upon activation, it conducts a sigmoid
    HIVSigmoidByYearAndSexDiagnostic test. Depending on the result of this test, the function can transit to two
    different states. It could trigger the OnART state if the sigmoid diagnostic test result is positive with
    ON_ART_TRIGGER_1 event. It could also trigger the HCTUptakePostDebut state if the sigmoid diagnostic test result is
    negative with HCT_UPTAKE_POST_DEBUT_TRIGGER_2 event.

    Args:
        campaign (emod_api.campaign): The campaign object to which the state is added.
        node_ids (Union[List[int], None]): A list of node IDs for which the state is applicable. If None, the state is
            applicable to all nodes.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from being in this
            state.
        start_day (int): The day on which the state starts.
        ramp_min (float): The minimum value of the sigmoid ramp in HIVSigmoidByYearAndSexDiagnostic intervention. Defaults to 0.
        ramp_max (float): The maximum value of the sigmoid ramp in HIVSigmoidByYearAndSexDiagnostic intervention. Defaults to 0.8507390283.
        ramp_midyear (float): The midyear value of the sigmoid ramp in HIVSigmoidByYearAndSexDiagnostic intervention. Defaults to 1997.4462231708.
        ramp_rate (float): The rate of the sigmoid ramp in HIVSigmoidByYearAndSexDiagnostic intervention. Defaults to 1.

    Returns:
        Tuple[str, str]: The triggers for the OnART and 'HCTUptakePostDebut' states.
    """
    linking_to_art_pv = CascadeState.LINKING_TO_ART

    initial_trigger = LINKING_TO_ART_TRIGGER

    # ART linking probability by time
    art_linking_probability = sigmoiddiag.new_diagnostic(campaign,
                                                         Positive_Event=ON_ART_TRIGGER_1,
                                                         Negative_Event=HCT_UPTAKE_POST_DEBUT_TRIGGER_2,
                                                         ramp_min=ramp_min,
                                                         ramp_max=ramp_max,
                                                         ramp_midyear=ramp_midyear,
                                                         ramp_rate=ramp_rate,
                                                         disqualifying_properties=disqualifying_properties,
                                                         new_property_value=linking_to_art_pv)
    add_triggered_event(campaign, event_name='LinkingToART: state 0 (Linking probability)',
                        in_trigger=initial_trigger, out_iv=[art_linking_probability],
                        node_ids=node_ids, start_day=start_day)
    return (ON_ART_TRIGGER_1,  # return the trigger for the OnART state
            HCT_UPTAKE_POST_DEBUT_TRIGGER_2)  # return the trigger for the HCTUptakePostDebut state


def add_state_OnART(campaign: emod_api.campaign,
                    art_reenrollment_willingness: float,
                    immediate_art_rate: float,
                    node_ids: Union[List[int], None],
                    disqualifying_properties: List[str],
                    start_day: int,
                    tvmap_immediate_ART_restart: dict = all_negative_time_value_map,
                    tvmap_reconsider_lost_forever: dict = all_negative_time_value_map):
    """
    This function manages the addition of the OnART state in the campaign.

    The function is initially triggered by the ON_ART_TRIGGER_1 and ON_ART_TRIGGER_2 events. Upon activation, it
    conducts a series of interventions and diagnostics, including a decision(with randomchoice) on whether to initiate
    ART immediately or delay(with HIVMuxer), initiation of ART, a delay(with HIVMuxer) to dropping off of ART, and a
    decision(with randomchoice) on willingness to test the eligibility of re-enroll in ART or transit to other states.

    Args:
        campaign (emod_api.campaign): The campaign object to which the state is added.
        art_reenrollment_willingness (float): The willingness of an individual to re-enroll in ART after dropout.
        immediate_art_rate (float): The rate at which ART is initiated immediately, without HIVMuxer delay.
        node_ids (Union[List[int], None]): A list of node IDs for which the state is applicable. If None, the state is
            applicable to all nodes.
        disqualifying_properties (List[str]): A list of properties that disqualify an individual from being in this
            state.
        start_day (int): The day on which the state starts.
        tvmap_immediate_ART_restart (dict): A time value map for HIVPiecewiseByYearAndSexDiagnostic intervention to
            consider restarting ART immediately after HIVmuxer delay. Defaults to all_negative_time_value_map which will
            always trigger the Negative event(HCT_UPTAKE_POST_DEBUT_TRIGGER_2) and transit to HCTUptakePostDebut state.
        tvmap_reconsider_lost_forever (dict): A time value map for the second HIVPiecewiseByYearAndSexDiagnostic
            intervention to reconsider being lost forever to ART care. Defaults to all_negative_time_value_map which
            will always trigger the Negative event(LostForever) and transit to LostForever state.

    Returns:
        Tuple[str, str]: The triggers for the HCTUptakePostDebut and LostForever states.
    """
    on_art_pv = CascadeState.ON_ART

    initial_trigger_randomchoice = ON_ART_TRIGGER_1
    initial_trigger_ART_hivmuxer = ON_ART_TRIGGER_2
    on_art_3_event = 'OnART3'
    art_initiation_delay_event = 'ARTInitiationDelayed'
    choices = {initial_trigger_ART_hivmuxer: immediate_art_rate,
               art_initiation_delay_event: round(1 - immediate_art_rate, 7)}  # to get rid of floating point decimal issues
    when_decision = randomchoice.new_diagnostic(campaign,
                                                choices=choices,
                                                disqualifying_properties=disqualifying_properties,
                                                new_property_value=on_art_pv)
    add_triggered_event(campaign, event_name='Delay to ART initiation: decide whether to initiate immediately or delay',
                        in_trigger=initial_trigger_randomchoice, out_iv=[when_decision],
                        node_ids=node_ids, start_day=start_day)
    # delay to ART initiation plus muxer to ensure agents only do it once at a time
    # Up-to 1-year delay before an agent makes further decisions on making further hct uptake decisions
    delay_to_art_initiation = hivmuxer.new_intervention(campaign,
                                                        muxer_name='OnART',
                                                        delay_complete_event=initial_trigger_ART_hivmuxer,
                                                        delay_distribution='WEIBULL_DISTRIBUTION',
                                                        delay_period_lambda=63.381,
                                                        delay_period_kappa=0.711,
                                                        disqualifying_properties=disqualifying_properties,
                                                        new_property_value=on_art_pv)
    add_triggered_event(campaign, event_name='OnART: state 0 (muxer and delay)',
                        in_trigger=art_initiation_delay_event, out_iv=[delay_to_art_initiation],
                        node_ids=node_ids, start_day=start_day)
    # initiate ART
    initiate_art = art.new_intervention(campaign)
    add_triggered_event(campaign, event_name='Initiate ART',
                        in_trigger=initial_trigger_ART_hivmuxer, out_iv=[initiate_art],
                        node_ids=node_ids, start_day=start_day)
    # delay to dropping off of ART + muxer to ensure drop-off once per agent/timestep
    art_dropout_delay = hivmuxer.new_intervention(campaign,
                                                  muxer_name='ARTDropoutDelay',
                                                  delay_complete_event=on_art_3_event,
                                                  delay_distribution='EXPONENTIAL_DISTRIBUTION',
                                                  delay_period_exponential=7300,
                                                  disqualifying_properties=disqualifying_properties,
                                                  new_property_value=on_art_pv)
    add_triggered_event(campaign, event_name='OnART: state 2 (delay to dropout)',
                        in_trigger=initial_trigger_ART_hivmuxer, out_iv=[art_dropout_delay],
                        node_ids=node_ids, start_day=start_day)
    # discontinue ART; dropout
    # QUESTION: do we need to change their CascadeState now that they're off ART?
    discontinue_ART = artdropout.new_intervention(campaign)
    add_triggered_event(campaign, event_name='OnART: state 3 (run ARTDropout)',
                        in_trigger=on_art_3_event, out_iv=[discontinue_ART],
                        node_ids=node_ids, start_day=start_day)
    # Willingness to re-enroll in ART after dropout
    ART_restart_test_choice = CustomEvent.HCT_UPTAKE_POST_DEBUT_8
    lostfoever_test_choice = CustomEvent.LOST_FOREVER_9
    choices = {ART_restart_test_choice: art_reenrollment_willingness,
               lostfoever_test_choice: round(1 - art_reenrollment_willingness, 7)}  # to get rid of floating point decimal issues
    willing_to_reenroll = randomchoice.new_diagnostic(campaign,
                                                      choices=choices,
                                                      disqualifying_properties=disqualifying_properties,
                                                      new_property_value=on_art_pv)
    add_triggered_event(campaign, event_name='OnART: state 4 (Willing to re-enroll in ART?)',
                        in_trigger=on_art_3_event, out_iv=[willing_to_reenroll],
                        node_ids=node_ids, start_day=start_day)

    # Note: the following 2 yearandsexdiag interventions have TVMap set to all negative values, which will always
    # trigger the Negative events and transit to HCTUptakePostDebut and LostForever states.

    # Consider restarting ART immediately after dropping off ART
    immediate_ART_restart = yearandsexdiag.new_diagnostic(campaign,
                                                          Positive_Event=initial_trigger_ART_hivmuxer,
                                                          Negative_Event=HCT_UPTAKE_POST_DEBUT_TRIGGER_2,
                                                          TVMap=tvmap_immediate_ART_restart,
                                                          disqualifying_properties=['CascadeState:LostForever'],
                                                          new_property_value='CascadeState:OnART')
    add_triggered_event(campaign, event_name='Consider not dropping (after 2016?)',
                        in_trigger=ART_restart_test_choice, out_iv=[immediate_ART_restart],
                        node_ids=node_ids, start_day=start_day)
    #
    # reconsider being lost forever to ART care
    reconsider_lost_forever = yearandsexdiag.new_diagnostic(campaign,
                                                            Positive_Event=initial_trigger_ART_hivmuxer,
                                                            Negative_Event=LOST_FOREVER_TRIGGER,
                                                            TVMap=tvmap_reconsider_lost_forever,
                                                            disqualifying_properties=['CascadeState:LostForever'],
                                                            new_property_value='CascadeState:OnART')
    add_triggered_event(campaign, event_name='Consider not lost forever (after 2016?)',
                        in_trigger=lostfoever_test_choice, out_iv=[reconsider_lost_forever],
                        node_ids=node_ids, start_day=start_day)
    return (HCT_UPTAKE_POST_DEBUT_TRIGGER_2,  # return the trigger for the HCTUptakePostDebut state
            LOST_FOREVER_TRIGGER)             # return the trigger for the LostForever state


def add_state_LostForever(campaign: emod_api.campaign, node_ids: Union[List[int], None], start_day: int):
    """
    Transition individuals to the 'LostForever' state in the campaign.

    This function is triggered by the LOST_FOREVER_TRIGGER event. Upon activation, it changes the target property
    key to 'CascadeState' and the target property value to 'LostForever', effectively moving individuals to the
    LostForever state in the campaign.

    Args:
        campaign (emod_api.campaign): The campaign object to which the state transition is to be added.
        node_ids (List[int]): A list of node IDs where this transition is applicable.
        start_day (int): The starting day of the campaign when this transition becomes active.

    """
    # Actually lost forever now
    initial_trigger = LOST_FOREVER_TRIGGER
    lost_forever = PropertyValueChanger(campaign,
                                        Target_Property_Key=CascadeState.LOST_FOREVER.split(':')[0],  # 'CascadeState'
                                        Target_Property_Value=CascadeState.LOST_FOREVER.split(':')[1],  # 'LostForever'
                                        )
    add_triggered_event(campaign, event_name='LostForever: state 0',
                        in_trigger=initial_trigger, out_iv=[lost_forever],
                        node_ids=node_ids, start_day=start_day)


# todo: making this function private for now, as it is not yet implemented
def _add_rtri_testing(campaign: emod_api.campaign,
                     rtri_node_ids: List[int] = None,
                     rtri_start_year: float = 2015,
                     rtri_testing_min_age: float = 15,
                     rtri_followup_rate: float = 1,
                     rtri_consent_rate: float = 1,
                     rtri_retesting_rate: float = 0.01):  # TODO: find a good starting value or just calibrate.
    raise NotImplementedError("This function is not yet implemented.")

    start_day = timestep_from_year(rtri_start_year, campaign.base_year)

    # Chance to follow-up a HIV+ result with an offer of a recency test
    # TODO: set these HIV+ test result triggers properly, they are ... confusing ... and some refactoring of their use may be needed
    triggers = ['retester_is_HIV+', 'HIV_Positive_at_ANC', 'ARTStaging9', 'ARTStaging1'] # TODO: update project json to have correct triggers, too (including the sending of the triggers, not just consumption). Verify/ask about all these triggers and e.g. double counting of blood draws for some.
    choices = {'RTRI_BEGIN_FOLLOWUP': rtri_followup_rate, 'RTRI_LOST_TO_FOLLOWUP': 1 - rtri_followup_rate}
    rtri_followup = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Received HIV+ test result. Followed up with an RTRI?',
                        in_trigger='ARTStaging9', out_iv=[rtri_followup],
                        node_ids=rtri_node_ids, start_day=start_day)

    # Determine if the person being offered a recency test is eligible (as known by person offering the test)
    rtri_eligible = hiv_utils.broadcast_event_immediate(campaign, event_trigger='RTRI_ELIGIBLE')
    add_triggered_event(campaign, event_name='Broadcast RTRI eligibility (eligible)',
                        in_trigger='RTRI_BEGIN_FOLLOWUP', out_iv=[rtri_eligible],
                        target_age_min=rtri_testing_min_age,
                        node_ids=rtri_node_ids, start_day=start_day)

    # Determine if the person being offered a recency test is NOT eligible (as known by person offering the test)
    rtri_ineligible = hiv_utils.broadcast_event_immediate(campaign, event_trigger='RTRI_INELIGIBLE')
    add_triggered_event(campaign, event_name='Broadcast RTRI eligibility (NOT eligible)',
                        in_trigger='RTRI_BEGIN_FOLLOWUP', out_iv=[rtri_ineligible],
                        target_age_max=rtri_testing_min_age - EPSILON,
                        node_ids=rtri_node_ids, start_day=start_day)

    # Chance to follow-up a HIV+ result with an offer of a recency test
    choices = {'RTRI_CONSENTED': rtri_consent_rate, 'RTRI_REFUSED': 1 - rtri_consent_rate}
    rtri_consent = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Check if person consents to an RTRI',
                        in_trigger='RTRI_ELIGIBLE', out_iv=[rtri_consent],
                        node_ids=rtri_node_ids, start_day=start_day)

    # Statistics of RTRI testing depends on whether an agent has been (truly) infected recently AND their ART history
    # Each agent tested qualifies for only one of four mutually exclusive test variations:
    # recently_infected AND has_been_on_ART
    # recently_infected AND NOT has_been_on_ART
    # NOT recently_infected AND has_been_on_ART
    # NOT recently_infected AND NOT has been_on_ART
    # We do not consider any case where an HIV- person is tested.

    # TODO: usage of this needs implementing. When done, update format of this argument being passed
    target_hiv_positive = {
        "Logic": [
            [{'class': 'IsHivPositive', "Is_Equal_To": 1}]
        ]
    }
    # RTRI test (1/4): recently_infected AND has_been_on_ART
    # TODO: set these probabilities properly
    choices = {'RTRI_TESTED_RECENT': 0.85, 'RTRI_TESTED_LONGTERM': 0.15}
    rtri_result = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Perform RTRI test (HIV+, recent, previous ART usage)',
                        in_trigger='RTRI_CONSENTED', out_iv=[rtri_result],
                        property_restrictions=["Recently_Infected:true", "Ever_Been_On_ART:true"],
                        targeting_logic=target_hiv_positive,
                        node_ids=rtri_node_ids, start_day=start_day)

    # RTRI test (2/4): recently_infected AND NOT has_been_on_ART
    # TODO: set these probabilities properly
    choices = {'RTRI_TESTED_RECENT': 0.8, 'RTRI_TESTED_LONGTERM': 0.2}
    rtri_result = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Perform RTRI test (HIV+, recent, NO previous ART usage)',
                        in_trigger='RTRI_CONSENTED', out_iv=[rtri_result],
                        property_restrictions=["Recently_Infected:true", "Ever_Been_On_ART:false"],
                        targeting_logic=target_hiv_positive,
                        node_ids=rtri_node_ids, start_day=start_day)

    # RTRI test (3/4): NOT recently_infected AND has_been_on_ART
    # TODO: set these probabilities properly
    choices = {'RTRI_TESTED_RECENT': 0.75, 'RTRI_TESTED_LONGTERM': 0.25}
    rtri_result = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Perform RTRI test (HIV+, longterm, previous ART usage)',
                        in_trigger='RTRI_CONSENTED', out_iv=[rtri_result],
                        property_restrictions=["Recently_Infected:false", "Ever_Been_On_ART:true"],
                        targeting_logic=target_hiv_positive,
                        node_ids=rtri_node_ids, start_day=start_day)

    # RTRI test (4/4): NOT recently_infected AND NOT has been_on_ART
    # TODO: set these probabilities properly
    choices = {'RTRI_TESTED_RECENT': 0.7, 'RTRI_TESTED_LONGTERM': 0.3}
    rtri_result = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Perform RTRI test (HIV+, longterm, NO previous ART usage)',
                        in_trigger='RTRI_CONSENTED', out_iv=[rtri_result],
                        property_restrictions=["Recently_Infected:false", "Ever_Been_On_ART:false"],
                        targeting_logic=target_hiv_positive,
                        node_ids=rtri_node_ids, start_day=start_day)

    #
    # Individual property management for infection recency, ART history, and (approximate) viral suppression
    #

    # all infections start out as recent
    recency_update = PropertyValueChanger(campaign,
                                          Target_Property_Key='Recently_Infected', Target_Property_Value='true')
    add_triggered_event(campaign, event_name='Infections start out recent, transitioning to longterm after 12 months',
                        in_trigger='NewInfectionEvent', out_iv=[recency_update],
                        node_ids=rtri_node_ids)

    # all people starting art are marked as having taking it at least once in their lives
    art_history_update = PropertyValueChanger(campaign,
                                              Target_Property_Key='Ever_Been_On_ART', Target_Property_Value='true')
    add_triggered_event(campaign, event_name='Record a person having been on ART at least once in their lives',
                        in_trigger='OnART1', out_iv=[art_history_update],
                        property_restrictions=['Ever_Been_On_ART:false'],
                        node_ids=rtri_node_ids)

    # all newly infected agents start out as virally unsuppressed
    suppression_update = PropertyValueChanger(campaign,
                                              Target_Property_Key='Virally_Suppressed', Target_Property_Value='false')
    add_triggered_event(campaign, event_name='Set viral suppression status to false upon infection (ignoring VL ramp-up time which is on the order of 1-2 months)',
                        in_trigger='NewInfectionEvent', out_iv=[suppression_update],
                        node_ids=rtri_node_ids)

    # agents who are on ART for 6 consecutive months are considered virally suppressed (a simplification)
    # TODO: usage of this needs implementing. When done, update format of this argument being passed
    target_on_ART_long_enough = {
        "Logic": [
            [{"class": "IsOnART", "Is_Equal_To": 1},
             {"class": "HasBeenOnArtMoreOrLessThanNumMonths", "More_Or_Less": "MORE", "Num_Months": 6}]
        ]
    }
    suppression_update = PropertyValueChanger(campaign,
                                              Target_Property_Key='Virally_Suppressed', Target_Property_Value='true')
    add_scheduled_event(campaign, event_name='Set viral suppression status to true after 6 consecutive months on ART',
                        out_iv=[suppression_update],
                        property_restrictions=['Virally_Suppressed:false'],
                        targeting_logic=target_on_ART_long_enough,
                        node_ids=rtri_node_ids)

    # set viral suppression to false upon ART dropout (a simplification)
    suppression_update = PropertyValueChanger(campaign,
                                              Target_Property_Key='Virally_Suppressed', Target_Property_Value='false')
    add_triggered_event(campaign, event_name='Set viral suppression status to false upon ART dropout (ignoring VL ramp-up time which is on the order of 1-2 months)',
                        in_trigger='OnART3', out_iv=[suppression_update],
                        node_ids=rtri_node_ids)

    # TODO: transition the existing campaign json (in actual project) to use drawblood instead of broadcast to match.
    # perform viral load testing to follow-up RTRI recent results (to confirm recency) (simply check viral load IP)
    # confirming recent infection
    vl_confirmation = drawblood.new_diagnostic(campaign, Positive_Event='REPORT_RECENT_INFECTION')
    add_triggered_event(campaign, event_name='Run VL test along with recent RTRI test result (reporting confirmed recent)',
                        in_trigger='RTRI_TESTED_RECENT', out_iv=[vl_confirmation],
                        property_restrictions=['Virally_Suppressed:false'],
                        node_ids=rtri_node_ids, start_day=start_day)

    # TODO: broadcast_event_immediate OR drawblood for this and the above event. Choose.
    # perform viral load testing to follow-up RTRI recent results (to confirm recency) (simply check viral load IP)
    # reclassify as longterm infection
    vl_confirmation = hiv_utils.broadcast_event_immediate(campaign, event_trigger='REPORT_LONGTERM_INFECTION')
    add_triggered_event(campaign, event_name='Run VL test along with recent RTRI test result (reporting longterm)',
                        in_trigger='RTRI_TESTED_RECENT', out_iv=[vl_confirmation],
                        property_restrictions=['Virally_Suppressed:true'],
                        node_ids=rtri_node_ids, start_day=start_day)

    # RTRI longterm results are never reclassified due to VL tests. We ignore RTRI test failure (RTRI-long, VL-unsuppressed).
    # simply report longterm infection
    vl_confirmation = hiv_utils.broadcast_event_immediate(campaign, event_trigger='REPORT_LONGTERM_INFECTION')
    add_triggered_event(campaign, event_name='Run VL test along with longterm RTRI test result (reporting longterm)',
                        in_trigger='RTRI_TESTED_LONGTERM', out_iv=[vl_confirmation],
                        node_ids=rtri_node_ids, start_day=start_day)

    # HIV/RTRI testing noise -- people don't always tell health care providers that they know they are HIV+, e.g., they
    # switch to a different health facility after moving and think they need a new HIV+ result to get a refill on their
    # ART medications. This event ensures there is a tunable fraction of the ART-history population HIV/RTRI testing
    # each timestep.
    # TODO: when should retesting start? probably before RTRI testing timeframe? Maybe once ART starts up?
    target_on_ART = {
        "Logic": [
            [{"class": "IsHivPositive", "Is_Equal_To": 1},
             {"class": "IsOnART", "Is_Equal_To": 1}]
        ],
    }
    retest_signal = hiv_utils.broadcast_event_immediate(campaign, event_trigger='HCTTestingLoop1--retesters')
    add_scheduled_event(campaign, event_name='Send people to test even if they are HIV+ and on ART. E.g., they might just be moving health facilities. Happens.',
                        out_iv=[retest_signal],
                        coverage=rtri_retesting_rate,
                        n_repetitions=-1,  # FOREVER
                        timesteps_between_repetitions=1,  # every timestep
                        targeting_logic=target_on_ART,
                        node_ids=rtri_node_ids, start_day=start_day)

    # HIV test for retesters (looser property restrictions compared to regular health care testing)
    # we target on-ART people here (again) to ensure that individuals who JUST went off of ART (but after broadcasting
    # HCTTestingLoop1--retesters) do not test. They have to wait until the next timestep, if they wish to retest.
    # distributing PMTCT HIV diagnostic test
    # TODO, QUESTION: should 'retesters' be considered 'presenting as symptomatic'? Ensure json is synced.
    # e.g. how will the health system treat them once they test HIV+ (again)?
    retester_hiv_test = rapiddiag.new_diagnostic(campaign,
                                                 Positive_Event='retester_is_HIV+',
                                                 Negative_Event='None',
                                                 disqualifying_properties=['CascadeState:LostForever'])
    add_triggered_event(campaign, event_name='HCTTestingLoop: state 1 (HIV rapid diagnostic) -- HIV+/OnART retesters',
                        in_trigger='HCTTestingLoop1--retesters', out_iv=[retester_hiv_test],
                        targeting_logic=target_on_ART,
                        node_ids=rtri_node_ids, start_day=start_day)


# todo: making this function private for now, as it is not yet implemented
def _add_index_testing(campaign: emod_api.campaign,
                      index_testing_triggers: List[str],
                      index_testing_node_ids: List[int] = None,
                      index_testing_start_year: float = 2015,
                      index_testing_partner_coverage: float = 0.5):  # TODO: definitely calibrate this!
    raise NotImplementedError("The index_testing_partner_coverage in this function is not yet implemented.")
    # TODO: add ALL of these campaign elements, when complete, to the original json version
    if index_testing_triggers is None:
        # QUESTION: are these right? Additionally, need to add retester_is_HIV+ in the campaign caller
        index_testing_triggers = ['HIV_Positive_at_ANC', 'ARTStaging9', 'ARTStaging1']
    start_day = timestep_from_year(index_testing_start_year, campaign.base_year)

    # Is a HIV+ test followed up with index testing offer by the health system?
    # TODO: set these probabilities properly
    choices = {'INDEX_TESTING_BEGIN_FOLLOWUP': 0.95, 'INDEX_TESTING_LOST_TO_FOLLOWUP': 0.05}
    index_testing_followup = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Follow-up newly diagnosed HIV+ individuals with index testing?',
                        in_trigger=index_testing_triggers, out_iv=[index_testing_followup],
                        node_ids=index_testing_node_ids, start_day=start_day)

    # Is the offer of index testing accepted?
    # TODO: set these probabilities properly
    choices = {'INDEX_TESTING_CONSENTED': 0.9, 'INDEX_TESTING_REFUSED': 0.1}
    index_testing_followup = randomchoice.new_diagnostic(campaign, choices=choices)
    add_triggered_event(campaign, event_name='Is an offer of index testing accepted by an individual?',
                        in_trigger='INDEX_TESTING_BEGIN_FOLLOWUP', out_iv=[index_testing_followup],
                        node_ids=index_testing_node_ids, start_day=start_day)

    # Actual event targeting partners: % coverage (calibrated) of their partners (of N_Partners) selected
    #   -> signal them.
    # TODO - talk with Dan B about this partner targeting
    index_testing_elicit_contacts = hiv_utils.broadcast_event_immediate(campaign,
                                                                        partner_coverage=index_testing_partner_coverage,
                                                                        event_trigger='ELICITED_CONTACT')
    add_triggered_event(campaign, event_name='Elicit contacts from index cases',
                        in_trigger='INDEX_TESTING_CONSENTED', out_iv=[index_testing_elicit_contacts],
                        node_ids=index_testing_node_ids, start_day=start_day)

    # partners: send them to HIV testing. QUESTION: Where exactly to link up in the CoC?
    # QUESTION = need to know which HIV test to send them to... HCT, prenatal (ha), symptomatic presentation, ...
    index_testing_contact_to_testing = hiv_utils.broadcast_event_immediate(campaign,
                                                                           partner_coverage=index_testing_partner_coverage,
                                                                           event_trigger='TODO:HIV_test_which_one')
    add_triggered_event(campaign, event_name='Sending elicited contacts/partners to testing',
                        in_trigger='ELICITED_CONTACT', out_iv=[index_testing_contact_to_testing],
                        node_ids=index_testing_node_ids, start_day=start_day)
