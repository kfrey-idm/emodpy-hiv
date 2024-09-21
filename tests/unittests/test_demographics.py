#!/usr/bin/env python
import unittest
import sys
from pathlib import Path
import json
from enum import Enum
import pandas as pd

import emod_api.campaign as camp
import emodpy_hiv.demographics.HIVDemographics as Demographics
import emodpy_hiv.demographics.DemographicsTemplates as DT

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))
import manifest


class RelType(Enum):
    trans = 'TRANSITORY'
    informal = 'INFORMAL'
    marital = 'MARITAL'
    commercial = 'COMMERCIAL'


class HIVDemographicsTest(unittest.TestCase):
    schema_path = manifest.schema_path

    # region unittest setup and teardown method
    @classmethod
    def setUpClass(cls):
        camp.schema_path = cls.schema_path

    def setUp(self):
        print(f"running {self._testMethodName}:")

    def tearDown(self):
        print("end of test\n")
    # endregion

    # region unittests
    def test_from_template_node(self):
        lat = 11
        lon = 22
        pop = 999
        name = "test_name"
        forced_id = 101
        demog = Demographics.from_template_node(lat=lat, lon=lon, pop=pop, name=name, forced_id=forced_id)

        self.assertTrue(isinstance(demog, Demographics.HIVDemographics))
        self.assertEqual(len(demog.implicits), 2)
        self.assertEqual(demog.node_count, 1)

        self.default_test(demog)

        nodes = demog.nodes
        node_attributes = nodes[0].to_dict()['NodeAttributes']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].forced_id, forced_id)
        self.assertEqual(nodes[0].name, name)
        self.assertEqual(node_attributes['InitialPopulation'], pop)
        self.assertEqual(node_attributes["Latitude"], lat)
        self.assertEqual(node_attributes["Longitude"], lon)

    def test_from_pop_csv(self):
        """
                test that verify that the demographics and spatial files can be generated. detailed test is in
        emodapi test_demog_from_pop.py
        """
        pop_filename_in = parent / 'inputs' / 'tiny_facebook_pop_clipped.csv'
        pop_filename_out = parent / "spatial_gridded_pop_dir"
        site = "No_Site"

        demog_filename = parent / 'demographics_from_pop_csv.json'
        spatial_csv_file = pop_filename_out / (site + '_grid.csv')
        spatial_json_file = pop_filename_out / (site + '_grid_id_2_cell_id.json')

        files_to_check = [demog_filename, spatial_csv_file, spatial_json_file]

        for file in files_to_check:
            if file.is_file():  # use missing_ok=True for python 3.8
                file.unlink()

        demog = Demographics.from_pop_csv(pop_filename_in, pop_filename_out=pop_filename_out, site=site)
        self.assertTrue(isinstance(demog, Demographics.HIVDemographics))
        self.assertEqual(len(demog.implicits), 2)
        self.assertEqual(demog.node_count, 5)

        self.default_test(demog)

        demog.generate_file(demog_filename)

        for file in files_to_check:
            self.assertTrue(file.is_file(), msg=f'{file} is not generated.')
        pass

    def test_from_params(self):
        """
            basic test for from_param in emodpy-hiv. more detailed test is in emodapi test_demog.py
        """
        demog_filename = parent / "demographics_from_params.json"
        if demog_filename.is_dir():
            demog_filename.unlink()

        totpop = 9876
        num_nodes = 199
        frac_rural = 0.3
        demog = Demographics.from_params(tot_pop=totpop, num_nodes=num_nodes, frac_rural=frac_rural)
        demog.SetDefaultProperties()
        demog.generate_file(demog_filename)

        self.assertTrue(demog_filename.is_file(), msg=f'{demog_filename} is not generated.')
        with demog_filename.open(mode='r') as demo_file:
            demog_json = json.load(demo_file)
        self.assertEqual(demog_json, demog.raw)

        id_reference = 'from_params'  # hardcoded value
        self.assertEqual(demog.raw['Metadata']['IdReference'], id_reference)
        self.assertEqual(num_nodes, len(demog_json['Nodes']))

        self.default_test(demog)
        pass
    # endregion

    def default_test(self, demog):
        defaults = demog.raw['Defaults']
        self.assertIn('NodeAttributes', defaults)
        self.assertIn('IndividualAttributes', defaults)
        self.assertIn('Society', defaults)

    def test_mortality(self):
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        demog.mortality(parent / "inputs" / "Malawi_male_mortality.csv",
                        parent / "inputs" / "Malawi_female_mortality.csv", predict_horizon=2060,
                        results_scale_factor=1.0/340.0, csv_out=True)
        # male_input = pd.read_csv(parent / "inputs" / "Malawi_male_mortality.csv")
        # female_input = pd.read_csv(parent / "inputs" / "Malawi_male_mortality.csv")
        output = demog.raw['Defaults']

        # Check population group consistency
        male_distribution = output['IndividualAttributes']['MortalityDistributionMale']
        female_distribution = output['IndividualAttributes']['MortalityDistributionMale']

        male_pop_groups = male_distribution['NumPopulationGroups'][0]
        self.assertEqual(len(male_distribution['PopulationGroups'][0]), male_pop_groups)

        female_pop_groups = female_distribution['NumPopulationGroups'][0]
        self.assertEqual(len(female_distribution['PopulationGroups'][0]), female_pop_groups)

        # Check result values consistency 
        self.assertEqual(len(male_distribution['ResultValues']), male_distribution['NumPopulationGroups'][0])
        self.assertEqual(len(female_distribution['ResultValues']), female_distribution['NumPopulationGroups'][0])

        # TODO: Check that predictions are aligned with population sizes
        for i in range(19):
            self.assertGreater(male_distribution['ResultValues'][i][0], male_distribution['ResultValues'][i][18]) # Pop sizes ascending, proportion should go down
            self.assertGreater(female_distribution['ResultValues'][i][0], female_distribution['ResultValues'][i][18])

        # Check prediction horizon is honored
        self.assertLessEqual(max(male_distribution['PopulationGroups'][1]), 2060)
        self.assertLessEqual(max(female_distribution['PopulationGroups'][1]), 2060)

        # Check results scale factor is consistent with parameters
        self.assertEqual(male_distribution['ResultScaleFactor'], 1.0/340.0)
        self.assertEqual(female_distribution['ResultScaleFactor'], 1.0/340.0)

        # TODO: check the mortality distribution against csv data 

    def test_assortivity_default(self):
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        matrix = [[0.3, 0.1, 0.5], [0.4, 0.2, 0.25], [0.2, 0.7, 0.8]]

        demog.apply_assortivity(RelType.trans.value, matrix)
        
        assortivity_area = demog.raw["Defaults"]["Society"]["TRANSITORY"]["Pair_Formation_Parameters"]["Assortivity"]

        self.assertEqual(["LOW", "MEDIUM", "HIGH"], assortivity_area["Axes"])
        self.assertEqual("INDIVIDUAL_PROPERTY", assortivity_area["Group"])
        self.assertEqual("Risk", assortivity_area["Property_Name"])
        self.assertEqual(matrix, assortivity_area["Weighting_Matrix_RowMale_ColumnFemale"])

        for row in assortivity_area["Weighting_Matrix_RowMale_ColumnFemale"]:
            for number in row:
                self.assertTrue(isinstance(number, float), msg=f"Value {number} in matrix is Not a number")

    def test_assortivity_columns_exception(self):
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        big_matrix = [[0.3, 0.1, 0.5, 0.6], [0.4, 0.2, 0.25, 0.7], [0.2, 0.7, 0.8, 0.8]]
        with self.assertRaises(ValueError):
            demog.apply_assortivity(RelType.trans.value, big_matrix)

    def test_assortivity_rows_exception(self):
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        too_many_lists = [[0.3, 0.1, 0.4], [0.3, 0.2, 0.4], [0.5, 0.1, 0.4], [0.6, 0.1, 0.4]]
        with self.assertRaises(ValueError):
            demog.apply_assortivity(RelType.trans.value, too_many_lists)

    def test_set_concurrency_params_by_type_and_risk(self):
        rel_type = RelType.commercial.value
        ip_value = "HIGH"
        max_simul_rels_male = 100
        max_simul_rels_female = 10
        prob_xtra_rel_male = 0.1
        prob_xtra_rel_female = 0.9
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        import emodpy_hiv.demographics.DemographicsTemplates as DT
        DT.add_society_from_template(demog, "PFA-Southern-Africa")
        demog.set_concurrency_params_by_type_and_risk(rel_type, ip_value, max_simul_rels_male=max_simul_rels_male,
                                                      max_simul_rels_female=max_simul_rels_female,
                                                      prob_xtra_rel_male=prob_xtra_rel_male,
                                                      prob_xtra_rel_female=prob_xtra_rel_female)
        concurrency_params = demog.raw['Defaults']["Society"][rel_type]['Concurrency_Parameters'][ip_value]
        self.assertEqual(concurrency_params['Max_Simultaneous_Relationships_Male'], max_simul_rels_male)
        self.assertEqual(concurrency_params['Max_Simultaneous_Relationships_Female'], max_simul_rels_female)
        self.assertEqual(concurrency_params['Prob_Extra_Relationship_Male'], prob_xtra_rel_male)
        self.assertEqual(concurrency_params['Prob_Extra_Relationship_Female'], prob_xtra_rel_female)

        # should not change the default values of other relationship type
        for other_rel_type in RelType:
            if other_rel_type.value != rel_type:
                concurrency_params = demog.raw['Defaults']["Society"][other_rel_type.value]['Concurrency_Parameters']
                # self.assertNotIn(ip_value, concurrency_params.keys())
                concurrency_params = concurrency_params[ip_value]
                self.assertNotEqual(concurrency_params['Max_Simultaneous_Relationships_Male'], max_simul_rels_male)
                self.assertNotEqual(concurrency_params['Max_Simultaneous_Relationships_Female'], max_simul_rels_female)
                self.assertNotEqual(concurrency_params['Prob_Extra_Relationship_Male'], prob_xtra_rel_male)
                self.assertNotEqual(concurrency_params['Prob_Extra_Relationship_Female'], prob_xtra_rel_female)

    def test_set_concurrency_params_by_type_and_risk_wrong_reltype(self):
        rel_type = 'marital'
        ip_value = "High"
        max_simul_rels_male = 100
        max_simul_rels_female = 10
        prob_xtra_rel_male = 0.1
        prob_xtra_rel_female = 0.9
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        with self.assertRaises(ValueError):
            demog.set_concurrency_params_by_type_and_risk(rel_type, ip_value, max_simul_rels_male=max_simul_rels_male,
                                                          max_simul_rels_female=max_simul_rels_female,
                                                          prob_xtra_rel_male=prob_xtra_rel_male,
                                                          prob_xtra_rel_female=prob_xtra_rel_female)

    def test_set_pair_form_params(self):
        rel_type = RelType.marital.value
        new_constant_rate = 0.05
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        demog.set_pair_form_params(rel_type, new_constant_rate=new_constant_rate)
        pair_form_params = demog.raw['Defaults']["Society"][rel_type]['Pair_Formation_Parameters']
        self.assertEqual(pair_form_params['Formation_Rate_Type'], 'CONSTANT')
        self.assertEqual(pair_form_params['Formation_Rate_Constant'], new_constant_rate)

        # should not change the default values of other relationship type
        for other_rel_type in RelType:
            if other_rel_type.value != rel_type:
                pair_form_params = demog.raw['Defaults']["Society"][other_rel_type.value]['Pair_Formation_Parameters']
                self.assertNotEqual(pair_form_params['Formation_Rate_Constant'], new_constant_rate)

    def test_set_coital_act_rate(self):
        rel_type = RelType.informal.value
        rate = 0.9
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        demog.set_coital_act_rate(rel_type, rate)
        relationship_params = demog.raw['Defaults']["Society"][rel_type]['Relationship_Parameters']
        self.assertEqual(relationship_params['Coital_Act_Rate'], rate)

        # should not change the default values of other relationship type
        for other_rel_type in RelType:
            if other_rel_type.value != rel_type:
                relationship_params = demog.raw['Defaults']["Society"][other_rel_type.value]['Relationship_Parameters']
                self.assertNotEqual(relationship_params['Coital_Act_Rate'], rate)

    def test_set_condom_usage_probs(self):
        rel_type = RelType.trans.value
        min_value = 0.2
        mid_value = 2005
        max_value = 0.8
        new_rate = 0.5
        demog = Demographics.from_template_node(lat=0, lon=0, pop=100000, name=1, forced_id=1)
        demog.set_condom_usage_probs(rel_type, min_value, mid_value, max_value, new_rate)
        condom_usage_probs = demog.raw['Defaults']["Society"][rel_type]['Relationship_Parameters']['Condom_Usage_Probability']
        self.assertEqual(condom_usage_probs['Min'], min_value)
        self.assertEqual(condom_usage_probs['Max'], max_value)
        self.assertEqual(condom_usage_probs['Mid'], mid_value)
        self.assertEqual(condom_usage_probs['Rate'], new_rate)

        # should not change the default values of other relationship type
        for other_rel_type in RelType:
            if other_rel_type.value != rel_type:
                condom_usage_probs = demog.raw['Defaults']["Society"][other_rel_type.value]['Relationship_Parameters'][
                    'Condom_Usage_Probability']
                self.assertNotEqual(condom_usage_probs['Min'], min_value)
                self.assertNotEqual(condom_usage_probs['Max'], max_value)
                self.assertNotEqual(condom_usage_probs['Mid'], mid_value)
                self.assertNotEqual(condom_usage_probs['Rate'], new_rate)


if __name__ == '__main__':
    unittest.main()

