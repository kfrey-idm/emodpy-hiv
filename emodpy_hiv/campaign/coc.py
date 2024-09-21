# QUESTION: verify dead-labeled code is dead
import pandas as pd

from emodpy_hiv.interventions.cascade_helpers import *
import emodpy_hiv.interventions.utils as hiv_utils
from emodpy_hiv.interventions import (outbreak, sigmoiddiag, randomchoice, yearandsexdiag, rapiddiag, modcoinf, pmtct,
                                      malecirc, stipostdebut, nchooser, hivmuxer)

from emod_api.interventions.common import PropertyValueChanger


# property restrictions/disqualifying properties/new property values checked
from hiv_workflow.lib.utils.frames import timestep_from_year, EPSILON

from enum import Enum
from typing import List


def convert_time_value_map(time_value_map) -> dict:
    """
    Convert time_value_map to a dictionary with time as key and value as value
    Args:
        time_value_map: A dictionary with "Times" and "Values" keys

    Returns:
        A dictionary with time as key and value as value

    """
    time_value_map_convert = {}
    for time, value in zip(time_value_map["Times"], time_value_map["Values"]):
        time_value_map_convert[time] = value
    return time_value_map_convert


def seed_infections(campaign,
                    seeding_node_ids: List[int] = None,
                    seeding_start_year: float = 1982,
                    seeding_coverage: float = 0.075,
                    seeding_target_min_age: float = 0,
                    seeding_target_max_age: float = 200,
                    seeding_target_gender: str = "All",
                    seeding_target_property_restrictions: list = None) -> None:
    event_name = f"Epidemic seeding in node(s) {str(seeding_node_ids)}"
    event = outbreak.seed_infections(campaign,
                                     node_ids=seeding_node_ids,
                                     event_name=event_name,
                                     start_day=timestep_from_year(seeding_start_year, campaign.start_year),
                                     coverage=seeding_coverage,
                                     target_min_age=seeding_target_min_age,
                                     target_max_age=seeding_target_max_age,
                                     target_gender=seeding_target_gender,
                                     target_properties=seeding_target_property_restrictions)
    campaign.add(event)


# property restrictions/disqualifying properties/new property values checked
def add_csw(campaign, manifest,
            csw_node_ids: List[int] = None,
            csw_male_uptake_coverage: float = 0.03, csw_female_uptake_coverage: float = 0.03):
    # manages commercial sex worker uptake and dropout (with delays) for men and women

    debut_event = "STIDebut"
    uptake_event = "Commercial_Uptake"  # also serves as the dropout_delay_event
    dropout_event = "Commercial_Dropout"
    uptake_delay_event = "Commercial_DelayFromDebutToUptake"

    # determine if women will become sex FSW
    time_value_map = {campaign.start_year: csw_female_uptake_coverage}
    # time_value_map = {"Times": [campaign.start_year], "Values": [csw_female_uptake_coverage]}
    will_become_FSW = yearandsexdiag.new_diagnostic(campaign,
                                                    Positive_Event=uptake_delay_event,
                                                    Negative_Event='None',
                                                    TVMap=time_value_map,
                                                    interpolation_order=1)
    add_triggered_event(campaign, event_name=f"Will ever become FSW in node(s) {str(csw_node_ids)}",
                        in_trigger=debut_event, out_iv=[will_become_FSW],
                        target_sex='Female', node_ids=csw_node_ids)

    # Female delay to uptake
    female_delay_to_uptake = hiv_utils.broadcast_event_delayed(campaign,
                                                               event_trigger=uptake_event,
                                                               delay={"Delay_Period_Min": 0, "Delay_Period_Max": 1825})
    add_triggered_event(campaign, event_name=f"Commercial Sex (Female): Delay to Uptake in node(s) {str(csw_node_ids)}",
                        in_trigger=uptake_delay_event, out_iv=[female_delay_to_uptake],
                        target_sex='Female', node_ids=csw_node_ids)

    # Female delay to dropout
    # QUESTION: campaign json indicates this is a different distribution from men (and from men/women uptake). Ok?
    female_dropout_delay = {"Delay_Period_Lambda": 2215, "Delay_Period_Kappa": 3.312}
    female_delay_to_dropout = hiv_utils.broadcast_event_delayed(campaign,
                                                                event_trigger=dropout_event,
                                                                delay=female_dropout_delay)
    add_triggered_event(campaign, event_name=f"Commercial Sex (Female): Delay to Dropout in node(s) {str(csw_node_ids)}",
                        in_trigger=uptake_event, out_iv=[female_delay_to_dropout],
                        target_sex='Female', node_ids=csw_node_ids)

    # determine if men will become FSW clients
    time_value_map = {campaign.start_year: csw_male_uptake_coverage}
    # time_value_map = {"Times": [campaign.start_year + 1], "Values": [csw_male_uptake_coverage]}
    will_become_FSW_client = yearandsexdiag.new_diagnostic(campaign,
                                                           Positive_Event=uptake_delay_event,
                                                           Negative_Event='None',
                                                           TVMap=time_value_map,
                                                           interpolation_order=1)
    add_triggered_event(campaign, event_name=f"Will ever become FSW client in node(s) {str(csw_node_ids)}",
                        in_trigger=debut_event, out_iv=[will_become_FSW_client],
                        target_sex='Male', node_ids=csw_node_ids)

    # Male delay to uptake
    male_delay_to_uptake = hiv_utils.broadcast_event_delayed(campaign,
                                                             event_trigger=uptake_event,
                                                             delay={"Delay_Period_Min": 0, "Delay_Period_Max": 3650})
    add_triggered_event(campaign, event_name=f"Commercial Sex (Male): Delay to Uptake in node(s) {str(csw_node_ids)}",
                        in_trigger=uptake_delay_event, out_iv=[male_delay_to_uptake],
                        target_sex='Male', node_ids=csw_node_ids)

    # Male delay to dropout
    male_dropout_delay = {"Delay_Period_Min": 730, "Delay_Period_Max": 10950}
    male_delay_to_dropout = hiv_utils.broadcast_event_delayed(campaign,
                                                              event_trigger=dropout_event,
                                                              delay=male_dropout_delay)
    add_triggered_event(campaign, event_name=f"Commercial Sex (Male): Delay to Dropout in node(s) {str(csw_node_ids)}",
                        in_trigger=uptake_event, out_iv=[male_delay_to_dropout],
                        target_sex='Male', node_ids=csw_node_ids)

    # commercial uptake, all genders
    risk_to_high = PropertyValueChanger(campaign,
                                        Target_Property_Key='Risk', Target_Property_Value='HIGH')
    add_triggered_event(campaign, event_name=f"Commercial Sex: Uptake in node(s) {str(csw_node_ids)}",
                        in_trigger=uptake_event, out_iv=[risk_to_high],
                        node_ids=csw_node_ids)

    # commercial dropout, all genders
    risk_to_medium = PropertyValueChanger(campaign,
                                          Target_Property_Key='Risk', Target_Property_Value='MEDIUM')
    add_triggered_event(campaign, event_name=f"Commercial Sex: Dropout in node(s) {str(csw_node_ids)}",
                        in_trigger=dropout_event, out_iv=[risk_to_medium],
                        node_ids=csw_node_ids)


