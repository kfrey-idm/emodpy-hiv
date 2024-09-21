#!/usr/bin/env python
import unittest
import sys
from pathlib import Path
import json
import os

import emod_api.campaign as campaign
import emod_api.interventions.common as common
import emod_api.schema_to_class

import emodpy_hiv.interventions.outbreak as ob
import emodpy_hiv.interventions.art as art
import emodpy_hiv.interventions.artdropout as artdropout
import emodpy_hiv.interventions.artstagingbycd4agnosticdiag as artstageagnosticdiag
import emodpy_hiv.interventions.artstagingbycd4diag as artstage4diag
import emodpy_hiv.interventions.drawblood as drawblood
import emodpy_hiv.interventions.malecirc as malecirc
import emodpy_hiv.interventions.modcoinf as modcoinf  
import emodpy_hiv.interventions.pmtct as pmtct
import emodpy_hiv.interventions.prep as prep
import emodpy_hiv.interventions.randomchoice as randomchoice
import emodpy_hiv.interventions.rapiddiag as rapiddiag
import emodpy_hiv.interventions.sigmoiddiag as sigmoiddiag
import emodpy_hiv.interventions.stipostdebut as stipostdebut
import emodpy_hiv.interventions.yearandsexdiag as yearandsexdiag
import emodpy_hiv.interventions.cascade_helpers as cascade
import emodpy_hiv.interventions.reftracker as reftracker
import emodpy_hiv.interventions.setsexualdebut as setsexualdebut
import emodpy_hiv.interventions.reftrackercoord as reftrackercoord

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))
import manifest


