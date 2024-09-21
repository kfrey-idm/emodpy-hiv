from emodpy_hiv.reporters.builtin import *


def config_reports(task, manifest):
    add_transmission_report(task)
    add_event_recorder(task, event_list=["NewInfectionEvent",
                                         "NewlySymptomatic",
                                         "StartTreatment",
                                         "StartedART",
                                         "GetTested",
                                         "HIVPositiveTest"],
                       ips_to_record=["Accessibility", "Risk"],
                       start_day=30000,
                       end_day=35000,
                       node_ids=None,
                       min_age_years=12,
                       max_age_years=67,
                       must_have_ip_key_value="",
                       must_have_intervention="",
                       property_change_ip_to_record="")
    add_report_relationship_consummated(task,
                                        start_year=1970,
                                        end_year=1985,
                                        node_ids=None,
                                        min_age_years=12,
                                        max_age_years=67,
                                        must_have_ip_key_value="",
                                        must_have_intervention="",
                                        individual_properties=["Accessibility", "Risk"])
    add_report_hiv_by_age_and_gender(task,
                                     start_year=1970,
                                     end_year=1985,
                                     collect_gender_data=True,
                                     collect_age_bins_data=[1, 16, 30, 60, 90, 120],
                                     collect_circumcision_data=True,
                                     collect_hiv_stage_data=True,
                                     collect_ip_data=["Accessibility", "Risk"],
                                     collect_intervention_data=["NewInfectionEvent"],
                                     add_transmitters=True,
                                     stratify_infected_by_cd4=True,
                                     event_counter_list=["NewInfectionEvent"],
                                     add_relationships=True,
                                     add_concordant_relationships=True)
    add_report_hiv_art(task)
    add_human_migration_tracking(task, manifest=manifest)
    add_report_event_counter(task, manifest, event_trigger_list=["NewInfectionEvent",
                                                                 "NewlySymptomatic",
                                                                 "StartTreatment",
                                                                 "StartedART",
                                                                 "GetTested",
                                                                 "HIVPositiveTest"], filename_suffix="demo_scenario")
    add_report_hiv_infection(task, start_year=1970, end_year=1985)
    add_report_hiv_mortality(task)
    add_report_simulation_stats(task, manifest)
    add_report_relationship_start(task,
                                  start_year=1970,
                                  end_year=1985,
                                  node_ids=None,
                                  min_age_years=12,
                                  max_age_years=67,
                                  include_hiv_disease_statistics=True,
                                  include_other_relationship_statistics=True,
                                  individual_properties=["Accessibility", "Risk"],
                                  must_have_ip_key_value="",
                                  must_have_intervention="")
    add_report_relationship_end(task)
    add_report_node_demographics(task, manifest=manifest,
                                 age_bins=[1, 30, 60, 120],
                                 ip_key_to_collect="Accessibility",
                                 stratify_by_gender=True)
    add_report_relationship_migration_tracking(task, manifest,
                                               start_year=1970,
                                               end_year=1985,
                                               node_ids=None,
                                               min_age_years=12,
                                               max_age_years=67,
                                               must_have_ip_key_value="",
                                               must_have_intervention="",
                                               filename_suffix="demo_scenario")


def config_non_schema_params(conf):
    conf.parameters["Disable_IP_Whitelist"] = 1
    conf.parameters["Enable_Continuous_Log_Flushing"] = 0
    conf.parameters["logLevel_default"] = "WARNING"
    #conf.parameters.alpha__logLevel_Memory = "WARNING"
    #conf.parameters.logLevel_InfectionHIV = "ERROR"
    #conf.parameters.logLevel_Instrumentation = "ERROR"
    #conf.parameters.logLevel_Memory = "ERROR"
    #conf.parameters.logLevel_OutbreakIndividual = "ERROR"
    #conf.parameters.logLevel_Simulation = "ERROR"
    #conf.parameters.logLevel_SusceptibilityHIV = "ERROR"

def set_config ( conf ):
    # 'Useless' params (not actually used by HIV) -- will be gone after merging in multi-parent depends-on solution from G-O.
    conf.parameters.Incubation_Period_Distribution = 'CONSTANT_DISTRIBUTION'
    conf.parameters.Incubation_Period_Constant = 0
 
    # HIV Science Params
    conf.parameters.Simulation_Type = "HIV_SIM"
    conf.parameters.Base_Infectivity = 0.002327836
    conf.parameters.CD4_Post_Infection_Weibull_Heterogeneity = 0
    conf.parameters.CD4_Post_Infection_Weibull_Scale = 540.55
    conf.parameters.Coital_Dilution_Factor_2_Partners = 0.75
    conf.parameters.Coital_Dilution_Factor_3_Partners = 0.6
    conf.parameters.Coital_Dilution_Factor_4_Plus_Partners = 0.45
    conf.parameters.Days_Between_Symptomatic_And_Death_Weibull_Heterogeneity = 0.5
    conf.parameters.Days_Between_Symptomatic_And_Death_Weibull_Scale = 618.341625
    conf.parameters.Enable_Maternal_Infection_Transmission = 1
    conf.parameters.HIV_Age_Max_for_Adult_Age_Dependent_Survival = 50
    conf.parameters.Male_To_Female_Relative_Infectivity_Ages = [ 0, 15, 25 ]
    conf.parameters.Male_To_Female_Relative_Infectivity_Multipliers = [ 4.684, 4.684, 2.962 ]
    conf.parameters.Maternal_Infection_Transmission_Probability = 0.3
    conf.parameters.Maternal_Transmission_ART_Multiplier = 0.03334
    conf.parameters.Min_Days_Between_Adding_Relationships = 0
    conf.parameters.PFA_Burnin_Duration_In_Days = 5475
    conf.parameters.STI_Coinfection_Acquisition_Multiplier = 5.5
    conf.parameters.STI_Coinfection_Transmission_Multiplier = 5.5
    conf.parameters.Sexual_Debut_Age_Female_Weibull_Heterogeneity = 0.299281948
    conf.parameters.Sexual_Debut_Age_Female_Weibull_Scale = 16.34494123
    conf.parameters.Sexual_Debut_Age_Male_Weibull_Heterogeneity = 0.053712118
    conf.parameters.Sexual_Debut_Age_Male_Weibull_Scale = 17.72188303

    # Simulation Setup
    conf.parameters.x_Base_Population = 0.05
    conf.parameters.Individual_Sampling_Type = "FIXED_SAMPLING"
    conf.parameters.Load_Balance_Filename = ""
    conf.parameters.Node_Grid_Size = 0.009 
    conf.parameters.Random_Number_Generator_Policy = "ONE_PER_NODE"
    conf.parameters.Random_Number_Generator_Type = "USE_AES_COUNTER"

    config_non_schema_params(conf)