# property restrictions/disqualifying properties/new property values checked
def add_post_debut_coinfection(campaign, manifest,
                               coinfection_node_ids: List[int] = None,
                               coinfection_coverage: float = 0.3,
                               coinfection_gender: str = 'All',
                               coinfection_risk_group: str = "Risk:HIGH"):
    # intervention object setup
    post_debut_trigger = 'initial_coinfection_post_debut'
    modify_coinfection_status_iv = modcoinf.new_intervention(campaign)
    is_post_debut_check = stipostdebut.new_diagnostic(campaign,
                                                      Positive_Event=post_debut_trigger,
                                                      Negative_Event='None')

    # seed co-infections in the initial target post-debut population
    add_scheduled_event(campaign,
                        event_name=f"Identifying initial {coinfection_risk_group} post-debut population to target for coinfections",
                        out_iv=[is_post_debut_check],
                        coverage=coinfection_coverage, target_sex=coinfection_gender,
                        property_restrictions=[coinfection_risk_group], node_ids=coinfection_node_ids,
                        start_day=1 + EPSILON)  # this must start AFTER the distribution event to distribute properly
    add_triggered_event(campaign,
                        event_name=f"Distributing coinfections to initial {coinfection_risk_group} post-debut population",
                        in_trigger=post_debut_trigger, out_iv=[modify_coinfection_status_iv],
                        target_sex=coinfection_gender,
                        property_restrictions=[coinfection_risk_group], node_ids=coinfection_node_ids,
                        start_day=1)  # the default start day, but being explicit due to ordering issue

    # distribute co-infections at sexual debut, ongoing
    add_triggered_event(campaign,
                        event_name=f"Distributing coinfections to {coinfection_risk_group} population at sexual debut",
                        in_trigger='STIDebut', out_iv=[modify_coinfection_status_iv],
                        coverage=coinfection_coverage, target_sex=coinfection_gender,
                        property_restrictions=[coinfection_risk_group], node_ids=coinfection_node_ids)


