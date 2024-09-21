import pandas as pd
from collections import defaultdict
from abc import ABC, abstractmethod
from typing import Dict, Union
import pathlib
from importlib import resources
from importlib.abc import Traversable

import emodpy_hiv.campaign.coc as coc
import emod_api
import emod_api.campaign as camp
import emodpy_hiv.country_data.zambia as zambia_data


class DefaultZambiaData:
    """
    This class contains the default data file paths for Zambia.
    """
    data_root = resources.files(zambia_data)
    historical_vmmc_data_file = data_root.joinpath("historical_vmmc_data.csv")
    initial_age_distribution_file = data_root.joinpath("initial_age_distribution.csv")
    initial_population_file = data_root.joinpath("initial_population.csv")
    female_mortality_file = data_root.joinpath("parsed_mortality--female.csv")
    male_mortality_file = data_root.joinpath("parsed_mortality--male.csv")
    fertility_file = data_root.joinpath("parsed_fertility.csv")


class Country(ABC):
    def __init__(self,
                 country_name: str, base_year: float = 1960.5):
        self.country_name = country_name
        self.base_year = base_year

    def initialize_campaign(self, schema_path, base_year):
        print(f"Telling emod-api to use {schema_path} as schema.")
        camp.set_schema(schema_path)
        camp.base_year = base_year
        return camp

    @staticmethod
    def load_nchooser_distribution_data(file_path: str) -> dict:
        """
        Load target distribution data into a dataframe format that works for Nchooser and group by node_id.
        Args:
            file_path: path to the csv file that contains the data

        Returns:
            dict: a dictionary that has node_id as the key and a dataframe as the value. The dataframe contains the
            distribution data for Nchooser.

        """
        data = pd.read_csv(file_path)
        data_dict = defaultdict(pd.DataFrame)
        for node_id in pd.unique(data['node_set']):
            node_data = data[data['node_set'] == node_id]
            node_dict = {'year': [], 'min_age': [], 'max_age': [], 'n_circumcisions': []}
            for year in pd.unique(node_data['year']):
                year_data = node_data[node_data['year'] == year]
                for _, row in year_data.iterrows():
                    node_dict['year'].append(year)
                    node_dict['min_age'].append(float(row['age_bin'].split(':')[0].replace('[', '')))
                    node_dict['max_age'].append(float(row['age_bin'].split(':')[1].replace(')', '')) - 0.00001)
                    node_dict['n_circumcisions'].append(int(row['n_circumcisions']))
            data_dict[int(node_id)] = pd.DataFrame(node_dict)
        return data_dict

    def add_male_circumcision(self, campaign, historical_vmmc_data_filepath,
                              traditional_male_circumcision_coverages_per_node):
        # ---- Add historical vmmc NChooser events to campaign ----
        self.add_historical_vmmc_nchooser(campaign, historical_vmmc_data_filepath)
        # ---- Add traditional male circumcision to campaign ----
        self.add_traditional_male_circumcision(campaign, traditional_male_circumcision_coverages_per_node)
        # ---- Add (VMMC) reference tracking to campaign ----
        self.add_vmmc_reference_tracking(campaign)

    def add_historical_vmmc_nchooser(self, campaign, historical_vmmc_data_filepath: str,
                                     historical_vmmc_reduced_acquire=0.6, historical_vmmc_start_year=2008):
        # Load historical vmmc data into data frame
        historical_vmmc_data = self.load_nchooser_distribution_data(historical_vmmc_data_filepath)
        for node_id in historical_vmmc_data:
            coc.add_historical_vmmc_nchooser(campaign=campaign,
                                             historical_vmmc_distributions_by_time=historical_vmmc_data[node_id],
                                             historical_vmmc_reduced_acquire=historical_vmmc_reduced_acquire,
                                             historical_vmmc_property_restrictions=None,
                                             historical_vmmc_start_year=historical_vmmc_start_year,
                                             historical_vmmc_node_ids=[node_id],
                                             has_intervention_name_exclusion=coc.ANY_MC,
                                             event_name=f"NChooser to produce specified number of program VMMCs in node"
                                                        f" {node_id}, {self.country_name}")

    def add_traditional_male_circumcision(self, campaign, traditional_male_circumcision_coverages_per_node: dict):
        randomchoice_start_year = 1975
        traditional_male_circumcision_start_year = 1961
        traditional_male_circumcision_reduced_acquire = 0.6
        for node_id, mc_coverage in traditional_male_circumcision_coverages_per_node.items():
            coc.add_traditional_male_circumcision(campaign=campaign,
                                                  traditional_male_circumcision_start_year=traditional_male_circumcision_start_year,
                                                  randomchoice_start_year=randomchoice_start_year,
                                                  traditional_male_circumcision_coverage=mc_coverage,
                                                  traditional_male_circumcision_reduced_acquire=traditional_male_circumcision_reduced_acquire,
                                                  traditional_male_circumcision_node_ids=[node_id])

    def add_vmmc_reference_tracking(self, campaign):
        vmmc_time_value_map = {"Times": [2015.9999, 2016, 2021], "Values": [0, 0.54, 0.9]}
        coc.add_vmmc_reference_tracking(campaign=campaign,
                                        vmmc_time_value_map=vmmc_time_value_map,
                                        vmmc_reduced_acquire=0.6,
                                        vmmc_target_min_age=15,
                                        vmmc_target_max_age=29.999999,
                                        vmmc_start_year=2015,
                                        vmmc_node_ids=None,  # all nodes
                                        update_period=30.4166666666667)

    def seed_infections(self, campaign):
        # add outbreak individual interventions with coverage 0.1 to all nodes with Risk:HIGH
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # DMB Removing "Risk:HIGH" and increasing coverage to 0.2.  Anna had some plots from 2016
        # that showed prevalence closer to 20% for gender-based age bins 25-45 
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        coc.seed_infections(campaign=campaign,
                            seeding_node_ids=None,  # all nodes
                            seeding_start_year=1982,
                            seeding_coverage=0.2,
                            seeding_target_property_restrictions=[])


    def add_csw(self, campaign):
        csw_male_uptake_coverage_nodeset1 = 0.195
        csw_female_uptake_coverage_nodeset1 = 0.125
        csw_male_uptake_coverage_nodeset2 = 0.0781
        csw_female_uptake_coverage_nodeset2 = 0.05
        coc.add_csw(campaign=campaign,
                    node_ids=[1, 2, 3, 7, 9],
                    male_uptake_coverage=csw_male_uptake_coverage_nodeset1,
                    female_uptake_coverage=csw_female_uptake_coverage_nodeset1)
        coc.add_csw(campaign=campaign,
                    node_ids=[4, 5, 6, 8, 10],
                    male_uptake_coverage=csw_male_uptake_coverage_nodeset2,
                    female_uptake_coverage=csw_female_uptake_coverage_nodeset2)

    def add_post_debut_coinfection(self, campaign):
        coinfection_risk_to_coverage = {'HIGH': 0.3, 'MEDIUM': 0.3, 'LOW': 0.1}
        for risk, coverage in coinfection_risk_to_coverage.items():
            coc.add_post_debut_coinfection(campaign=campaign,
                                           coinfection_coverage=coverage,
                                           coinfection_gender='All',
                                           coinfection_IP=f'Risk:{risk}')

    def add_pmtct(self, campaign):
        self.add_state_TestingOnANC(campaign)
        # Testing of children at 6 weeks of age
        self.add_state_TestingOnChild6w(campaign)

    def add_health_care_testing(self,
                                campaign: emod_api.campaign,
                                hct_start_year: float = 1990):
        start_day = coc.timestep_from_year(hct_start_year, self.base_year)

        self.add_state_HCTUptakeAtDebut(campaign=campaign,
                                        start_day=start_day)

        self.add_state_HCTUptakePostDebut(campaign=campaign,
                                          start_day=start_day)

        self.add_state_HCTTestingLoop(campaign=campaign,
                                      start_day=start_day)

    def add_ART_cascade(self, campaign, art_cascade_start_year: float = 1990):
        start_day = coc.timestep_from_year(art_cascade_start_year, self.base_year)

        self.add_state_TestingOnSymptomatic(campaign=campaign, start_day=start_day)

        #
        # ---- BEGIN ART STAGING SECTION ----
        #
        self.add_state_ARTStagingDiagnosticTest(campaign=campaign, start_day=start_day)

        self.add_state_ARTStaging(campaign=campaign, start_day=start_day)
        #
        # ---- BEGIN PRE-ART ----
        #
        # chance of linking to pre-ART
        self.add_state_LinkingToPreART(campaign=campaign, start_day=start_day)

        # ensuring each agent continues this cascade once per timestep
        self.add_state_OnPreART(campaign=campaign, start_day=start_day)
        #
        # ---- BEGIN ART LINKING ----
        #
        self.add_state_LinkingToART(campaign=campaign, start_day=start_day)

        # decide to initiate ART now or later
        self.add_state_OnART(campaign=campaign, start_day=start_day)
        #
        self.add_state_LostForever(campaign=campaign, start_day=start_day)

    def add_state_TestingOnANC(self, campaign: emod_api.campaign):
        node_ids = None
        start_year = 1990
        coverage = 1.0
        sigmoid_ramp_min = 0
        sigmoid_ramp_max = 0.975
        sigmoid_ramp_midyear = 2005.87
        sigmoid_ramp_rate = 0.7136
        link_to_ART_rate = 0.8
        treatment_a_efficacy = 0.9
        treatment_b_efficacy = 0.96667
        sdNVP_efficacy = 0.66
        start_day = coc.timestep_from_year(start_year, campaign.base_year)
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART,
                                    coc.CascadeState.ART_STAGING,
                                    coc.CascadeState.TESTING_ON_SYMPTOMATIC]
        property_restrictions = 'Accessibility:Yes'

        coc.add_state_TestingOnANC(campaign=campaign,
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

    def add_state_TestingOnChild6w(self, campaign: emod_api.campaign):
        child_testing_start_year = 2004
        node_ids = None
        child_testing_time_value_map = {"Times": [2004, 2005, 2006, 2008, 2009],
                                        "Values": [0, 0.03, 0.1, 0.2, 0.3365]}
        child_testing_start_day = coc.timestep_from_year(child_testing_start_year, campaign.base_year)
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART,
                                    coc.CascadeState.ART_STAGING,
                                    coc.CascadeState.TESTING_ON_SYMPTOMATIC]
        property_restrictions = 'Accessibility:Yes'
        coc.add_state_TestingOnChild6w(campaign=campaign,
                                       disqualifying_properties=disqualifying_properties,
                                       time_value_map=child_testing_time_value_map,
                                       node_ids=node_ids,
                                       property_restrictions=property_restrictions,
                                       start_day=child_testing_start_day)

    def add_state_HCTUptakeAtDebut(self, campaign: emod_api.campaign, start_day: int):
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART,
                                    coc.CascadeState.ART_STAGING]
        coc.add_state_HCTUptakeAtDebut(campaign=campaign,
                                       disqualifying_properties=disqualifying_properties,
                                       node_ids=None,
                                       start_day=start_day)

    def add_state_HCTUptakePostDebut(self, campaign: emod_api.campaign, start_day: int):
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART,
                                    coc.CascadeState.ART_STAGING]
        coc.add_state_HCTUptakePostDebut(campaign=campaign, disqualifying_properties=disqualifying_properties,
                                         node_ids=None, hct_reentry_rate=1, start_day=start_day,
                                         tvmap_test_for_enter_HCT_testing_loop=coc.all_negative_time_value_map)

    def add_state_HCTTestingLoop(self, campaign: emod_api.campaign, start_day: int):
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART,
                                    coc.CascadeState.ART_STAGING]
        hct_delay_to_next_test = [730, 365, 1100]  # Default values for Zambia model
        hct_delay_to_next_test_node_ids = [[1, 2, 3, 4, 6, 7], [5, 9, 10], [8]]  # Default values for Zambia model
        hct_delay_to_next_test_node_names = ['Default', 'Lusaka, Southern, Western',
                                             'Northern']  # Default values for Zambia model
        coc.add_state_HCTTestingLoop(campaign=campaign, disqualifying_properties=disqualifying_properties,
                                     start_day=start_day, hct_retention_rate=0.95,
                                     tvmap_consider_immediate_ART=coc.all_negative_time_value_map,
                                     hct_delay_to_next_test=hct_delay_to_next_test,
                                     hct_delay_to_next_test_node_ids=hct_delay_to_next_test_node_ids,
                                     hct_delay_to_next_test_node_names=hct_delay_to_next_test_node_names, node_ids=None)

    def add_state_TestingOnSymptomatic(self, campaign: emod_api.campaign, start_day: int):
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART,
                                    coc.CascadeState.ART_STAGING]
        coc.add_state_TestingOnSymptomatic(campaign=campaign,
                                           disqualifying_properties=disqualifying_properties,
                                           start_day=start_day, node_ids=None,
                                           tvmap_increased_symptomatic_presentation=coc.all_negative_time_value_map)

    def add_state_ARTStagingDiagnosticTest(self, campaign: emod_api.campaign, start_day: int):
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART]
        coc.add_state_ARTStagingDiagnosticTest(campaign=campaign,
                                               disqualifying_properties=disqualifying_properties,
                                               start_day=start_day, node_ids=None)

    def add_state_ARTStaging(self, campaign: emod_api.campaign, start_day: int):
        cd4_retention_rate = 1
        pre_staging_retention = 0.85
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER,
                                    coc.CascadeState.ON_ART,
                                    coc.CascadeState.LINKING_TO_ART,
                                    coc.CascadeState.ON_PRE_ART,
                                    coc.CascadeState.LINKING_TO_PRE_ART]
        coc.add_state_ARTStaging(campaign=campaign,
                                 disqualifying_properties=disqualifying_properties,
                                 start_day=start_day, node_ids=None, pre_staging_retention=pre_staging_retention,
                                 cd4_retention_rate=cd4_retention_rate)

    def add_state_LinkingToPreART(self, campaign: emod_api.campaign, start_day: int):
        disqualifying_properties_pre_art_linking = [coc.CascadeState.LOST_FOREVER,
                                                    coc.CascadeState.ON_ART,
                                                    coc.CascadeState.LINKING_TO_ART,
                                                    coc.CascadeState.ON_PRE_ART]
        coc.add_state_LinkingToPreART(campaign=campaign,
                                      disqualifying_properties=disqualifying_properties_pre_art_linking,
                                      start_day=start_day, node_ids=None)

    def add_state_OnPreART(self, campaign: emod_api.campaign, start_day: int):
        disqualifying_properties_pre_art = [coc.CascadeState.LOST_FOREVER,
                                            coc.CascadeState.ON_ART,
                                            coc.CascadeState.LINKING_TO_ART]
        pre_art_retention = 0.75
        coc.add_state_OnPreART(campaign=campaign,
                               node_ids=None,
                               pre_art_retention=pre_art_retention,
                               disqualifying_properties=disqualifying_properties_pre_art,
                               start_day=start_day)

    def add_state_LinkingToART(self, campaign: emod_api.campaign, start_day: int):
        node_ids = None
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER, coc.CascadeState.ON_ART]
        coc.add_state_LinkingToART(campaign=campaign,
                                   node_ids=node_ids,
                                   disqualifying_properties=disqualifying_properties,
                                   start_day=start_day)

    def add_state_OnART(self, campaign: emod_api.campaign, start_day: int):
        node_ids = None
        art_reenrollment_willingness = 0.9
        immediate_art_rate = 0.1
        tvmap_immediate_ART_restart = coc.all_negative_time_value_map
        tvmap_reconsider_lost_forever = coc.all_negative_time_value_map
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER]
        coc.add_state_OnART(campaign=campaign,
                            art_reenrollment_willingness=art_reenrollment_willingness,
                            immediate_art_rate=immediate_art_rate,
                            node_ids=node_ids,
                            disqualifying_properties=disqualifying_properties,
                            start_day=start_day,
                            tvmap_immediate_ART_restart=tvmap_immediate_ART_restart,
                            tvmap_reconsider_lost_forever=tvmap_reconsider_lost_forever)

    def add_state_LostForever(self, campaign: emod_api.campaign, start_day: int):
        node_ids = None
        coc.add_state_LostForever(campaign=campaign,
                                  node_ids=node_ids,
                                  start_day=start_day)

    def build_campaign(self,
                       schema_path: str,
                       base_year: float,
                       historical_vmmc_data_filepath: Union[str, Traversable],
                       traditional_male_circumcision_coverages_per_node: dict):
        """
        A method to pass into EMODTask to build campaign events for Emod.

        Args:
            schema_path(str): file path to the schema file.
            base_year(float): base year for the Simulation.
            historical_vmmc_data_filepath(str): file path to the historical vmmc data csv file.
            traditional_male_circumcision_coverages_per_node(Dict[int: float]): coverage of traditional male
                circumcision per node.

        Returns:

        """
        # ---- Initialize a campaign object -----
        campaign = self.initialize_campaign(schema_path, base_year)

        # ---- Add male circumcision to campaign -----
        # This block contains 3 chunk of events: historical vmmc NChooser, traditional male circumcision and VMMC with
        # reference tracking.
        self.add_male_circumcision(campaign, historical_vmmc_data_filepath,
                                   traditional_male_circumcision_coverages_per_node)

        # ---- Add prevention of mother-to-child transmission (PMTCT) to campaign ----
        # This pmtct block contains 2 Cascade states: TestingOnANC and TestingOnChild6w
        self.add_pmtct(campaign)

        # ---- Add OutbreakIndividual interventions to campaign ----
        self.seed_infections(campaign)

        # ---- Add commercial sex worker (CSW) uptake and dropout (with delays) for men and women to campaign ----
        self.add_csw(campaign)

        # ---- Add co-infections post sexual debut to campaign ----
        self.add_post_debut_coinfection(campaign)

        # ---- Add health care testing loops to campaign ----
        # This health care testing block contains 3 Cascade states: HCTUptakeAtDebut, HCTUptakePostDebut and
        # HCTTestingLoop
        self.add_health_care_testing(campaign)

        # ---- Add Antiretroviral Therapy (ART) Cascade to campaign ----
        # This ART Cascade block contains 8 Cascade states: TestingOnSymptomatic, ARTStagingDiagnosticTest, ARTStaging
        # LinkingToPreART, OnPreART, LinkingToART, OnART and LostForever
        self.add_ART_cascade(campaign)

        return campaign


