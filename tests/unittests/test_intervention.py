#!/usr/bin/env python
import unittest
import sys
from pathlib import Path
import json
import os

import emod_api.campaign as camp
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
import emodpy_hiv.interventions.random as random
import emodpy_hiv.interventions.rapiddiag as rapiddiag
import emodpy_hiv.interventions.sigmoiddiag as sigmoiddiag
import emodpy_hiv.interventions.stipostdebut as stipostdebut
import emodpy_hiv.interventions.yearandsexdiag as yearandsexdiag
import emodpy_hiv.interventions.cascade_helpers as cascade
import emodpy_hiv.interventions.reftracker as reftracker 

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))
import schema_path_file

# TODO, uncomment positive/negative test events when merged into G-O
class HIVInterventionTest(unittest.TestCase):
    schema_path = schema_path_file.schema_path
    is_debugging = True

    # region unittest setup and teardown method
    @classmethod
    def setUpClass(cls):
        camp.schema_path = cls.schema_path

    def setUp(self):
        print(f"running {self._testMethodName}:")
        self.output_filename = ""
        pass

    def tearDown(self):
        if os.path.exists(self.output_filename) and not self.is_debugging:
            os.remove(self.output_filename)

        print("end of test\n")
        pass
    # endregion

    # region outbreak
    def test_outbreak_new_intervention(self):
        timestep = 365
        coverage = 0.05
        event = ob.new_intervention(timestep=timestep, camp=camp, coverage=coverage)
        self.assertEqual(event.Start_Day, timestep)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'OutbreakIndividual')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)
    # endregion

    # region ART
    def test_art_new_default(self):
        start_day = 1
        coverage = 1.0
        node_ids = []
        event = art.new_intervention_event(camp=camp, start_day=start_day, coverage=coverage, node_ids=None)

        self.assertEqual(event.Start_Day, start_day)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'AntiretroviralTherapy')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)

    def test_art_new_custom(self):
        start_day = 5
        coverage = 0.5
        event = art.new_intervention_event(camp=camp, start_day=start_day, coverage=coverage, node_ids=None)

        self.assertEqual(event.Start_Day, start_day)
        self.assertEqual(event.Event_Coordinator_Config.Intervention_Config['class'], 'AntiretroviralTherapy')
        self.assertEqual(event.Event_Coordinator_Config.Demographic_Coverage, coverage)

    def test_art_as_file(self):
        start_day = 5
        coverage = 1.0 # No way to configure
        event = art.new_intervention_as_file(camp=camp, start_day=start_day, filename=None)

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

        event = artdropout.new_intervention_event(camp, start_day, coverage, node_ids)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ARTDropout')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_art_dropout_as_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "ARTDropout.json"

        event = artdropout.new_intervention_as_file(camp, start_day, self.output_filename)
        
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


        event = artstageagnosticdiag.new_intervention_event(camp, pos_event, neg_event, abp_tvmap, abt_tvmap, abw_tvmap, cua_tvmap, cbt_tvmap, cbw_tvmap,start_day, coverage)
        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVARTStagingCD4AgnosticDiagnostic')
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
        event = artstageagnosticdiag.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = artstageagnosticdiag.new_intervention_event(camp, pos_event, neg_event, abp_tvmap, abt_tvmap, abw_tvmap, cua_tvmap, cbt_tvmap, cbw_tvmap, start_day, coverage)
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

        event = artstageagnosticdiag.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = drawblood.new_intervention_event(camp=camp, pos_event=pos_event, start_day=start_day, coverage=coverage)

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVDrawBlood')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")

    def test_draw_blood_file(self):
        start_day = 2
        coverage = 1.0

        self.output_filename = "blooddraw.json"

        event = artstageagnosticdiag.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = malecirc.new_intervention_event(camp, start_day, coverage, node_ids)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'MaleCircumcision')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_malecirc_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "malecirc.json"

        event = malecirc.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = modcoinf.new_intervention_event(camp, start_day, coverage, node_ids)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ModifyStiCoInfectionStatus')
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['New_STI_CoInfection_Status'], 1)
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
    
    def test_modcoinf_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "modcoinf.json"

        event = modcoinf.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = pmtct.new_intervention_event(camp, start_day, coverage, node_ids)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'PMTCT')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_pmtct_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "pmtct.json"

        event = pmtct.new_intervention_as_file(camp, start_day, self.output_filename)
        
        with open(self.output_filename) as pmtct_file:
            event = json.load(pmtct_file)

        event = event['Events'][0]
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'PMTCT')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_prep_custom(self):
        start_day = 2
        coverage = 0.8
        node_ids = [1, 2] # Gonna add this check later

        event = prep.new_intervention_event(camp, start_day, coverage, node_ids)
        
        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'ControlledVaccine')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)

    def test_prep_file(self):
        start_day = 2
        coverage = 1.0
        node_ids = [1, 2] # Gonna add this check later

        self.output_filename = "prep.json"
        event = prep.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = random.new_intervention_event(camp, choices, start_day, coverage)

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVRandomChoice')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Choices'], choices)

    def test_random_file(self):
        start_day = 2
        coverage = 1.0
        choices = {"Yes":0.4, "No":0.6}

        self.output_filename = "random.json"
        event = random.new_intervention_as_file(camp, start_day, choices, self.output_filename)
        
        with open(self.output_filename) as random_file:
            event = json.load(random_file)

        event = event['Events'][0]


        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVRandomChoice')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Choices'], choices)

    def test_rapiddiag_custom(self):
        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        start_day = 2
        coverage = 0.8

        event = rapiddiag.new_intervention_event(camp, pos_event, neg_event, start_day, coverage)

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['class'], 'HIVRapidHIVDiagnostic')
        self.assertEqual(event['Event_Coordinator_Config']['Demographic_Coverage'], coverage)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Negative_Diagnosis_Event'], neg_event)
        self.assertEqual(event['Event_Coordinator_Config']['Intervention_Config']['Positive_Diagnosis_Event'], pos_event)
        #self.assertEqual(intervention_config['Negative_Diagnosis_Event'], "GP_EVENT_001")
        #self.assertEqual(intervention_config['Positive_Diagnosis_Event'], "GP_EVENT_000")

    def test_rapiddiag_file(self):
        start_day = 2
        coverage = 1.0

        self.output_filename = "rapiddiag.json"

        event = rapiddiag.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = sigmoiddiag.new_intervention_event(camp, pos_event, neg_event, ramp_min, ramp_max, ramp_midyear, ramp_rate, start_day, coverage)

        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVSigmoidByYearAndSexDiagnostic')
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

        event = sigmoiddiag.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = stipostdebut.new_intervention_event(camp, pos_event, neg_event, start_day, coverage)

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

        event = stipostdebut.new_intervention_as_file(camp, start_day, self.output_filename)
        
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

        event = yearandsexdiag.new_intervention_event(camp, pos_event, neg_event, tvmap, start_day, coverage)
        intervention_config = event['Event_Coordinator_Config']['Intervention_Config']

        self.assertEqual(event['Start_Day'], start_day)
        self.assertEqual(intervention_config['class'], 'HIVPiecewiseByYearAndSexDiagnostic')
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

        event = yearandsexdiag.new_intervention_as_file(camp, start_day, tvmap, self.output_filename)
        
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
        cascade.reset(camp)
        camp.campaign_dict['Events'] = []
        timestep = 2
        coverage = 0.7
        trigger = "StartTreatment"
        cascade.trigger_art(camp, timestep, coverage, trigger)
        self.output_file = "TriggerArtAdd.json"
        camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        self.assertEqual(len(event_dict['Events']), 1)

        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        intervention = event_coordinator["Intervention_Config"]["Intervention_List"][0]

        self.assertEqual(event_coordinator["Demographic_Coverage"], coverage)
        self.assertEqual(intervention["Broadcast_Event"], trigger)
        self.assertEqual(intervention["Intervention_Name"], "BroadcastEvent")
        self.assertEqual(event_dict["Events"][0]["Start_Day"], timestep)

    def test_trigger_art_add(self):
        cascade.reset(camp)
        trigger="StartTreatment"
        cascade.add_art_from_trigger(camp, trigger)
        self.output_file = "TriggerArt.json"
        camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        self.assertEqual(len(event_dict['Events']), 1)
        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        # Should give ART if a StartTreatment signal is observed, broadcasts a "StartedART" signal
        intervention_config = event_coordinator["Intervention_Config"]["Actual_IndividualIntervention_Config"]
        self.assertEqual(intervention_config["class"], "AntiretroviralTherapy")
        self.assertEqual(event_coordinator["Intervention_Config"]['Trigger_Condition_List'], [trigger])

    def test_trigger_art_from_pos_test(self):
        cascade.reset(camp)
        trigger = "HIVPositiveTest"
        cascade.trigger_art_from_pos_test(camp, trigger, lag_time=20)
        self.output_file = "TriggerArtPosTest.json"
        camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        self.assertEqual(len(event_dict['Events']), 1)
        # Should see that HIVPositiveTest is the trigger, leads to ART intervention
        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        intervention_config = event_coordinator["Intervention_Config"]["Actual_IndividualIntervention_Config"]

        #self.assertEqual(len(intervention_config['Intervention_List']), 1)
        self.assertEqual(intervention_config["Actual_IndividualIntervention_Configs"][0]["Broadcast_Event"], "StartTreatment")
        self.assertEqual(event_coordinator["Intervention_Config"]['Trigger_Condition_List'], [trigger])
        self.assertEqual(intervention_config["Delay_Period"], 20)

    def test_add_test(self):
        # Check Get tested signal
        # Check for HIV rapid diagnostic test
        cascade.reset(camp)
        signal = "GetTested"
        cascade.add_test(camp, signal)
        self.output_file = "AddTest.json"
        camp.save(self.output_file)

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
        cascade.reset(camp)
        trigger = "FeelSick"
        cascade.add_choice(camp, trigger)
        self.output_file = "AddMeh.json"
        camp.save(self.output_file)

        with open(self.output_file) as art_file:
            event_dict = json.load(art_file)

        event_coordinator = event_dict["Events"][0]["Event_Coordinator_Config"]
        intervention_config = event_coordinator["Intervention_Config"]["Actual_IndividualIntervention_Config"]

        #self.assertEqual(len(intervention_config['Intervention_List']), 1)
        self.assertEqual(intervention_config["Intervention_Name"], "HIVRandomChoice")
        self.assertEqual(intervention_config["Choices"], {"GetTested": 0.5, "Ignore": 0.5})
        self.assertEqual(event_coordinator["Intervention_Config"]['Trigger_Condition_List'], [trigger])
        pass

    def test_seed_infection(self):
        # Simple check that campaign event matches params
        cascade.reset(camp)
        timestep = 3
        coverage = 0.8
        cascade.seed_infection(camp, timestep, coverage)
        self.output_file = "SeedInfection.json"
        camp.save(self.output_file)

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

        tracking_intervention = rapiddiag.new_intervention_event(camp, pos_event, neg_event, start_day, coverage_intervention)


        event = reftracker.DistributeIVByRefTrack(camp, start_day_distribute, tracking_intervention, tvmap, Target_Age_Min=target_age_min, Target_Age_Max=target_age_max, Target_Gender=target_gender, Update_Period=update_period)

        event_coordinator = event["Event_Coordinator_Config"]

        intervention_config = event_coordinator["Intervention_Config"]["Event_Coordinator_Config"]["Intervention_Config"]
        self.assertEqual(event_coordinator["Intervention_Config"]["Event_Coordinator_Config"]["class"], "StandardInterventionDistributionEventCoordinator") # Make sure it's distributing this
        self.assertEqual(event_coordinator["Target_Age_Max"], target_age_max)
        self.assertEqual(event_coordinator["Target_Age_Min"], target_age_min)
        self.assertEqual(event_coordinator["Target_Gender"], target_gender)
        self.assertEqual(intervention_config["Intervention_Name"], "HIVRapidHIVDiagnostic")
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

        tracking_intervention = rapiddiag.new_intervention_event(camp, pos_event, neg_event, start_day, coverage_intervention)
        tracking_intervention2 = yearandsexdiag.new_intervention_as_file(camp, start_day, tvmap)

        event = reftracker.DistributeIVByRefTrack(camp, start_day_distribute, [tracking_intervention, tracking_intervention2], tvmap, Target_Age_Min=target_age_min, Target_Age_Max=target_age_max, Target_Gender=target_gender)

        event_coordinator = event["Event_Coordinator_Config"]
        self.assertEqual(len(event_coordinator["Intervention_Config"]["Intervention_List"]), 2)
        self.assertEqual(event_coordinator["Intervention_Config"]["class"], "MultiInterventionDistributor")


    def test_reftracker_file(self):
        start_day = 2.0

        pos_event = "BleepBloop"
        neg_event = "BloopBleep"
        coverage_intervention = 0.9

        self.output_filename = "RefTracker.json"

        tracking_intervention = rapiddiag.new_intervention_event(camp, pos_event, neg_event, start_day, coverage_intervention)
        event = reftracker.new_intervention_as_file(camp, tracking_intervention)

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
    