# TODO, uncomment positive/negative test events when merged into G-O
class HIVInterventionTest(unittest.TestCase):
    is_debugging = True

    # region unittest setup and teardown method
    @classmethod
    def setUpClass(cls):
        cls.camp = campaign
        cls.camp.schema_path = manifest.schema_path

    def setUp(self):
        self.camp.reset()
        print(f"running {self._testMethodName}:")
        self.output_filename = ""

    def tearDown(self):
        if os.path.exists(self.output_filename) and not self.is_debugging:
            os.remove(self.output_filename)

        print("end of test\n")
    # endregion

    # region outbreak
    def test_outbreak_new_intervention(self):
        timestep = 365
        coverage = 0.05
        event = ob.new_intervention(timestep=timestep, camp=self.camp, coverage=coverage)
        self.assertEqual(event.Start_Day, timestep)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'OutbreakIndividual')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)
    # endregion

    # region ReferenceTrackingCoordinatorTrackingConfig
    def test_DistributeIVByRefTrackCoord_with_intervention_list(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        interventions = [emod_api.schema_to_class.get_class_with_defaults("OutbreakIndividual", self.camp.schema_path)] * 2

        start_year = 1960.5
        end_year = 2050
        update_period = 30.416667
        target_age_min = 14
        target_age_max = 19
        time_value_map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)
        tracking_config_copy = tracking_config.copy()

        ref = reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, interventions, time_value_map,
                                                          End_Year=end_year,
                                                          Tracking_Config=tracking_config, Update_Period=update_period,
                                                          Target_Age_Min=target_age_min, Target_Age_Max=target_age_max)

        self.assertEqual(ref["class"], "CampaignEventByYear")
        self.assertEqual(ref["Start_Year"], start_year)
        self.assertEqual(ref["Nodeset_Config"]["class"], "NodeSetAll")
        self.assertEqual(ref["Event_Coordinator_Config"]["class"], "ReferenceTrackingEventCoordinatorTrackingConfig")
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Times"], [1960, 1970, 1980])
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Values"], [0.1, 0.2, 0.3])
        self.assertEqual(ref["Event_Coordinator_Config"]["End_Year"], end_year)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Demographic"], "Everyone")
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Gender"], "All")
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Min"], target_age_min)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Max"], target_age_max)
        self.assertEqual(ref["Event_Coordinator_Config"]["Update_Period"], update_period)
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["class"],
                         "MultiInterventionDistributor")
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["Intervention_List"][0]["class"],
                         "OutbreakIndividual")
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["Intervention_List"][1]["class"],
                         "OutbreakIndividual")
        self.assertDictEqual(ref["Event_Coordinator_Config"]["Tracking_Config"], tracking_config_copy)

    def test_DistributeIVByRefTrackCoord_with_intervention(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        intervention = emod_api.schema_to_class.get_class_with_defaults("OutbreakIndividual", self.camp.schema_path)
        intervention_copy = intervention.copy()

        start_year = 1960.5
        end_year = 2050
        update_period = 30.416667
        target_age_min = 14
        target_age_max = 19
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)
        tracking_config_copy = tracking_config.copy()

        ref = reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, intervention, Time_Value_Map,
                                                          End_Year=end_year,
                                                          Tracking_Config=tracking_config, Update_Period=update_period,
                                                          Target_Age_Min=target_age_min, Target_Age_Max=target_age_max)

        self.assertEqual(ref["class"], "CampaignEventByYear")
        self.assertEqual(ref["Start_Year"], start_year)
        self.assertEqual(ref["Nodeset_Config"]["class"], "NodeSetAll")
        self.assertEqual(ref["Event_Coordinator_Config"]["class"], "ReferenceTrackingEventCoordinatorTrackingConfig")
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Times"], [1960, 1970, 1980])
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Values"], [0.1, 0.2, 0.3])
        self.assertEqual(ref["Event_Coordinator_Config"]["End_Year"], end_year)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Demographic"], "Everyone")
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Gender"], "All")
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Min"], target_age_min)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Max"], target_age_max)
        self.assertEqual(ref["Event_Coordinator_Config"]["Update_Period"], update_period)
        self.assertDictEqual(ref["Event_Coordinator_Config"]["Intervention_Config"], intervention_copy)
        self.assertDictEqual(ref["Event_Coordinator_Config"]["Tracking_Config"], tracking_config_copy)

    def test_DistributeIVByRefTrackCoord_with_intervention_Target_Demographic(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        intervention = emod_api.schema_to_class.get_class_with_defaults("OutbreakIndividual", self.camp.schema_path)
        intervention_copy = intervention.copy()

        start_year = 1960.5
        end_year = 2050
        update_period = 30.416667
        target_age_min = 14
        target_age_max = 19
        target_demographic = "ExplicitAgeRangesAndGender"
        target_gender = "Female"
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)
        tracking_config_copy = tracking_config.copy()

        ref = reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, intervention, Time_Value_Map,
                                                          End_Year=end_year,
                                                          Tracking_Config=tracking_config, Update_Period=update_period,
                                                          Target_Gender=target_gender, Target_Age_Min=target_age_min,
                                                          Target_Age_Max=target_age_max,
                                                          Target_Demographic=target_demographic)

        self.assertEqual(ref["class"], "CampaignEventByYear")
        self.assertEqual(ref["Start_Year"], start_year)
        self.assertEqual(ref["Nodeset_Config"]["class"], "NodeSetAll")
        self.assertEqual(ref["Event_Coordinator_Config"]["class"], "ReferenceTrackingEventCoordinatorTrackingConfig")
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Times"], [1960, 1970, 1980])
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Values"], [0.1, 0.2, 0.3])
        self.assertEqual(ref["Event_Coordinator_Config"]["End_Year"], end_year)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Demographic"], target_demographic)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Gender"], target_gender)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Min"], target_age_min)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Max"], target_age_max)
        self.assertEqual(ref["Event_Coordinator_Config"]["Update_Period"], update_period)
        self.assertDictEqual(ref["Event_Coordinator_Config"]["Intervention_Config"], intervention_copy)
        self.assertDictEqual(ref["Event_Coordinator_Config"]["Tracking_Config"], tracking_config_copy)

    def test_DistributeIVByRefTrackCoord_set_node_and_property_restriction(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        intervention = emod_api.schema_to_class.get_class_with_defaults("OutbreakIndividual", self.camp.schema_path)
        start_year = 1960.5
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)

        prop_rest_within_node = emod_api.schema_to_class.get_class_with_defaults("idmType:PropertyRestrictions", self.camp.schema_path)
        prop_rest_within_node.append({"Prop": "Value"})

        with self.assertRaises(ValueError) as err:
            reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, intervention, Time_Value_Map, tracking_config,
                                                        Property_Restrictions=["Prop:Value"],
                                                        Property_Restrictions_Within_Node=prop_rest_within_node)
        self.assertEqual(str(err.exception),
                         "Cannot set both Property_Restrictions and Property_Restrictions_Within_Node")

    def test_DistributeIVByRefTrackCoord_Target_Demographic_no_age(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        intervention = emod_api.schema_to_class.get_class_with_defaults("OutbreakIndividual", self.camp.schema_path)
        start_year = 1960.5
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)
        Target_Demographic = "ExplicitAgeRangesAndGender"
        with self.assertRaises(ValueError) as err:
            reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, intervention, Time_Value_Map, tracking_config,
                                                        Target_Demographic=Target_Demographic)
        self.assertEqual(str(err.exception),
                         "Target_Age_Min and Target_Age_Max need to be set when setting Target_Demographic == 'ExplicitAgeRanges' or 'ExplicitAgeRangesAndGender'")

    def test_DistributeIVByRefTrackCoord_Target_Demographic_ExplicitAgeRanges_no_age(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        intervention = emod_api.schema_to_class.get_class_with_defaults("OutbreakIndividual", self.camp.schema_path)
        start_year = 1960.5
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)
        Target_Demographic = "ExplicitAgeRanges"
        with self.assertRaises(ValueError) as err:
            reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, intervention, Time_Value_Map, tracking_config,
                                                        Target_Demographic=Target_Demographic)
        self.assertEqual(str(err.exception),
                         "Target_Age_Min and Target_Age_Max need to be set when setting Target_Demographic == 'ExplicitAgeRanges' or 'ExplicitAgeRangesAndGender'")
    # endregion

    # region SetSexualDebutAge
    def test_setsexualdebut_new_intervention_sets_implicits(self):
        """ Test if the intervention generated from default values is correct """
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        # check that list of implicits is empty
        self.assertEqual(len(self.camp.implicits), 0)

        event = setsexualdebut._new_intervention(camp=self.camp)

        # new_intervention adds _enable_debut_age_as_intervention to camp.implicits to
        # set Sexual_Debut_Age_Setting_Type to "FROM_INTERVENTION".
        parameters = emod_api.schema_to_class.ReadOnlyDict({"Sexual_Debut_Age_Setting_Type": "WEIBULL"})
        config = emod_api.schema_to_class.ReadOnlyDict({"parameters": parameters})
        c = self.camp.implicits[0](config)   # call the first implicit in the list, this should set Sexual_Debut_Age_Setting_Type in config
        self.assertEqual(c["parameters"]["Sexual_Debut_Age_Setting_Type"], "FROM_INTERVENTION")

    def test_setsexualdebut_new_intervention_default(self):
        """ Test if the intervention generated from default values is correct """
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        event = setsexualdebut._new_intervention(camp=self.camp)

        self.assertEqual(event["class"], "SetSexualDebutAge")
        self.assertEqual(event["Age_Years"], 125)       # default value, not used because Setting_Type = "CURRENT_AGE"
        self.assertEqual(event["Intervention_Name"], "SetSexualDebutAge")
        self.assertEqual(event["Disqualifying_Properties"], [])
        self.assertEqual(event["Setting_Type"], "CURRENT_AGE")
        self.assertEqual(event["Distributed_Event_Trigger"], "")

    def test_setsexualdebut_new_intervention_user_defined(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        event = setsexualdebut._new_intervention(camp=self.camp, Setting_Type="USER_SPECIFIED", Age_Years=24,
                                                 Distributed_Event_Trigger="SetSexualDebutAge_Event")
        self.assertEqual(event["class"], "SetSexualDebutAge")
        self.assertEqual(event["Age_Years"], 24)
        self.assertEqual(event["Intervention_Name"], "SetSexualDebutAge")
        self.assertEqual(event["Setting_Type"], "USER_SPECIFIED")
        self.assertEqual(event["Distributed_Event_Trigger"], "SetSexualDebutAge_Event")

    def test_setsexualdebut_new_intervention_user_defined_throw_value_error_1(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        # Setting_Type = "USER_SPECIFIED" requires Age_Years to be set
        with self.assertRaises(ValueError) as err:
            setsexualdebut._new_intervention(camp=self.camp, Setting_Type="USER_SPECIFIED")
        self.assertEqual(str(err.exception), "If 'Setting_Type' == 'USER_SPECIFIED', 'Age_Years' must be set")

    def test_setsexualdebut_new_intervention_user_defined_throw_value_error_2(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        # Setting_Type = "USER_SPECIFIED" requires Age_Years to be set
        with self.assertRaises(ValueError) as err:
            setsexualdebut._new_intervention(camp=self.camp, Setting_Type="CURRENT_AGE", Age_Years=24)
        expected_msg = "'Setting_Type' == 'CURRENT_AGE', sets the age of sexual debut to the current age of the"\
                       " individual when the intervention is received. 'Age_Years' will not be used, please set to None"
        self.assertEqual(str(err.exception), expected_msg)

    def test_setsexualdebut_new_intervention_event_sets_implicits(self):
        """ Test if the intervention generated from default values is correct """
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        event = setsexualdebut.new_intervention_event(camp=self.camp)

        # new_intervention adds _enable_debut_age_as_intervention to camp.implicits to
        # set Sexual_Debut_Age_Setting_Type to "FROM_INTERVENTION".
        parameters = emod_api.schema_to_class.ReadOnlyDict({"Sexual_Debut_Age_Setting_Type": "SOME_VALUE"})
        config = emod_api.schema_to_class.ReadOnlyDict({"parameters": parameters})
        c = self.camp.implicits[0](config)
        self.assertEqual(c["parameters"]["Sexual_Debut_Age_Setting_Type"], "FROM_INTERVENTION")

    def test_setsexualdebut_new_event_default(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        event = setsexualdebut.new_intervention_event(camp=self.camp)

        self.assertEqual(event.Start_Day, 1)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'SetSexualDebutAge')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, 1.0)
        self.assertEqual(event.Event_Coordinator_Config["Target_Demographic"], "Everyone")
        self.assertEqual(event.Event_Coordinator_Config["Target_Gender"], "All")
        self.assertEqual(event.Event_Coordinator_Config["class"], "StandardInterventionDistributionEventCoordinator")
        self.assertEqual(event.Nodeset_Config["class"], "NodeSetAll")
        self.assertEqual(event["class"], "CampaignEvent")

    def test_setsexualdebut_new_event_user_defined(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        start_day = 123
        coverage = 0.5
        target_gender = "Female"
        target_demographic = "ExplicitGender"
        event = setsexualdebut.new_intervention_event(camp=self.camp, Event_Start_Day=start_day, Coverage=coverage,
                                                      Target_Gender=target_gender, Target_Demographic=target_demographic,
                                                      node_ids=None, intervention_name="SetSexualDebutAge",
                                                      disqualifying_properties=['CascadeState:LostForever'],
                                                      new_property_value="CascadeState:OnART")

        self.assertEqual(event.Start_Day, start_day)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'SetSexualDebutAge')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Intervention_Name, "SetSexualDebutAge")
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Disqualifying_Properties, ["CascadeState:LostForever"])
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.New_Property_Value, "CascadeState:OnART")
        self.assertEqual(event.Event_Coordinator_Config["Target_Demographic"], target_demographic)
        self.assertEqual(event.Event_Coordinator_Config["Target_Gender"], "Female")
        self.assertEqual(event.Event_Coordinator_Config["class"], "StandardInterventionDistributionEventCoordinator")
        self.assertEqual(event.Nodeset_Config["class"], "NodeSetAll")
        self.assertEqual(event["class"], "CampaignEvent")


    def test_setsexualdebut_new_event_user_defined_2(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        start_day = 123
        coverage = 0.5
        age_min = 0.123
        age_max = 15.15
        target_demographic = "ExplicitAgeRanges"
        event = setsexualdebut.new_intervention_event(camp=self.camp, Event_Start_Day=start_day, Coverage=coverage,
                                                      Target_Demographic=target_demographic, Target_Age_Min=age_min,
                                                      Target_Age_Max=age_max, node_ids=None)

        self.assertEqual(event.Start_Day, start_day)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'SetSexualDebutAge')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)
        self.assertEqual(event.Event_Coordinator_Config["Target_Age_Min"], age_min)
        self.assertEqual(event.Event_Coordinator_Config["Target_Age_Max"], age_max)
        self.assertEqual(event.Event_Coordinator_Config["Target_Demographic"], target_demographic)
        self.assertEqual(event.Event_Coordinator_Config["Target_Gender"], "All")
        self.assertEqual(event.Event_Coordinator_Config["class"], "StandardInterventionDistributionEventCoordinator")
        self.assertEqual(event.Nodeset_Config["class"], "NodeSetAll")
        self.assertEqual(event["class"], "CampaignEvent")

    def test_setsexualdebut_new_event_user_defined_3(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        start_day = 123
        coverage = 0.5
        age_min = 0.123
        age_max = 15.15
        target_demographic = "ExplicitAgeRangesAndGender"
        event = setsexualdebut.new_intervention_event(camp=self.camp, Event_Start_Day=start_day, Coverage=coverage,
                                                      Target_Demographic=target_demographic, Target_Age_Min=age_min,
                                                      Target_Age_Max=age_max, node_ids=None)

        self.assertEqual(event.Start_Day, start_day)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'SetSexualDebutAge')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)
        self.assertEqual(event.Event_Coordinator_Config["Target_Age_Min"], age_min)
        self.assertEqual(event.Event_Coordinator_Config["Target_Age_Max"], age_max)
        self.assertEqual(event.Event_Coordinator_Config["Target_Demographic"], target_demographic)
        self.assertEqual(event.Event_Coordinator_Config["Target_Gender"], "All")
        self.assertEqual(event.Event_Coordinator_Config["class"], "StandardInterventionDistributionEventCoordinator")
        self.assertEqual(event.Nodeset_Config["class"], "NodeSetAll")
        self.assertEqual(event["class"], "CampaignEvent")

    def test_setsexualdebut_track_sexual_debut_default(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}

        ref = setsexualdebut.track_sexual_debut_intervention(self.camp, Time_Value_Map)
        self.assertEqual(ref["class"], "CampaignEventByYear")
        self.assertEqual(ref["Start_Year"], 1960.5)     # default value
        self.assertEqual(ref["Nodeset_Config"]["class"], "NodeSetAll")
        self.assertEqual(ref["Event_Coordinator_Config"]["class"], "ReferenceTrackingEventCoordinatorTrackingConfig")
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Times"], [1960.0, 1970.0, 1980.0])
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Values"], [0.1, 0.2, 0.3])
        self.assertEqual(ref["Event_Coordinator_Config"]["End_Year"], 2050)   # default value
        self.assertEqual(ref["Event_Coordinator_Config"]["Tracking_Config"]["class"], "IsPostDebut")
        self.assertEqual(ref["Event_Coordinator_Config"]["Tracking_Config"]["Is_Equal_To"], 1)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Gender"], "All")   # default value
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Min"], 0)      # default value
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Max"], 125)    # default value
        self.assertEqual(ref["Event_Coordinator_Config"]["Update_Period"], 30.416667)   # default value
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["class"], "SetSexualDebutAge")
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["Setting_Type"], "CURRENT_AGE")  # default value

    def test_setsexualdebut_track_sexual_debut(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        start_year = 1960.5
        end_year = 2010
        update_period = 123
        target_gender = "Female"
        target_age_min = 14
        target_age_max = 19
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        setting_type = "USER_SPECIFIED"
        age_years = 13

        ref = setsexualdebut.track_sexual_debut_intervention(self.camp, Time_Value_Map, Start_Year=start_year, End_Year=end_year,
                                                             Update_Period=update_period, Target_Gender=target_gender,
                                                             Target_Age_Min=target_age_min, Target_Age_Max=target_age_max,
                                                             Setting_Type=setting_type, Age_Years=age_years)

        self.assertEqual(ref["class"], "CampaignEventByYear")
        self.assertEqual(ref["Start_Year"], start_year)
        self.assertEqual(ref["Nodeset_Config"]["class"], "NodeSetAll")
        self.assertEqual(ref["Event_Coordinator_Config"]["class"], "ReferenceTrackingEventCoordinatorTrackingConfig")
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Times"], [1960.0, 1970.0, 1980.0])
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Values"], [0.1, 0.2, 0.3])
        self.assertEqual(ref["Event_Coordinator_Config"]["End_Year"], end_year)
        self.assertEqual(ref["Event_Coordinator_Config"]["Tracking_Config"]["class"], "IsPostDebut")
        self.assertEqual(ref["Event_Coordinator_Config"]["Tracking_Config"]["Is_Equal_To"], 1)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Gender"], target_gender)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Min"], target_age_min)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Max"], target_age_max)
        self.assertEqual(ref["Event_Coordinator_Config"]["Update_Period"], update_period)
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["class"], "SetSexualDebutAge")
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["Setting_Type"], "USER_SPECIFIED")
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["Age_Years"], age_years)
    # end region SetSexualDebutAge

    def test_set_sexual_debut_with_reftrackercoord(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        event = setsexualdebut._new_intervention(camp=self.camp)
        start_year = 1960.5
        end_year = 2050
        update_period = 30.416667
        target_gender = "Female"
        target_age_min = -1
        target_age_max = 19
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)
        tracking_config_copy = tracking_config.copy()

        ref = reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, event, Time_Value_Map, End_Year=end_year,
                                                          Tracking_Config=tracking_config, Update_Period=update_period,
                                                          Target_Gender=target_gender, Target_Age_Min=target_age_min,
                                                          Target_Age_Max=target_age_max)

        self.assertEqual(ref["class"], "CampaignEventByYear")
        self.assertEqual(ref["Start_Year"], start_year)
        self.assertEqual(ref["Nodeset_Config"]["class"], "NodeSetAll")
        self.assertEqual(ref["Event_Coordinator_Config"]["class"], "ReferenceTrackingEventCoordinatorTrackingConfig")
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Times"], [1960.0, 1970.0, 1980.0])
        self.assertEqual(ref["Event_Coordinator_Config"]["Time_Value_Map"]["Values"], [0.1, 0.2, 0.3])
        self.assertEqual(ref["Event_Coordinator_Config"]["End_Year"], end_year)
        self.assertDictEqual(ref["Event_Coordinator_Config"]["Tracking_Config"], tracking_config_copy)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Gender"], target_gender)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Min"], target_age_min)
        self.assertEqual(ref["Event_Coordinator_Config"]["Target_Age_Max"], target_age_max)
        self.assertEqual(ref["Event_Coordinator_Config"]["Update_Period"], update_period)
        self.assertEqual(ref["Event_Coordinator_Config"]["Intervention_Config"]["class"], "SetSexualDebutAge")

    def test_set_sexual_debut_with_reftrackercoord(self):
        emod_api.schema_to_class.schema_cache = None  # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        event = setsexualdebut._new_intervention(camp=self.camp)
        start_year = 1960.5
        Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}
        tracking_config = emod_api.schema_to_class.get_class_with_defaults("IsPostDebut", self.camp.schema_path)
        prop_rest_within_node = emod_api.schema_to_class.get_class_with_defaults("idmType:PropertyRestrictions",  self.camp.schema_path)
        prop_rest_within_node.append({"Prop": "Value"})

        with self.assertRaises(ValueError) as err:
            reftrackercoord.DistributeIVByRefTrackCoord(self.camp, start_year, event, Time_Value_Map,tracking_config,
                                                        Property_Restrictions=["Prop:Value"],
                                                        Property_Restrictions_Within_Node=prop_rest_within_node)
        self.assertEqual(str(err.exception), "Cannot set both Property_Restrictions and Property_Restrictions_Within_Node")


    def test_set_sexual_debut_new_intervention_as_file(self):
        emod_api.schema_to_class.schema_cache = None    # emod_api.schema_to_class.get_schema() only sets new schema if schema_cache == None

        filename = "test_sexual_debut.json"
        start_day = 12
        setsexualdebut.new_intervention_as_file(camp=self.camp, start_day=start_day, filename=filename)
        
        # open file and check if the intervention is correct
        with open(filename) as sexual_debut_file:
            event = json.load(sexual_debut_file)['Events'][0]

        self.assertEqual(event["Start_Day"], start_day)
        self.assertEqual(event["Event_Coordinator_Config"]["Intervention_Config"]['class'], 'SetSexualDebutAge')
        self.assertEqual(event["Event_Coordinator_Config"]["Demographic_Coverage"], 1.0)
        self.assertEqual(event["Event_Coordinator_Config"]["Individual_Selection_Type"], 'DEMOGRAPHIC_COVERAGE')
        self.assertEqual(event["Event_Coordinator_Config"]["Target_Demographic"], "Everyone")
        self.assertEqual(event["Event_Coordinator_Config"]["Target_Gender"], "All")
        self.assertEqual(event["Event_Coordinator_Config"]["class"], "StandardInterventionDistributionEventCoordinator")
        self.assertEqual(event["Nodeset_Config"]["class"], "NodeSetAll")
        self.assertEqual(event["class"], "CampaignEvent")

    # region ART
    def test_art_new_default(self):
        start_day = 1
        coverage = 1.0
        node_ids = []
        event = art.new_intervention_event(camp=self.camp, start_day=start_day, coverage=coverage, node_ids=None)

        self.assertEqual(event.Start_Day, start_day)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'AntiretroviralTherapy')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)

    def test_art_new_custom(self):
        start_day = 5
        coverage = 0.5
        event = art.new_intervention_event(camp=self.camp, start_day=start_day, coverage=coverage, node_ids=None,
                                           intervention_name="ART", disqualifying_properties=["CascadeState:LostForever"],
                                           new_property_value="CascadeState:OnART")

        self.assertEqual(event.Start_Day, start_day)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'AntiretroviralTherapy')
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Intervention_Name, "ART")
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Disqualifying_Properties,
                         ["CascadeState:LostForever"])
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.New_Property_Value, "CascadeState:OnART")
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)

    def test_art_as_file(self):
        start_day = 5
        coverage = 1.0 # No way to configure
        event = art.new_intervention_as_file(camp=self.camp, start_day=start_day, filename=None)

        self.output_filename = "AntiRetroviralTherapy.json"
        with open(self.output_filename) as art_file:
            event = json.load(art_file)

        event = event['Events'][0]

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'AntiretroviralTherapy')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_art_dropout_custom(self):
        start_day = 2
        coverage = 0.8
        node_ids = [1, 2] # Gonna add this check later

        event = artdropout.new_intervention_event(self.camp, start_day, coverage, node_ids,
                                                  intervention_name="ARTDropout_Intervention",
                                                  disqualifying_properties=["CascadeState:LostForever"],
                                                  new_property_value="CascadeState:OnART")
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ARTDropout')
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Intervention_Name, "ARTDropout_Intervention")
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Disqualifying_Properties,
                         ["CascadeState:LostForever"])
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.New_Property_Value, "CascadeState:OnART")
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_art_dropout_as_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "ARTDropout.json"

        event = artdropout.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as art_dropout_file:
            event = json.load(art_dropout_file)

        event = event['Events'][0]

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ARTDropout')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    # end region

    def test_artstaging_agnostic_custom(self):
        start_day = 2
        coverage = 0.8
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        abw_tvmap = {1: 0.4, 2: 0.5, 3: 0.1}
        abt_tvmap = {1.1: 0.3, 2.1: 0.2, 3.1: 0.5}
        abp_tvmap = {4: 0.95, 3: 0.05}
        cua_tvmap = {5: 0.3, 2: 0.7}
        cbt_tvmap = {2: 0.8, 1: 0.2}
        cbw_tvmap = {1: 0.1, 2: 0.2, 3: 0.7}


        event = artstageagnosticdiag.new_intervention_event(self.camp, pos_event, neg_event, abp_tvmap, abt_tvmap, abw_tvmap, cua_tvmap, cbt_tvmap, cbw_tvmap,start_day, coverage,
                                                            intervention_name="HIVARTStagingCD4AgnosticDiagnostic_Intervention",
                                                            disqualifying_properties=["CascadeState:LostForever"],
                                                            new_property_value="CascadeState:ARTStaging")
        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVARTStagingCD4AgnosticDiagnostic')
        self.assertEqual(intervention_config.Intervention_Name, "HIVARTStagingCD4AgnosticDiagnostic_Intervention")
        self.assertEqual(intervention_config.Disqualifying_Properties, ["CascadeState:LostForever"])
        self.assertEqual(intervention_config.New_Property_Value, "CascadeState:ARTStaging")
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(intervention_config['Negative_Diagnosis_Event'], neg_event)
        self.assertEqual(intervention_config['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")

        abp_map_values = intervention_config['Adult_By_Pregnant']
        self.assertEqual(abp_map_values['Times'], [4, 3])
        self.assertEqual(abp_map_values['Values'], [0.95, 0.05])

        abw_map_values = intervention_config['Adult_By_TB']
        self.assertEqual(abw_map_values['Times'], [1.1, 2.1, 3.1])
        self.assertEqual(abw_map_values['Values'], [0.3, 0.2, 0.5])

        abt_map_values = intervention_config['Adult_By_TB']
        self.assertEqual(abt_map_values['Times'], [1.1, 2.1, 3.1])
        self.assertEqual(abt_map_values['Values'], [0.3, 0.2, 0.5])

        cua_map_values = intervention_config['Child_Treat_Under_Age_In_Years_Threshold']
        self.assertEqual(cua_map_values['Times'], [5, 2])
        self.assertEqual(cua_map_values['Values'], [0.3, 0.7])

        cbt_map_values = intervention_config['Child_By_TB']
        self.assertEqual(cbt_map_values['Times'], [2, 1])
        self.assertEqual(cbt_map_values['Values'], [0.8, 0.2])

    def test_artstaging_agnostic_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "Art_Staging_Agnostic.json"
        event = artstageagnosticdiag.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as art_staging_agnostic_file:
            event = json.load(art_staging_agnostic_file)

        event = event['Events'][0]


        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVARTStagingCD4AgnosticDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], "HIVTestedNegative")
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], "HIVTestedPositive")

    def test_artstagingbycd4diag_custom(self):
        start_day = 2
        coverage = 0.8
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        abw_tvmap = {1: 0.4,2: 0.5, 3: 0.1}
        abt_tvmap = {1: 0.3, 2: 0.2, 3: 0.5}
        abp_tvmap = {5: 0.95, 17.0: 0.05}
        cua_tvmap = {1.1: 0.3, 2.2: 0.7}
        cbt_tvmap = {0: 0.8, 1: 0.2}
        cbw_tvmap = {1.1: 0.1, 1.2: 0.2, 1.3: 0.7}

        event = artstageagnosticdiag.new_intervention_event(self.camp, pos_event, neg_event, abp_tvmap, abt_tvmap, abw_tvmap, cua_tvmap, cbt_tvmap, cbw_tvmap, start_day, coverage)
        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVARTStagingCD4AgnosticDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(intervention_config['Negative_Diagnosis_Event'], neg_event)
        self.assertEqual(intervention_config['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")

        abp_map_values = intervention_config['Adult_By_Pregnant']
        self.assertEqual(abp_map_values['Times'], [5, 17.0])
        self.assertEqual(abp_map_values['Values'], [0.95, 0.05])

        abw_map_values = intervention_config['Adult_By_TB']
        self.assertEqual(abw_map_values['Times'], [1, 2, 3])
        self.assertEqual(abw_map_values['Values'], [0.3, 0.2, 0.5])

        abt_map_values = intervention_config['Adult_By_TB']
        self.assertEqual(abt_map_values['Times'], [1.0, 2.0, 3.0])
        self.assertEqual(abt_map_values['Values'], [0.3, 0.2, 0.5])

        cua_map_values = intervention_config['Child_Treat_Under_Age_In_Years_Threshold']
        self.assertEqual(cua_map_values['Times'], [1.1, 2.2])
        self.assertEqual(cua_map_values['Values'], [0.3, 0.7])

        cbt_map_values = intervention_config['Child_By_TB']
        self.assertEqual(cbt_map_values['Times'], [0, 1])
        self.assertEqual(cbt_map_values['Values'], [0.8, 0.2])

    def test_artstagingbycd4diag_as_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "artstagingbycd4diag.json"

        event = artstageagnosticdiag.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as art_staging_cd4diag_file:
            event = json.load(art_staging_cd4diag_file)

        event = event['Events'][0]


        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVARTStagingCD4AgnosticDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], "HIVTestedNegative")
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], "HIVTestedPositive")

    def test_draw_blood_custom(self):
        pos_event = "BleepBloop"
        start_day = 2
        coverage = 0.8

        event = drawblood.new_intervention_event(camp=self.camp, pos_event=pos_event, start_day=start_day, coverage=coverage,
                                                 intervention_name="HIVDrawBlood_Intervention",
                                                 disqualifying_properties=["CascadeState:LostForever",
                                                                           "CascadeState:OnART",
                                                                           "CascadeState:LinkingToART",
                                                                           "CascadeState:OnPreART",
                                                                           "CascadeState:LinkingToPreART"],
                                                 new_property_value="CascadeState:ARTStaging")

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVDrawBlood')
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Intervention_Name, "HIVDrawBlood_Intervention")
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Disqualifying_Properties,
                         ["CascadeState:LostForever", "CascadeState:OnART", "CascadeState:LinkingToART",
                          "CascadeState:OnPreART", "CascadeState:LinkingToPreART"])
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.New_Property_Value, "CascadeState:ARTStaging")
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")

    def test_draw_blood_file(self):
        start_day = 2
        coverage = 1.0

        self.output_filename = "blooddraw.json"

        event = artstageagnosticdiag.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as blood_file:
            event = json.load(blood_file)

        event = event['Events'][0]


        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVARTStagingCD4AgnosticDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], "HIVTestedPositive")

    def test_malecirc_custom(self):
        start_day = 2
        coverage = 0.8
        node_ids = [1, 2] # Gonna add this check later

        event = malecirc.new_intervention_event(self.camp, start_day, coverage, node_ids,
                                                intervention_name="MaleCircumcision_Intervention",
                                                disqualifying_properties=["CascadeState:LostForever"],
                                                new_property_value=None)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'MaleCircumcision')
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Intervention_Name, "MaleCircumcision_Intervention")
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Disqualifying_Properties, ["CascadeState:LostForever"])
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.New_Property_Value, '')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_malecirc_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "malecirc.json"

        event = malecirc.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as circumcision_file:
            event = json.load(circumcision_file)

        event = event['Events'][0]
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'MaleCircumcision')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_modcoinf_custom(self):
        start_day = 2
        coverage = 0.8
        node_ids = [1, 2] # Gonna add this check later

        event = modcoinf.new_intervention_event(self.camp, start_day, coverage, node_ids)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ModifyStiCoInfectionStatus')
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['New_STI_CoInfection_Status'], 1)
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
    
    def test_modcoinf_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "modcoinf.json"

        event = modcoinf.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as modcoinf_file:
            event = json.load(modcoinf_file)

        event = event['Events'][0]
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ModifyStiCoInfectionStatus')
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['New_STI_CoInfection_Status'], 1)
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_pmtct_custom(self):
        start_day = 2
        coverage = 0.8
        node_ids = [1, 2] # Gonna add this check later

        event = pmtct.new_intervention_event(self.camp, start_day, coverage, node_ids)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'PMTCT')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_pmtct_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "pmtct.json"

        event = pmtct.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as pmtct_file:
            event = json.load(pmtct_file)

        event = event['Events'][0]
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'PMTCT')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_prep_custom(self):
        efficacy_times = [ 0, 365 ]
        efficacy_values = [ 1.0, 1.0 ]
        start_day = 2
        coverage = 0.8
        node_ids = [1, 2] # Gonna add this check later

        event = prep.new_intervention_event(self.camp, efficacy_times, efficacy_values, start_day, coverage, node_ids,
                                            intervention_name="Prep_Intervention",
                                            disqualifying_properties=["CascadeState:LostForever"],
                                            new_property_value="CascadeState:Prep")
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ControlledVaccine')
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Intervention_Name, "Prep_Intervention")
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Disqualifying_Properties, ["CascadeState:LostForever"])
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.New_Property_Value, "CascadeState:Prep")
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_prep_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "prep.json"
        event = prep.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as prep_file:
            event = json.load(prep_file)

        event = event['Events'][0]
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ControlledVaccine')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_random_custom(self):
        start_day = 2
        coverage = 0.8
        choices = {"Yes":0.4, "No":0.6}

        event = randomchoice.new_intervention_event(self.camp, choices, start_day, coverage)

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVRandomChoice')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Choice_Names'], ['Yes', 'No'])
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Choice_Probabilities'], [0.4, 0.6])

    def test_random_file(self):
        start_day = 2
        coverage = 1.0
        choices = {"Yes":0.4, "No":0.6}

        self.output_filename = "random.json"
        event = randomchoice.new_intervention_as_file(self.camp, start_day, choices, self.output_filename)
        
        with open(self.output_filename) as random_file:
            event = json.load(random_file)

        event = event['Events'][0]


        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVRandomChoice')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Choice_Names'], ['Yes', 'No'])
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Choice_Probabilities'], [0.4, 0.6])

    def test_rapiddiag_custom(self):
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        start_day = 2
        coverage = 0.8

        event = rapiddiag.new_intervention_event(self.camp, pos_event, neg_event, start_day, coverage,
                                                 intervention_name="HIVRapidHIVDiagnostic_Intervention",
                                                 disqualifying_properties=["CascadeState:LostForever",
                                                                           "CascadeState:OnART",
                                                                           "CascadeState:LinkingToART",
                                                                           "CascadeState:OnPreART",
                                                                           "CascadeState:LinkingToPreART",
                                                                           "CascadeState:ARTStaging",
                                                                           "CascadeState:TestingOnSymptomatic"],
                                                 new_property_value="CascadeState:TestingOnANC")

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVRapidHIVDiagnostic')
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Intervention_Name, "HIVRapidHIVDiagnostic_Intervention")
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.Disqualifying_Properties,
                         ["CascadeState:LostForever", "CascadeState:OnART", "CascadeState:LinkingToART",
                          "CascadeState:OnPreART", "CascadeState:LinkingToPreART", "CascadeState:ARTStaging",
                          "CascadeState:TestingOnSymptomatic"])
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config.New_Property_Value, "CascadeState:TestingOnANC")
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], neg_event)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")

    def test_rapiddiag_file(self):
        start_day = 2
        coverage = 1.0

        self.output_filename = "rapiddiag.json"

        event = rapiddiag.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as rapiddiag_file:
            event = json.load(rapiddiag_file)

        event = event['Events'][0]

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVRapidHIVDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], "HIVTestedNegative")
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], "HIVTestedPositive")

    def test_sigmoiddiag_custom(self):
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        start_day = 2
        coverage = 0.8
        ramp_min = 0.2
        ramp_max = 0.8
        ramp_midyear = 2005
        ramp_rate = 0.8

        event = sigmoiddiag.new_intervention_event(self.camp, pos_event, neg_event, ramp_min, ramp_max, ramp_midyear, ramp_rate, start_day, coverage,
                                                   intervention_name="HIVSigmoidByYearAndSexDiagnostic_Intervention",
                                                   disqualifying_properties=["CascadeState:LostForever",
                                                                             "CascadeState:OnART",
                                                                             "CascadeState:LinkingToART",
                                                                             "CascadeState:OnPreART",
                                                                             "CascadeState:LinkingToPreART",
                                                                             "CascadeState:ARTStaging",
                                                                             "CascadeState:TestingOnSymptomatic"],
                                                   new_property_value="CascadeState:TestingOnANC")

        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVSigmoidByYearAndSexDiagnostic')
        self.assertEqual(intervention_config.Intervention_Name, "HIVSigmoidByYearAndSexDiagnostic_Intervention")
        self.assertEqual(intervention_config.Disqualifying_Properties,
                         ["CascadeState:LostForever", "CascadeState:OnART", "CascadeState:LinkingToART",
                          "CascadeState:OnPreART", "CascadeState:LinkingToPreART", "CascadeState:ARTStaging",
                          "CascadeState:TestingOnSymptomatic"])
        self.assertEqual(intervention_config.New_Property_Value, "CascadeState:TestingOnANC")
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(intervention_config['Negative_Diagnosis_Event'], neg_event)
        self.assertEqual(intervention_config['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")
        self.assertEqual(intervention_config['Ramp_Max'], ramp_max)
        self.assertEqual(intervention_config['Ramp_Min'], ramp_min)
        self.assertEqual(intervention_config['Ramp_MidYear'], ramp_midyear)
        self.assertEqual(intervention_config['Ramp_Rate'], ramp_rate)

    def test_sigmoiddiag_file(self):
        start_day = 2
        coverage = 1.0

        self.output_filename = "sigmoiddiag.json"

        event = sigmoiddiag.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as sigmoiddiag_file:
            event = json.load(sigmoiddiag_file)

        event = event['Events'][0]

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVSigmoidByYearAndSexDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], "HIVTestedNegative")
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], "HIVTestedPositive")

    def test_stipostdebut_custom(self):
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        start_day = 2
        coverage = 0.8

        event = stipostdebut.new_intervention_event(self.camp, pos_event, neg_event, start_day, coverage)

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'STIIsPostDebut')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], neg_event)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")

    def test_stipostdebut_file(self):
        start_day = 2
        coverage = 1.0

        self.output_filename = "stipostdebut.json"

        event = stipostdebut.new_intervention_as_file(self.camp, start_day, self.output_filename)
        
        with open(self.output_filename) as stipostdebut_file:
            event = json.load(stipostdebut_file)

        event = event['Events'][0]

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'STIIsPostDebut')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], "HIVTestedNegative")
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], "HIVTestedPositive")

    def test_yearandsexdiag_custom(self):
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        start_day = 2
        coverage = 0.8
        tvmap = {15.4:0, 1.6:1}

        event = yearandsexdiag.new_intervention_event(self.camp, pos_event, neg_event, tvmap, start_day, coverage,
                                                      intervention_name="HIVPiecewiseByYearAndSexDiagnostic_Intervention",
                                                      disqualifying_properties=["CascadeState:LostForever",
                                                                                 "CascadeState:OnART",
                                                                                 "CascadeState:LinkingToART",
                                                                                 "CascadeState:OnPreART",
                                                                                 "CascadeState:LinkingToPreART",
                                                                                 "CascadeState:ARTStaging",
                                                                                 "CascadeState:TestingOnSymptomatic"],
                                                      new_property_value="CascadeState:TestingOnANC")
        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVPiecewiseByYearAndSexDiagnostic')
        self.assertEqual(intervention_config.Intervention_Name, "HIVPiecewiseByYearAndSexDiagnostic_Intervention")
        self.assertEqual(intervention_config.Disqualifying_Properties,
                         ['CascadeState:LostForever', 'CascadeState:OnART', 'CascadeState:LinkingToART',
                          'CascadeState:OnPreART', 'CascadeState:LinkingToPreART', 'CascadeState:ARTStaging',
                          'CascadeState:TestingOnSymptomatic'])
        self.assertEqual(intervention_config.New_Property_Value, "CascadeState:TestingOnANC")
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(intervention_config['Negative_Diagnosis_Event'], neg_event)
        self.assertEqual(intervention_config['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")
        timemap = intervention_config['Time_Value_Map']
        self.assertEqual(timemap['Times'], [15.4, 1.6])
        self.assertEqual(timemap['Values'], [0, 1])

    def test_yearandsexdiag_file(self):
        start_day = 2
        coverage = 1.0
        tvmap = {7.1:0, 15.0:1}

        self.output_filename = "yearandsexdiag.json"

        event = yearandsexdiag.new_intervention_as_file(self.camp, start_day, tvmap, self.output_filename)
        
        with open(self.output_filename) as yearandsexdiag_file:
            event = json.load(yearandsexdiag_file)

        event = event['Events'][0]
        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVPiecewiseByYearAndSexDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "HIVTestedNegative")
        self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "HIVTestedPositive")

        timemap = intervention_config['Time_Value_Map']
        self.assertEqual(timemap['Times'], [7.1, 15.0])
        self.assertEqual(timemap['Values'], [0, 1])

    def test_trigger_art(self):
        cascade.reset(self.camp)
        self.camp.campaign_dict['Events'] = []
        timestep = 2
        coverage = 0.7
        trigger = "StartedART"
        cascade.trigger_art(self.camp, timestep, coverage, trigger)
        self.output_file = "TriggerArtAdd.json"
        self.camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        self.assertEqual(len(event_dict['Events']), 1)

        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        intervention = event_coordinator["Intervention_Config"]

        self.assertEqual(event_coordinator["Demographic_Coverage"], coverage)
        self.assertEqual(intervention["Broadcast_Event"], trigger)
        self.assertEqual(intervention["Intervention_Name"], "BroadcastEvent")
        self.assertEqual(event_dict["Events"][0]["Start_Day"], timestep)

    def test_trigger_art_add(self):
        cascade.reset(self.camp)
        trigger = "StartTreatment"
        start_art_event = common.BroadcastEvent(self.camp, trigger)
        self.camp.add(start_art_event)
        cascade.add_art_from_trigger(self.camp, trigger)
        self.output_file = "TriggerArt.json"
        self.camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        self.assertEqual(len(event_dict['Events']), 2)
        self.assertEqual(event_dict["Events"][0]["Broadcast_Event"], trigger)
        event_coordinator = event_dict["Events"][1]["Event_Coordinator_Config"]
        # Should give ART if a StartTreatment signal is observed, broadcasts a "StartedART" signal
        intervention_config = event_coordinator["Intervention_Config"]["Actual_IndividualIntervention_Config"]
        self.assertEqual(intervention_config["class"], "AntiretroviralTherapy")
        self.assertEqual(event_coordinator["Intervention_Config"]['Trigger_Condition_List'], [trigger])

    def test_trigger_art_from_pos_test(self):
        cascade.reset(self.camp)
        trigger = "HIVNewlyDiagnosed"
        cascade.trigger_art_from_pos_test(self.camp, trigger, lag_time=20)
        self.output_file = "TriggerArtPosTest.json"
        self.camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        self.assertEqual(len(event_dict['Events']), 1)
        # Should see that HIVPositiveTest is the trigger, leads to ART intervention
        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        intervention_config = event_coordinator["Intervention_Config"]["Actual_IndividualIntervention_Config"]

        #self.assertEqual(len(intervention_config['Intervention_List']), 1)
        self.assertEqual(intervention_config["Actual_IndividualIntervention_Configs"][0]["Broadcast_Event"], "StartTreatment")
        self.assertEqual(event_coordinator["Intervention_Config"]['Trigger_Condition_List'], [trigger])
        self.assertEqual(intervention_config["Delay_Period_Constant"], 20)

    def test_add_test(self):
        # Check Get tested signal
        # Check for HIV rapid diagnostic test
        cascade.reset(self.camp)
        signal = "NewlySymptomatic"
        cascade.add_test(self.camp, signal)
        self.output_file = "AddTest.json"
        self.camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        intervention_config = event_coordinator["Intervention_Config"]["Actual_IndividualIntervention_Config"]

        #self.assertEqual(len(intervention_config['Intervention_List']), 1)
        self.assertEqual(intervention_config["Actual_IndividualIntervention_Configs"][0]["Intervention_Name"], "HIVRapidHIVDiagnostic")
        self.assertEqual(event_coordinator["Intervention_Config"]['Trigger_Condition_List'], [signal])

    def test_add_choice(self):
        # Check "FeelSick" trigger
        # Check for tested
        cascade.reset(self.camp)
        trigger = "NewlySymptomatic"
        cascade.add_choice(self.camp, trigger)
        self.output_file = "AddMeh.json"
        self.camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        intervention_config = event_coordinator["Intervention_Config"]["Actual_IndividualIntervention_Config"]

        #self.assertEqual(len(intervention_config['Intervention_List']), 1)
        self.assertEqual(intervention_config["Intervention_Name"], "HIVRandomChoice")
        self.assertEqual(intervention_config["Choice_Names"], ["GetTested", "Ignore"])
        self.assertEqual(intervention_config["Choice_Probabilities"], [0.5, 0.5])
        self.assertEqual(event_coordinator["Intervention_Config"]['Trigger_Condition_List'], [trigger])

    def test_seed_infection(self):
        # Simple check that campaign event matches params
        cascade.reset(self.camp)
        timestep = 3
        coverage = 0.8
        cascade.seed_infection(self.camp, timestep, coverage)
        self.output_file = "SeedInfection.json"
        self.camp.save(self.output_file)

        with open(self.output_file) as seed_file:
            event_dict = json.load(seed_file)

        event = event_dict["Events"][0]
        event_coordinator = event["Event_Coordinator_Config"]
        intervention_config = event_coordinator["Intervention_Config"]
        self.assertEqual(event_coordinator['Demographic_Coverage'], coverage)
        self.assertEqual(intervention_config["class"], "OutbreakIndividual")

        self.assertEqual(event['Start_Day'], timestep)

    def test_reftracker(self):
        start_day_distribute = 2.0
        tvmap = {7.1:0, 15.0:1}
        target_age_min = 5
        target_age_max = 25
        target_gender = "Male"

        start_day = 3.0
        # Not checking these, intervention already covered
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        coverage_intervention = 0.8
        update_period = 2

        tracking_intervention = rapiddiag.new_intervention_event(self.camp, pos_event, neg_event, start_day, coverage_intervention,
                                                                 intervention_name="HIVRapidHIVDiagnostic_Intervention",
                                                                 disqualifying_properties=["CascadeState:LostForever",
                                                                                           "CascadeState:OnART",
                                                                                           "CascadeState:LinkingToART",
                                                                                           "CascadeState:OnPreART",
                                                                                           "CascadeState:LinkingToPreART"],
                                                                 new_property_value="CascadeState:ARTStagingDiagnosticTest")


        event = reftracker.DistributeIVByRefTrack(self.camp, start_day_distribute, tracking_intervention, tvmap, Target_Age_Min=target_age_min, Target_Age_Max=target_age_max, Target_Gender=target_gender, Update_Period=update_period)

        event_coordinator = event["Event_Coordinator_Config"]

        intervention_config = event_coordinator["Intervention_Config"]["Event_Coordinator_Config"]["Intervention_Config"]
        self.assertEqual(event_coordinator["Intervention_Config"]["Event_Coordinator_Config"]["class"], "StandardInterventionDistributionEventCoordinator") # Make sure it's distributing this
        self.assertEqual(event_coordinator["Target_Age_Max"], target_age_max)
        self.assertEqual(event_coordinator["Target_Age_Min"], target_age_min)
        self.assertEqual(event_coordinator["Target_Gender"], target_gender)
        self.assertEqual(intervention_config["Intervention_Name"], "HIVRapidHIVDiagnostic_Intervention")
        self.assertEqual(intervention_config.Intervention_Name, "HIVRapidHIVDiagnostic_Intervention")
        self.assertEqual(intervention_config.Disqualifying_Properties,
                         ["CascadeState:LostForever", "CascadeState:OnART", "CascadeState:LinkingToART",
                          "CascadeState:OnPreART", "CascadeState:LinkingToPreART"])
        self.assertEqual(intervention_config.New_Property_Value, "CascadeState:ARTStagingDiagnosticTest")
        self.assertEqual(event_coordinator["Time_Value_Map"]["Times"], [7.1, 15.0])
        self.assertEqual(event_coordinator["Time_Value_Map"]["Values"], [0, 1])
        self.assertEqual(event["Start_Day"], start_day_distribute)
        self.assertEqual(event_coordinator["Update_Period"], update_period)

    def test_reftracker_multiple(self):
        start_day_distribute = 2.0
        tvmap = {7.1:0, 15.0:1}
        target_age_min = 5
        target_age_max = 25
        target_gender = "Male"

        start_day = 3.0
        # Not checking these, intervention already covered
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        coverage_intervention = 0.8

        tracking_intervention = rapiddiag.new_intervention_event(self.camp, pos_event, neg_event, start_day, coverage_intervention)
        tracking_intervention2 = yearandsexdiag.new_intervention_as_file(self.camp, start_day, tvmap)

        event = reftracker.DistributeIVByRefTrack(self.camp, start_day_distribute, [tracking_intervention, tracking_intervention2], tvmap, Target_Age_Min=target_age_min, Target_Age_Max=target_age_max, Target_Gender=target_gender)

        event_coordinator = event["Event_Coordinator_Config"]
        self.assertEqual(len(event_coordinator["Intervention_Config"]["Intervention_List"]), 2)
        self.assertEqual(event_coordinator["Intervention_Config"]["class"], "MultiInterventionDistributor")


    def test_reftracker_file(self):
        start_day = 2.0

        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        coverage_intervention = 0.9

        self.output_filename = "RefTracker.json"

        tracking_intervention = rapiddiag.new_intervention_event(self.camp, pos_event, neg_event, start_day, coverage_intervention)
        event = reftracker.new_intervention_as_file(self.camp, tracking_intervention)

        with open(self.output_filename) as reftracker_file:
            event = json.load(reftracker_file)

        event = event["Events"][0]
        event_coordinator = event["Event_Coordinator_Config"]

        intervention_config = event_coordinator["Intervention_Config"]["Event_Coordinator_Config"]["Intervention_Config"]
        self.assertEqual(event_coordinator["Intervention_Config"]["Event_Coordinator_Config"]["class"], "StandardInterventionDistributionEventCoordinator") # Make sure it's distributing this
        self.assertEqual(intervention_config["Intervention_Name"], "HIVRapidHIVDiagnostic")
        self.assertEqual(event["Start_Day"], 1.0)


if __name__ == '__main__':
    unittest.main()
    