class Zambia(Country):
    """
    Zambia country model class. This class is a subclass of the Country class and implements the build_campaign method
    to build campaign object to be used with EMODTask.

    Example:
        >>> from emodpy_hiv.country_model import Zambia
        >>> from emodpy.emod_task import EMODTask
        >>> import manifest
        >>> from functools import partial
        >>> zambia = Zambia()
        >>> # Define a campaign_builder function to pass in the required arguments for the zambia.build_campaign() method.
        >>> def campaign_builder():
        >>>     return zambia.build_campaign(schema_path=manifest.schema_file, base_year=1960.5)
        >>> # Alternatively, you can use the partial function to pass in the required arguments for the
        >>> # zambia.build_campaign() method. For example:
        >>> # campaign_builder = partial(zambia.build_campaign, schema_path=manifest.schema_file, base_year=1960.5)
        >>> # Create an EMODTask object using the campaign_builder function
        >>> task = EMODTask.from_default2(config_path="config.json",
        >>>                               eradication_path=manifest.eradication_path,
        >>>                               campaign_builder=campaign_builder, ...)
    """

    def __init__(self, country_name="Zambia"):
        super().__init__(country_name)

    def build_config(self, config):
        config.parameters.Simulation_Type = "HIV_SIM"
        config.parameters.Simulation_Duration = 99.5 * 365
        config.parameters.Simulation_Timestep = 30.4166666666667

        # Reduce the initial population so tutorial can double it
        config.parameters.x_Base_Population = 0.002 #0.005

        config.parameters.Start_Time = 0
        config.parameters.AIDS_Duration_In_Months = 9
        config.parameters.AIDS_Stage_Infectivity_Multiplier = 4.5
        config.parameters.Acute_Duration_In_Months = 2.9
        config.parameters.Acute_Stage_Infectivity_Multiplier = 26
        config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_COMPLEX"
        config.parameters.Base_Individual_Sample_Rate = 1
        config.parameters.Base_Infectivity = 0.00031382269992254885
        config.parameters.Base_Year = 1960.5
        config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
        config.parameters.Birth_Rate_Time_Dependence = "NONE"
        config.parameters.CD4_At_Death_LogLogistic_Heterogeneity = 0.7
        config.parameters.CD4_At_Death_LogLogistic_Scale = 2.96
        config.parameters.CD4_Post_Infection_Weibull_Heterogeneity = 0.2756
        config.parameters.CD4_Post_Infection_Weibull_Scale = 560.43
        config.parameters.Coital_Dilution_Factor_2_Partners = 0.75
        config.parameters.Coital_Dilution_Factor_3_Partners = 0.6
        config.parameters.Coital_Dilution_Factor_4_Plus_Partners = 0.45
        config.parameters.Condom_Transmission_Blocking_Probability = 0.8
        config.parameters.Days_Between_Symptomatic_And_Death_Weibull_Heterogeneity = 0.5
        config.parameters.Days_Between_Symptomatic_And_Death_Weibull_Scale = 618.341625
        config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
        config.parameters.Enable_Aging = 1
        config.parameters.Enable_Birth = 1
        config.parameters.Enable_Coital_Dilution = 1
        config.parameters.Enable_Default_Reporting = 1
        config.parameters.Enable_Demographics_Reporting = 0
        config.parameters.Enable_Demographics_Birth = 0
        config.parameters.Enable_Infectivity_Reservoir = 0
        config.parameters.Enable_Maternal_Protection = 0
        config.parameters.Enable_Natural_Mortality = 1
        config.parameters.HIV_Adult_Survival_Scale_Parameter_Intercept = 21.182
        config.parameters.HIV_Adult_Survival_Scale_Parameter_Slope = -0.2717
        config.parameters.HIV_Adult_Survival_Shape_Parameter = 2
        config.parameters.HIV_Age_Max_for_Adult_Age_Dependent_Survival = 50
        config.parameters.HIV_Age_Max_for_Child_Survival_Function = 15
        config.parameters.HIV_Child_Survival_Rapid_Progressor_Fraction = 0.57
        config.parameters.HIV_Child_Survival_Rapid_Progressor_Rate = 1.52
        config.parameters.HIV_Child_Survival_Slow_Progressor_Scale = 16
        config.parameters.HIV_Child_Survival_Slow_Progressor_Shape = 2.7
        config.parameters.Heterogeneous_Infectiousness_LogNormal_Scale = 0
        config.parameters.Incubation_Period_Constant = 0
        config.parameters.Incubation_Period_Distribution = "CONSTANT_DISTRIBUTION"
        config.parameters.Individual_Sampling_Type = "FIXED_SAMPLING"
        config.parameters.Infection_Updates_Per_Timestep = 1
        config.parameters.Infectivity_Scale_Type = "CONSTANT_INFECTIVITY"
        config.parameters.Male_To_Female_Relative_Infectivity_Ages = [0, 15, 25]
        config.parameters.Male_To_Female_Relative_Infectivity_Multipliers = [2.9976868182763963,
                                                                             2.9976868182763963,
                                                                             2.936393464131044]
        config.parameters.Maternal_Infection_Transmission_Probability = 0.3
        config.parameters.Maternal_Transmission_ART_Multiplier = 0.03334
        config.parameters.Migration_Model = "NO_MIGRATION"
        config.parameters.Min_Days_Between_Adding_Relationships = 0
        config.parameters.Node_Grid_Size = 0.009
        config.parameters.PFA_Burnin_Duration_In_Days = 5475
        config.parameters.PFA_Cum_Prob_Selection_Threshold = 0.2
        config.parameters.Population_Density_Infectivity_Correction = "CONSTANT_INFECTIVITY"
        config.parameters.Population_Scale_Type = "FIXED_SCALING"
        config.parameters.Run_Number = 1
        config.parameters.STI_Coinfection_Acquisition_Multiplier = 5.5
        config.parameters.STI_Coinfection_Transmission_Multiplier = 5.5
        config.parameters.Serialized_Population_Reading_Type = "NONE"
        config.parameters.Serialized_Population_Writing_Type = "NONE"
        config.parameters.Sexual_Debut_Age_Setting_Type = "WEIBULL"
        config.parameters.Sexual_Debut_Age_Female_Weibull_Heterogeneity = 0.22002507694706103
        config.parameters.Sexual_Debut_Age_Female_Weibull_Scale = 15.092122890359025
        config.parameters.Sexual_Debut_Age_Male_Weibull_Heterogeneity = 0.1268087803455056
        config.parameters.Sexual_Debut_Age_Male_Weibull_Scale = 15.582384534190258
        config.parameters.Sexual_Debut_Age_Min = 13

        config.parameters["logLevel_InfectionHIV"] = "ERROR"
        config.parameters["logLevel_Instrumentation"] = "INFO"
        config.parameters["logLevel_Memory"] = "INFO"
        config.parameters["logLevel_OutbreakIndividual"] = "ERROR"
        config.parameters["logLevel_Simulation"] = "INFO"
        config.parameters["logLevel_SusceptibilityHIV"] = "ERROR"
        config.parameters["logLevel_AntiretroviralTherapy"] = "ERROR"
        config.parameters["logLevel_default"] = "WARNING"

        return config

    def build_campaign(self,
                       schema_path: str,
                       base_year: float = 1960.5,
                       historical_vmmc_data_filepath: Union[str, Traversable] = DefaultZambiaData.historical_vmmc_data_file,
                       traditional_male_circumcision_coverages_per_node: Dict[int, float] = None):
        
        if traditional_male_circumcision_coverages_per_node is None:
            traditional_male_circumcision_coverages_per_node = \
                {1: 0.054978651, 2: 0.139462861, 3: 0.028676043, 4: 0.091349358,
                 5: 0.12318707, 6: 0.039308099, 7: 0.727917322, 8: 0.041105263,
                 9: 0.044388102, 10: 0.398239794}

        return super().build_campaign(schema_path, base_year, historical_vmmc_data_filepath,
                                      traditional_male_circumcision_coverages_per_node)

    def build_demographics(self):
        import emodpy_hiv.demographics.country_models as demog_cm

        demog = demog_cm.load_country_model_demographics_default("zambia")

        return demog