# property restrictions/disqualifying properties/new property values checked
def add_pmtct(campaign, manifest,
              pmtct_child_testing_time_value_map: dict,
              pmtct_child_testing_start_year: float = 2004,
              pmtct_node_ids: List[int] = None,
              pmtct_coverage: float = 1.0,
              pmtct_start_year: float = 1990,
              pmtct_ramp_min: float = 0,
              pmtct_ramp_max: float = 0.975,
              pmtct_ramp_midyear: float = 2005.87,
              pmtct_ramp_rate: float = 0.7136,
              pmtct_link_to_ART_rate: float = 0.8):

    pmtct_start_day = timestep_from_year(pmtct_start_year, campaign.start_year)
    child_testing_start_day = timestep_from_year(pmtct_child_testing_start_year, campaign.start_year)
    disqualifying_properties = ["CascadeState:LostForever",
                                "CascadeState:OnART",
                                "CascadeState:LinkingToART",
                                "CascadeState:OnPreART",
                                "CascadeState:LinkingToPreART",
                                "CascadeState:ARTStaging",
                                "CascadeState:TestingOnSymptomatic"]
    testing_on_ANC_pv = "CascadeState:TestingOnANC"
    testing_child_pv = "CascadeState:TestingOnChild6w"

    # PMTCT HIV diagnostic test availability by time
    diagnostic_availability = sigmoiddiag.new_diagnostic(campaign,
                                                         Positive_Event='Needs_PMTCT_Diagnostic_Test',
                                                         Negative_Event='None',
                                                         ramp_min=pmtct_ramp_min,
                                                         ramp_max=pmtct_ramp_max,
                                                         ramp_midyear=pmtct_ramp_midyear,
                                                         ramp_rate=pmtct_ramp_rate,
                                                         disqualifying_properties=disqualifying_properties,
                                                         new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='Availability of PMTCT diagnostic test',
                        in_trigger='TwelveWeeksPregnant', out_iv=[diagnostic_availability],
                        coverage=pmtct_coverage, target_sex='Female', property_restrictions=['Accessibility:Yes'],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # distributing PMTCT HIV diagnostic test
    pmtct_hiv_test = rapiddiag.new_diagnostic(campaign,
                                              Positive_Event='HIV_Positive_at_ANC',
                                              Negative_Event='None',
                                              disqualifying_properties=disqualifying_properties,
                                              new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='PMTCT diagnostic test',
                        in_trigger='Needs_PMTCT_Diagnostic_Test', out_iv=[pmtct_hiv_test],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # Chance to enter ART post-positive result during ANC
    # QUESTION: should we send the signal ARTStaging2 instead? We already have a 0.8/0.2 dropout from PMTCT test here. Why double the chance to drop?
    choices = {'ARTStaging1': pmtct_link_to_ART_rate, 'None': 1 - pmtct_link_to_ART_rate}
    link_to_ART_decision = randomchoice.new_diagnostic(campaign,
                                                 choices=choices,
                                                 disqualifying_properties=disqualifying_properties,
                                                 new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='Linking from PMTCT positive result to ART',
                        in_trigger='HIV_Positive_at_ANC', out_iv=[link_to_ART_decision],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # PMTCT treatment selection based on time
    treatment_selection = sigmoiddiag.new_diagnostic(campaign,
                                                     Positive_Event='Needs_sdNVP_PMTCT',
                                                     Negative_Event='Needs_Combination_PMTCT',
                                                     ramp_min=0,
                                                     ramp_max=1,
                                                     ramp_midyear=2008.4,
                                                     ramp_rate=-1,
                                                     disqualifying_properties=disqualifying_properties,
                                                     new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='ANC/PMTCT: Choose Single-Dose Nevirapine (sdNVP) or Combination (Option A/B)',
                        in_trigger='HIV_Positive_at_ANC', out_iv=[treatment_selection],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # PMTCT treatment with sdNVP
    sdNVP_treatment = pmtct.new_intervention(campaign, efficacy=0.66)
    add_triggered_event(campaign, event_name='ANC/PMTCT: Less Effective PMTCT (sdNVP)',
                        in_trigger='Needs_sdNVP_PMTCT', out_iv=[sdNVP_treatment],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # PMTCT combination treatment selection
    time_value_map = convert_time_value_map({"Times": [2013.249], "Values": [1]})
    combination_treatment_selection = yearandsexdiag.new_diagnostic(campaign,
                                                                    Positive_Event='Needs_Option_B',
                                                                    Negative_Event='Needs_Option_A',
                                                                    TVMap=time_value_map,
                                                                    disqualifying_properties=disqualifying_properties,
                                                                    new_property_value=testing_on_ANC_pv)
    add_triggered_event(campaign, event_name='ANC/PMTCT: Combination Option A or B?',
                        in_trigger='Needs_Combination_PMTCT', out_iv=[combination_treatment_selection],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # PMTCT treatment with combination A
    pmtct_combination_treatment_A = pmtct.new_intervention(campaign, efficacy=0.9)
    add_triggered_event(campaign, event_name='ANC/PMTCT (Option A)',
                        in_trigger='Needs_Option_A', out_iv=[pmtct_combination_treatment_A],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # PMTCT treatment with combination B
    pmtct_combination_treatment_B = pmtct.new_intervention(campaign, efficacy=0.96667)
    add_triggered_event(campaign, event_name='ANC/PMTCT (Option B)',
                        in_trigger='Needs_Option_B', out_iv=[pmtct_combination_treatment_B],
                        node_ids=pmtct_node_ids, start_day=pmtct_start_day)

    # Testing of children at 6 weeks of age
    child_hiv_test = yearandsexdiag.new_diagnostic(campaign,
                                                   Positive_Event='ARTStaging0',
                                                   Negative_Event='None',
                                                   TVMap=pmtct_child_testing_time_value_map,
                                                   interpolation_order=1,
                                                   disqualifying_properties=disqualifying_properties,
                                                   new_property_value=testing_child_pv)
    add_triggered_event(campaign, event_name='CHILD 6W TESTING',
                        in_trigger='SixWeeksOld', out_iv=[child_hiv_test],
                        property_restrictions=['Accessibility:Yes'],
                        node_ids=pmtct_node_ids, start_day=child_testing_start_day)


# TODO: when doing A-B testing, translate Any_MC in existing json to MaleCircumcision (the new, default name used)
def add_traditional_male_circumcision(campaign, manifest,
                                      traditional_male_circumcision_coverage: float = 0.054978651,
                                      traditional_male_circumcision_reduced_acquire: float = 0.6,
                                      traditional_male_circumcision_node_ids: List[int] = None):
    # start time is arbitrary; just needs to be pre-epidemic
    start_day = timestep_from_year(1975, campaign.start_year)
    will_circumcise = 'WillReceiveTraditionalMaleCircumcision'

    # set up circumcision coverage selection
    choices = {will_circumcise: traditional_male_circumcision_coverage, 'None': 1 - traditional_male_circumcision_coverage}
    decide_traditional_male_circumcision = randomchoice.new_diagnostic(campaign, choices=choices)

    # Initializing historical traditional male circumcision in the population
    add_scheduled_event(campaign, event_name=f"Traditional male circumcision initialization in node(s) {str(traditional_male_circumcision_node_ids)}",
                        out_iv=[decide_traditional_male_circumcision],
                        target_sex='Male',
                        node_ids=traditional_male_circumcision_node_ids, start_day=start_day + EPSILON)

    # traditional male circumcision at birth, ongoing
    add_triggered_event(campaign, event_name=f"Traditional male circumcision at birth in node(s) {str(traditional_male_circumcision_node_ids)}",
                        in_trigger='Births', out_iv=[decide_traditional_male_circumcision],
                        target_sex='Male',
                        node_ids=traditional_male_circumcision_node_ids, start_day=start_day + EPSILON)

    # NOTE: this creates per-node-set events, which is more 'wasteful' if non-all-nodes are specified. But should work
    # just as well and prevent the user from calling a separate, second TMC function
    # actual traditional male circumcision event
    distribute_circumcision = malecirc.new_intervention(campaign,
                                                        reduced_acquire=traditional_male_circumcision_reduced_acquire,
                                                        reporting_name='Non_Program_MC')
    add_triggered_event(campaign, event_name=f"Apply traditional male circumcision intervention in node(s) {str(traditional_male_circumcision_node_ids)}",
                        in_trigger=will_circumcise, out_iv=[distribute_circumcision],
                        target_sex='Male',
                        node_ids=traditional_male_circumcision_node_ids, start_day=start_day)


def add_vmmc_reference_tracking(campaign, manifest,
                                vmmc_time_value_map: dict,
                                vmmc_reduced_acquire: float = 0.6,
                                vmmc_target_min_age: float = 15,
                                vmmc_target_max_age: float = 29.999999,
                                vmmc_start_year: float = 2015,
                                vmmc_node_ids: List[int] = None):
    start_day = timestep_from_year(vmmc_start_year, campaign.start_year)
    distribute_circumcision = malecirc.new_intervention(campaign,
                                                        reduced_acquire=vmmc_reduced_acquire,
                                                        reporting_name='Program_VMMC')
    add_reference_tracked_event(campaign, event_name='Reference tracking of VMMC',
                                out_iv=distribute_circumcision,
                                target_min_age=vmmc_target_min_age,
                                target_max_age=vmmc_target_max_age,
                                target_sex='Male',
                                target_disease_state='HIV_Negative',
                                time_value_map=vmmc_time_value_map,
                                update_period=30.4166666666667,
                                start_day=start_day,
                                node_ids=vmmc_node_ids)


# TODO: these are NChooserEventCoordinatorHIV events for Program VMMC, one per node. define/request add_nchooser_distributed_events method from emodpy-hiv
def add_historical_vmmc_nchooser(campaign, manifest,
                                 historical_vmmc_distributions_by_time: pd.DataFrame,
                                 historical_vmmc_reduced_acquire: float = 0.6,
                                 historical_vmmc_property_restrictions: List[str] = None,
                                 historical_vmmc_start_year: float = 2008,
                                 historical_vmmc_node_ids: List[int] = None):
    if historical_vmmc_property_restrictions is None:
        historical_vmmc_property_restrictions = []
    start_day = timestep_from_year(historical_vmmc_start_year, campaign.start_year)
    nchooser.add_nchooser_distributed_circumcision_event(campaign,
                                                         target_disease_state=["HIV_Negative", "Not_Have_Intervention"],
                                                         has_intervention_name_exclusion='MaleCircumcision',
                                                         distributions=historical_vmmc_distributions_by_time,
                                                         property_restrictions=historical_vmmc_property_restrictions,
                                                         circumcision_reduced_acquire=historical_vmmc_reduced_acquire,
                                                         distributed_event_trigger = 'Reference tracking of VMMC',
                                                         start_day=start_day,
                                                         event_name='Reference tracking of VMMC',
                                                         node_ids=historical_vmmc_node_ids)


def add_health_care_testing(campaign, manifest,
                            hct_node_ids: List[int] = None,
                            hct_start_year: float = 1990,
                            hct_reentry_rate: float = 1,
                            hct_retention_rate: float = 0.95,
                            hct_delay_to_next_test: int = 730):
    start_day = timestep_from_year(hct_start_year, campaign.start_year)
    disqualifying_properties = ["CascadeState:LostForever",
                                "CascadeState:OnART",
                                "CascadeState:LinkingToART",
                                "CascadeState:OnPreART",
                                "CascadeState:LinkingToPreART",
                                "CascadeState:ARTStaging"]
    disqualifying_properties_plus_hct_loop = disqualifying_properties + ["CascadeState:HCTTestingLoop"]

    # set up health care testing uptake at sexual debut by time
    uptake_choice = sigmoiddiag.new_diagnostic(campaign,
                                               Positive_Event='HCTTestingLoop0',
                                               Negative_Event='HCTUptakePostDebut1',
                                               ramp_min=-0.005,
                                               ramp_max=0.05,
                                               ramp_midyear=2005,
                                               ramp_rate=1,
                                               disqualifying_properties=disqualifying_properties,
                                               new_property_value='CascadeState:HCTUptakeAtDebut')
    add_triggered_event(campaign, event_name='HCTUptakeAtDebut: state 0 (decision, sigmoid by year and sex)',
                        in_trigger='STIDebut', out_iv=[uptake_choice],
                        property_restrictions=['Accessibility:Yes'],
                        node_ids=hct_node_ids, start_day=start_day)

    # initialization of health care testing (hct) at specified starting year
    initialize_hct = hiv_utils.broadcast_event_immediate(campaign,
                                                         event_trigger='HCTUptakePostDebut0')
    hiv_utils.set_intervention_properties(initialize_hct,disqualifying_properties=disqualifying_properties,
                                          new_property_value='CascadeState:HCTUptakePostDebut')
    add_scheduled_event(campaign, event_name='HCTUptakePostDebut: HCT Uptake Initialization',
                        out_iv=[initialize_hct],
                        node_ids=hct_node_ids, start_day=start_day)

    # ensure that everyone who is entering the health care testing system is post-debut (this is a filter: must be
    # post-debut to proceed)
    is_post_debut_check = stipostdebut.new_diagnostic(campaign,
                                                      Positive_Event='HCTUptakePostDebut1',
                                                      Negative_Event='None')
    add_triggered_event(campaign, event_name='Ensure HCTUptakePostDebut0 agents are post-debut',
                        in_trigger='HCTUptakePostDebut0', out_iv=[is_post_debut_check],
                        node_ids=hct_node_ids, start_day=start_day)

    # Up-to 1-year delay before an agent makes further decisions on making further hct uptake decisions
    delay_to_uptake_decision = hivmuxer.new_intervention(camp,
                                                         muxer_name='HCTUptakePostDebut',
                                                         max_entries=1,  # TODO: this should be the default & then remove
                                                         delay_complete_event='HCTUptakePostDebut2',
                                                         delay_distribution='CONSTANT_DISTRIBUTION',
                                                         delay_period_constant=365,
                                                         disqualifying_properties=disqualifying_properties_plus_hct_loop,
                                                         new_property_value='CascadeState:HCTUptakePostDebut')
    add_triggered_event(campaign, event_name='HCTUptakePostDebut1: state 1 (1-year delay, reachable)',
                        in_trigger='HCTUptakePostDebut1', out_iv=[delay_to_uptake_decision],
                        property_restrictions=['Accessibility=Yes'],
                        node_ids=hct_node_ids, start_day=start_day)

    # decision on hct uptake
    uptake_decision = sigmoiddiag.new_diagnostic(campaign,
                                                 Positive_Event='HCTTestingLoop0',
                                                 Negative_Event='HCTUptakePostDebut7',
                                                 ramp_min=-0.01,
                                                 ramp_max=0.15,
                                                 ramp_midyear=2006,
                                                 ramp_rate=1,
                                                 disqualifying_properties=disqualifying_properties_plus_hct_loop,
                                                 new_property_value="CascadeState:HCTUptakePostDebut"
                                                 )
    add_triggered_event(campaign, event_name='HCTUptakePostDebut: state 2 (Decision to uptake HCT)',
                        in_trigger='HCTUptakePostDebut2', out_iv=[uptake_decision],
                        property_restrictions=['Accessibility=Yes'],
                        node_ids=hct_node_ids, start_day=start_day)

    # reentry into uptake loop from lost-to-followup and ART dropout
    # QUESTION: ask... should this be HCTUptakePostDebut1 **1** ?? (can someone be non-debut and artdropout or ltfu? (maybe exposed children??)
    choices = {'HCTUptakePostDebut0': hct_reentry_rate, 'None': 1 - hct_reentry_rate}
    reentry_decision = randomchoice.new_diagnostic(campaign,
                                                   choices=choices,
                                                   new_property_value='CascadeState:HCTUptakePostDebut')
    add_triggered_event(campaign, event_name='HCTUptakePostDebut: state 3 (From LTFU or ART dropout back into HCT uptake loop)',
                        in_trigger=['HCTUptakePostDebut3', 'HCTUptakePostDebut9'], out_iv=[reentry_decision],
                        node_ids=hct_node_ids, start_day=start_day)

    # testing loop -- delay until next test
    delay_to_next_hct = hivmuxer.new_intervention(campaign,
                                                  muxer_name='HCTTestingLoop',
                                                  max_entries=1,  # TODO: this should be the default & then remove
                                                  delay_complete_event='HCTTestingLoop1',
                                                  delay_distribution='CONSTANT_DISTRIBUTION',
                                                  delay_period_constant=hct_delay_to_next_test,
                                                  disqualifying_properties=disqualifying_properties,
                                                  new_property_value='CascadeState:HCTTestingLoop')
    add_triggered_event(campaign, event_name='HCTTestingLoop: state 0 (delay to next HCT): Default',
                        in_trigger='HCTTestingLoop0', out_iv=[delay_to_next_hct],
                        node_ids=hct_node_ids, start_day=start_day)

    # testing loop -- hct hiv test
    hiv_test = rapiddiag.new_diagnostic(campaign,
                                        Positive_Event='ARTStaging9',
                                        Negative_Event='HCTTestingLoop2',
                                        disqualifying_properties=disqualifying_properties,
                                        new_property_value='CascadeState:HCTTestingLoop')
    add_triggered_event(campaign, event_name='HCTTestingLoop: state 1 (HIV rapid diagnostic)',
                        in_trigger='HCTTestingLoop1', out_iv=[hiv_test],
                        node_ids=hct_node_ids, start_day=start_day)

    # testing loop -- hct retention -- stay in loop or dropout
    choices = {'HCTTestingLoop0': hct_retention_rate, 'HCTUptakePostDebut1': 1 - hct_retention_rate}
    retention_decision = randomchoice.new_diagnostic(campaign,
                                                     choices=choices,
                                                     disqualifying_properties=disqualifying_properties,
                                                     new_property_value='CascadeState:HCTTestingLoop')
    add_triggered_event(campaign, event_name='HCTTestingLoop: state 2 (HCT Testing retention/dropout)',
                        in_trigger='HCTTestingLoop2', out_iv=[retention_decision],
                        node_ids=hct_node_ids, start_day=start_day)


def add_ART_cascade(campaign, manifest,
                    art_cascade_node_ids: List[int] = None,
                    art_cascade_start_year: float = 1990,
                    art_cascade_pre_staging_retention: float = 0.85,
                    art_cascade_cd4_retention_rate: float = 1,
                    art_cascade_pre_art_retention: float = 0.75,
                    art_cascade_immediate_art_rate: float = 0.1,
                    art_cascade_art_reenrollment_willingness: float = 0.9):
    start_day = timestep_from_year(art_cascade_start_year, campaign.start_year)
    disqualifying_properties = ["CascadeState:LostForever",
                                "CascadeState:OnART",
                                "CascadeState:LinkingToART",
                                "CascadeState:OnPreART",
                                "CascadeState:LinkingToPreART"]
    disqualifying_properties_plus_art_staging = disqualifying_properties + ["CascadeState:ARTStaging"]

    # presentation of symptoms leading to HIV testing
    probability_of_symptoms = sigmoiddiag.new_diagnostic(campaign,
                                                         Positive_Event='ARTStaging0',
                                                         Negative_Event='ARTStaging8',
                                                         ramp_min=0.25,
                                                         ramp_max=0.9,
                                                         ramp_midyear=2002,
                                                         ramp_rate=0.5,
                                                         disqualifying_properties=disqualifying_properties_plus_art_staging,
                                                         new_property_value='CascadeState:TestingOnSymptomatic')
    add_triggered_event(campaign, event_name='TestingOnSymptomatic: state 0 (Presentation probability)',
                        in_trigger='HIVSymptomatic', out_iv=[probability_of_symptoms],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # # TODO: is this dead code?
    # # Consider increased symptomatic presentation at some point
    # increased_symptomatic_presentation_time_value_map = {"Times": [1990, 2016], "Values": [0, 0]}
    # increased_symptomatic_presentation_disqualifying_properties = ["CascadeState:LostForever",
    #                                                                "CascadeState:OnART",
    #                                                                "CascadeState:LinkingToART",
    #                                                                "CascadeState:OnPreART",
    #                                                                "CascadeState:LinkingToPreART",
    #                                                                "CascadeState:ARTStaging"]
    # increased_symptomatic_presentation = yearandsexdiag.new_diagnostic(campaign,
    #                                                                    Positive_Event='ARTStaging2',
    #                                                                    Negative_Event='None',
    #                                                                    TVMap=increased_symptomatic_presentation_time_value_map,
    #                                                                    disqualifying_properties=increased_symptomatic_presentation_disqualifying_properties,
    #                                                                    new_property_value='CascadeState:TestingOnSymptomatic')
    # add_triggered_event(campaign, event_name='Consider increased symptomatic presentation (after 2016?)',
    #                     in_trigger='ARTStaging8', out_iv=[increased_symptomatic_presentation],
    #                     node_ids=art_cascade_node_ids, start_day=start_day)

    #
    # BEGIN ART STAGING SECTION
    #

    # HIV testing of those who present with symptoms
    hiv_test = rapiddiag.new_diagnostic(campaign,
                                        Positive_Event='ARTStaging1',
                                        Negative_Event='None',
                                        disqualifying_properties=disqualifying_properties,
                                        new_property_value='CascadeState:ARTStagingDiagnosticTest')  # QUESTION: bug? if a person is left in this state, do other events consider it?
    add_triggered_event(campaign, event_name='ART Staging: state 0 (HIV rapid diagnostic)',
                        in_trigger='ARTStaging0', out_iv=[hiv_test],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # chance to return for blood draw
    choices = {'ARTStaging2': art_cascade_pre_staging_retention, 'HCTUptakePostDebut3': 1 - art_cascade_pre_staging_retention}
    prestaging_retention = randomchoice.new_diagnostic(campaign,
                                                       choices=choices,
                                                       disqualifying_properties=disqualifying_properties,
                                                       new_property_value='CascadeState:ARTStaging')
    add_triggered_event(campaign, event_name='ARTStaging: state 1 (random choice: linking from positive diagnostic test)',
                        in_trigger='ARTStaging1', out_iv=[prestaging_retention],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # ensuring each agent continues testing in this cascade once per timestep
    muxer = hivmuxer.new_intervention(campaign,
                                      muxer_name='ARTStaging',
                                      max_entries=1,  # TODO: this should be the default & then remove
                                      delay_complete_event='ARTStaging3',
                                      delay_distribution='CONSTANT_DISTRIBUTION',
                                      delay_period_constant=1,
                                      disqualifying_properties=disqualifying_properties,
                                      new_property_value='CascadeState:ARTStaging')
    add_triggered_event(campaign, event_name='ARTStaging: state 2 (Muxer to make sure only one entry per DT)',
                        in_trigger='ARTStaging2', out_iv=[muxer],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # perform blood draw
    draw_blood = drawblood.new_diagnostic(campaign,
                                          Positive_Event='ARTStaging4',
                                          disqualifying_properties=disqualifying_properties,
                                          new_property_value='CascadeState:ARTStaging')
    add_triggered_event(campaign, event_name='ARTStaging: state 3 (draw blood)',
                        in_trigger='ARTStaging3', out_iv=[draw_blood],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # TODO: map-out this artstaging cascade; it doesn't seem to make sense (error on my part? original campaign?)
    # TODO: move this into an input data file and read?
    # CD4 agnostic ART eligibility check

    adult_by_pregnant = convert_time_value_map({"Times": [2002, 2013.95], "Values": [0, 1]})
    adult_by_TB = convert_time_value_map({"Times": [2002], "Values": [1]})
    adult_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})
    child_treat_under_age_in_years_threshold = convert_time_value_map({"Times": [2002, 2013.95], "Values": [5, 15]})
    child_by_TB = convert_time_value_map({"Times": [2002, 2010.5], "Values": [0, 1]})
    child_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})

    art_eligibility = artstagingbycd4agnosticdiag.new_diagnostic(campaign,
                                                                 Positive_Event='LinkingToART0',
                                                                 Negative_Event='ARTStaging5',
                                                                 abp_tvmap=adult_by_pregnant,
                                                                 abt_tvmap=adult_by_TB,
                                                                 abw_tvmap=adult_by_WHO_stage,
                                                                 cua_tvmap=child_treat_under_age_in_years_threshold,
                                                                 cbt_tvmap=child_by_TB,
                                                                 cbw_tvmap=child_by_WHO_stage,
                                                                 disqualifying_properties=disqualifying_properties,
                                                                 new_property_value='CascadeState:ARTStaging')
    add_triggered_event(campaign, event_name='ARTStaging: state 4 (check eligibility for ART, CD4 agnostic)',
                        in_trigger='ARTStaging4', out_iv=[art_eligibility],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # if NOT eligible for ART without checking CD4, decide to return for CD4 test or lost-to-followup (LTFU)
    choices = {'ARTStaging6': art_cascade_cd4_retention_rate, 'HCTUptakePostDebut9': 1 - art_cascade_cd4_retention_rate}
    cd4_retention = randomchoice.new_diagnostic(campaign,
                                                choices=choices,
                                                disqualifying_properties=disqualifying_properties,
                                                new_property_value='CascadeState:ARTStaging')
    add_triggered_event(campaign, event_name='ARTStaging: state 5 (random choice: Return for CD4 or LTFU)',
                        in_trigger='ARTStaging5', out_iv=[cd4_retention],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # determine if eligible for ART given CD4 counts
    # TODO: move this into an input data file and read?
    cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 500]})
    pregnant_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 2000]})
    active_TB_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5], "Values": [200, 2000]})
    art_eligibility_by_cd4 = artstagingbycd4diag.new_diagnostic(campaign,
                                                                Positive_Event='LinkingToART0',
                                                                Negative_Event='LinkingToPreART0',
                                                                Threshold_TVMap=cd4_threshold,
                                                                IP_TVMap=pregnant_cd4_threshold,
                                                                IAT_TVMap=active_TB_cd4_threshold,
                                                                disqualifying_properties=disqualifying_properties,
                                                                new_property_value='CascadeState:ARTStaging')
    add_triggered_event(campaign, event_name='ARTStaging: state 6 (check eligibility for ART by CD4)',
                        in_trigger='ARTStaging6', out_iv=[art_eligibility_by_cd4],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    #
    # END ART STAGING SECTION
    #

    #
    # BEGIN PRE-ART
    #

    # chance of linking to pre-ART
    # QUESTION: should we exclude CascadeState:LinkingToPreART, too?
    disqualifying_properties_pre_art_linking = ["CascadeState:LostForever",
                                                "CascadeState:OnART",
                                                "CascadeState:LinkingToART",
                                                "CascadeState:OnPreART"]
    link_decision = sigmoiddiag.new_diagnostic(campaign,
                                               Positive_Event='OnPreART0',
                                               Negative_Event='HCTUptakePostDebut9',
                                               ramp_min=0.7572242198,
                                               ramp_max=0.9591484679,
                                               ramp_midyear=2006.8336631523,
                                               ramp_rate=1,
                                               female_multiplier=1.5,
                                               disqualifying_properties=disqualifying_properties_pre_art_linking,
                                               new_property_value="CascadeState:LinkingToPreART")
    add_triggered_event(campaign, event_name='LinkingToPreART: state 0 (Linking probability)',
                        in_trigger='LinkingToPreART0', out_iv=[link_decision],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # ensuring each agent continues this cascade once per timestep
    # TODO: is this right to not exclude LinkingToPreART? could someone go back here IN THAT STATE ALREADY??
    disqualifying_properties_pre_art = ["CascadeState:LostForever",
                                        "CascadeState:OnART",
                                        "CascadeState:LinkingToART"]
    muxer = hivmuxer.new_intervention(campaign,
                                      muxer_name='PreART',
                                      max_entries=1,  # TODO: this should be the default & then remove
                                      delay_complete_event='OnPreART1',
                                      delay_distribution='CONSTANT_DISTRIBUTION',
                                      delay_period_constant=182,
                                      disqualifying_properties=disqualifying_properties_pre_art,
                                      new_property_value='CascadeState:OnPreART')
    add_triggered_event(campaign, event_name='OnPreART: state 0 (muxer, 182-day delay)',
                        in_trigger='OnPreART0', out_iv=[muxer],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # decision to continue to pre-ART or lost to followup (LTFU)
    choices = {'OnPreART2': art_cascade_pre_art_retention, 'HCTUptakePostDebut9': 1 - art_cascade_pre_art_retention}
    pre_ART_retention = randomchoice.new_diagnostic(campaign,
                                              choices=choices,
                                              disqualifying_properties=disqualifying_properties_pre_art,
                                              new_property_value='CascadeState:CascadeState:OnPreART')
    add_triggered_event(campaign, event_name='OnPreART: state 1 (random choice: pre-ART or LTFU)',
                        in_trigger='OnPreART1', out_iv=[pre_ART_retention],
                        node_ids=art_cascade_node_ids, start_day=start_day)


    # TODO: move this into an input data file and read?
    # CD4 agnostic pre-ART eligibility check
    adult_by_pregnant = convert_time_value_map({"Times": [2002, 2013.95], "Values": [0, 1]})
    adult_by_TB = convert_time_value_map({"Times": [2002], "Values": [1]})
    adult_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})
    child_treat_under_age_in_years_threshold = convert_time_value_map({"Times": [2002, 2013.95], "Values": [5, 15]})
    child_by_TB = convert_time_value_map({"Times": [2002, 2010.5], "Values": [0, 1]})
    child_by_WHO_stage = convert_time_value_map({"Times": [2002, 2007.45, 2016], "Values": [4, 3, 0]})
    pre_art_eligibility = artstagingbycd4agnosticdiag.new_diagnostic(campaign,
                                                                     Positive_Event='OnART0',
                                                                     Negative_Event='OnPreART3',
                                                                     abp_tvmap=adult_by_pregnant,
                                                                     abt_tvmap=adult_by_TB,
                                                                     abw_tvmap=adult_by_WHO_stage,
                                                                     cua_tvmap=child_treat_under_age_in_years_threshold,
                                                                     cbt_tvmap=child_by_TB,
                                                                     cbw_tvmap=child_by_WHO_stage,
                                                                     disqualifying_properties=disqualifying_properties_pre_art,
                                                                     new_property_value='CascadeState:OnPreART')
    add_triggered_event(campaign, event_name='OnPreART: state 2 (check eligibility for ART, CD4 agnostic)',
                        in_trigger='OnPreART2', out_iv=[pre_art_eligibility],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # perform blood draw, pre-ART
    draw_blood = drawblood.new_diagnostic(campaign,
                                          Positive_Event='OnPreART4',
                                          disqualifying_properties=disqualifying_properties_pre_art,
                                          new_property_value='CascadeState:OnPreART')
    add_triggered_event(campaign, event_name='OnPreART: state 3 (draw blood)',
                        in_trigger='OnPreART3', out_iv=[draw_blood],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # TODO: note that the ART and pre-ART cascades have a different order for retention, is this right?? Explore/verify then ask.
    # determine if eligible for ART given CD4 counts
    # TODO: move this into an input data file and read?
    cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 500]})
    pregnant_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5, 2013.95], "Values": [200, 350, 2000]})
    active_TB_cd4_threshold = convert_time_value_map({"Times": [2002, 2010.5], "Values": [200, 2000]})
    art_eligibility_by_cd4 = artstagingbycd4diag.new_diagnostic(campaign,
                                                                Positive_Event='OnART0',
                                                                Negative_Event='OnPreART0',
                                                                Threshold_TVMap=cd4_threshold,
                                                                IP_TVMap=pregnant_cd4_threshold,
                                                                IAT_TVMap=active_TB_cd4_threshold,
                                                                disqualifying_properties=disqualifying_properties_pre_art,
                                                                new_property_value='CascadeState:OnPreART')
    add_triggered_event(campaign, event_name='OnPreART: state 4 (check eligibility for ART by CD4)',
                        in_trigger='OnPreART4', out_iv=[art_eligibility_by_cd4],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    #
    # END PRE-ART
    #

    #
    # BEGIN ART LINKING
    #

    # ART linking probability by time
    art_linking_disqualifying_properties = ["CascadeState:LostForever", "CascadeState:OnART"]
    art_linking_probability = sigmoiddiag.new_diagnostic(campaign,
                                                         Positive_Event='OnART0',
                                                         Negative_Event='HCTUptakePostDebut3',
                                                         ramp_min=0,
                                                         ramp_max=0.8507390283,
                                                         ramp_midyear=1997.4462231708,
                                                         ramp_rate=1,
                                                         disqualifying_properties=art_linking_disqualifying_properties,
                                                         new_property_value='CascadeState:LinkingToART')
    add_triggered_event(campaign, event_name='LinkingToART: state 0 (Linking probability)',
                        in_trigger='LinkingToART0', out_iv=[art_linking_probability],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # decide to initiate ART now or later
    disqualifying_properties_art = ["CascadeState:LostForever"]
    choices = {'OnART1': art_cascade_immediate_art_rate, 'ARTInitiationDelayed': 1 - art_cascade_immediate_art_rate}
    when_decision = randomchoice.new_diagnostic(campaign,
                                                choices=choices,
                                                disqualifying_properties=disqualifying_properties_art,
                                                new_property_value="CascadeState:OnART")
    add_triggered_event(campaign, event_name='Delay to ART initiation: decide whether to initiate immediately or delay',
                        in_trigger='OnART0', out_iv=[when_decision],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # delay to ART initiation plus muxer to ensure agents only do it once at a time
    # Up-to 1-year delay before an agent makes further decisions on making further hct uptake decisions
    delay = {"Delay_Period_Lambda": 63.381, "Delay_Period_Kappa": 0.711, "Delay_Period_Max": 120, "Delay_Period_Min": 1}
    delay_to_art_initiation = hivmuxer.new_intervention(campaign,
                                                        muxer_name='OnART',
                                                        max_entries=1,  # TODO: this should be the default & then remove
                                                        delay_complete_event='OnART1',
                                                        delay_distribution='WEIBULL_DISTRIBUTION',
                                                        delay_period_lambda=63.381,
                                                        delay_period_kappa=0.711,
                                                        disqualifying_properties=disqualifying_properties_art,
                                                        new_property_value='CascadeState:OnART')
    add_triggered_event(campaign, event_name='OnART: state 0 (muxer and delay)',
                        in_trigger='ARTInitiationDelayed', out_iv=[delay_to_art_initiation],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # initiate ART
    initiate_art = art.new_intervention(campaign)
    add_triggered_event(campaign, event_name='Initiate ART',
                        in_trigger='OnART1', out_iv=[initiate_art],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # delay to dropping off of ART + muxer to ensure drop-off once per agent/timestep
    art_dropout_delay = hivmuxer.new_intervention(campaign,
                                                  muxer_name='ARTDropoutDelay',
                                                  max_entries=1,  # TODO: this should be the default & then remove
                                                  delay_complete_event='OnART3',
                                                  delay_distribution='CONSTANT_DISTRIBUTION',
                                                  delay_period_constant=7300,
                                                  disqualifying_properties=disqualifying_properties_art,
                                                  new_property_value='CascadeState:OnART')
    add_triggered_event(campaign, event_name='OnART: state 2 (delay to dropout)',
                        in_trigger='OnART1', out_iv=[art_dropout_delay],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # discontinue ART; dropout
    # QUESTION: do we need to change their CascadeState now that they're off ART?
    discontinue_ART = artdropout.new_intervention(campaign)
    add_triggered_event(campaign, event_name='OnART: state 3 (run ARTDropout)',
                        in_trigger='OnART3', out_iv=[discontinue_ART],
                        node_ids=art_cascade_node_ids, start_day=start_day)

    # Willingness to re-enroll in ART after dropout
    choices = {'HCTUptakePostDebut8': art_cascade_art_reenrollment_willingness,
               'LostForever9': 1 - art_cascade_art_reenrollment_willingness}
    willing_to_reenroll = randomchoice.new_diagnostic(campaign,
                                                      choices=choices,
                                                      disqualifying_properties=['CascadeState:LostForever'],
                                                      new_property_value="CascadeState:OnART")
    add_triggered_event(campaign, event_name='OnART: state 4 (Willing to re-enroll in ART?)',
                        in_trigger='OnART3', out_iv=[willing_to_reenroll],
                        node_ids=art_cascade_node_ids, start_day=start_day)


    # #
    # # TODO: The following are currently NOT enabled in Zambia campaign, but may be used? (these are the only consumers of certain signals)
    # # TODO: The following may not even belong in this big ART function (maybe only parts, maybe none, consider)
    # #
    #
    # # TODO: is this dead code?
    # # Consider restarting ART immediately after dropping off ART
    # restart_ART_time_value_map = {"Times": [1990, 2016], "Values": [0, 0]}
    # immediate_ART_restart = yearandsexdiag.new_diagnostic(campaign,
    #                                                       Positive_Event='OnART1',
    #                                                       Negative_Event='HCTUptakePostDebut3',
    #                                                       TVMap=restart_ART_time_value_map,
    #                                                       disqualifying_properties=['CascadeState:LostForever'],
    #                                                       new_property_value='CascadeState:OnART')
    # add_triggered_event(campaign, event_name='Consider not dropping (after 2016?)',
    #                     in_trigger='HCTUptakePostDebut8', out_iv=[immediate_ART_restart],
    #                     node_ids=art_cascade_node_ids, start_day=start_day)
    #
    # # TODO: is this dead code?
    # # reconsider being lost forever to ART care
    # reconsider_lost_forever_time_value_map = {"Times": [1990, 2016], "Values": [0, 0]}
    # reconsider_lost_forever = yearandsexdiag.new_diagnostic(campaign,
    #                                                       Positive_Event='OnART1',
    #                                                       Negative_Event='LostForever0',
    #                                                       TVMap=reconsider_lost_forever_time_value_map,
    #                                                       disqualifying_properties=['CascadeState:LostForever'],
    #                                                       new_property_value='CascadeState:OnART')
    # add_triggered_event(campaign, event_name='Consider not lost forever (after 2016?)',
    #                     in_trigger='LostForever9', out_iv=[reconsider_lost_forever],
    #                     node_ids=art_cascade_node_ids, start_day=start_day)
    #
    # # TODO: is this dead code?
    # # Actually lost forever now
    # lost_forever = PropertyValueChanger(campaign,
    #                                     Target_Property_Key='CascadeState', Target_Property_Value='LostForever')
    # add_triggered_event(campaign, event_name='LostForever: state 0',
    #                     in_trigger='LostForever0', out_iv=[lost_forever],
    #                     node_ids=art_cascade_node_ids, start_day=start_day)
    #
    # # TODO: is this dead code?
    # # Consider immediate ART in HCT loop, no further testing for eligibility or potential waiting, at some point
    # consider_immediate_ART_time_value_map = {"Times": [1990, 2016], "Values": [0, 0]}
    # consider_immediate_ART_disqualifying_properties = ["CascadeState:LostForever",
    #                                                    "CascadeState:OnART",
    #                                                    "CascadeState:LinkingToART",
    #                                                    "CascadeState:OnPreART",
    #                                                    "CascadeState:LinkingToPreART",
    #                                                    "CascadeState:ARTStaging"]
    # consider_immediate_ART = yearandsexdiag.new_diagnostic(campaign,
    #                                                        Positive_Event='OnART1',
    #                                                        Negative_Event='ARTStaging1',
    #                                                        TVMap=consider_immediate_ART_time_value_map,
    #                                                        disqualifying_properties=consider_immediate_ART_disqualifying_properties,
    #                                                        new_property_value='CascadeState:HCTTestingLoop')
    # add_triggered_event(campaign, event_name='Consider immediate ART (after 2016?)',
    #                     in_trigger='ARTStaging9', out_iv=[consider_immediate_ART],
    #                     node_ids=art_cascade_node_ids, start_day=start_day)


def add_rtri_testing(campaign, manifest,
                     rtri_node_ids: List[int] = None,
                     rtri_start_year: float = 2015,
                     rtri_testing_min_age: float = 15,
                     rtri_followup_rate: float = 1,
                     rtri_consent_rate: float = 1,
                     rtri_retesting_rate: float = 0.01):  # TODO: find a good starting value or just calibrate.
    raise NotImplementedError("This function is not yet implemented.")

    start_day = timestep_from_year(rtri_start_year, campaign.start_year)

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


def add_index_testing(campaign, manifest,
                      index_testing_triggers: List[str],
                      index_testing_node_ids: List[int] = None,
                      index_testing_start_year: float = 2015,
                      index_testing_partner_coverage: float = 0.5):  # TODO: definitely calibrate this!
    raise NotImplementedError("The index_testing_partner_coverage in this function is not yet implemented.")
    # TODO: add ALL of these campaign elements, when complete, to the original json version
    if index_testing_triggers is None:
        # QUESTION: are these right? Additionally, need to add retester_is_HIV+ in the campaign caller
        index_testing_triggers = ['HIV_Positive_at_ANC', 'ARTStaging9', 'ARTStaging1']
    start_day = timestep_from_year(index_testing_start_year, campaign.start_year)

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

