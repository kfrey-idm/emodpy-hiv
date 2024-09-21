import json
import unittest
import sys
from enum import Enum
import pandas as pd
from pathlib import Path
from typing import List

from emod_api.demographics.PropertiesAndAttributes import IndividualAttributes

from emodpy_hiv.demographics.hiv_demographics import HIVDemographics
from emodpy_hiv.demographics.relationship_types import RelationshipTypes

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))

ROUNDING_DIGITS = 9


class HIVDemographicsTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fertility(self):
        node_id = 0
        fertility_path = Path(parent, 'inputs', 'Uganda_Fertility_Historical_Projection.csv')
        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        demographics.set_fertility(path_to_csv=fertility_path, node_ids=[node_id])
        node = demographics.get_node_by_id(node_id=node_id)
        distribution = node.individual_attributes.fertility_distribution
        # first, ensure non-specified node(s) are unaffected
        self.assertEqual(demographics.get_node_by_id(node_id=1).individual_attributes.fertility_distribution, None)

        # now verify format/data
        self.assertTrue(isinstance(distribution, IndividualAttributes.FertilityDistribution))
        self.assertEqual(distribution.axis_names, ["age", "year"])
        self.assertEqual(distribution.axis_scale_factors, [365, 1])
        self.assertEqual(distribution.axis_units, ["years", "simulation_year"])  # TODO: change to simulation_year

        self.assertEqual(len(distribution.population_groups), 2)  # first for age, second for years
        ages = [15, 19.99, 20, 24.99, 25, 29.99, 30, 34.99, 35, 39.99, 40, 45.99, 45, 49.99]
        self.assertEqual(distribution.population_groups[0], ages)
        # 1950-2100 by 5 year bins (and .99 entries to stair-step)
        times = [1950, 1954.99, 1955, 1959.99, 1960, 1964.99, 1965, 1969.99, 1970, 1974.99, 1975, 1979.99,
                 1980, 1984.99, 1985, 1989.99, 1990, 1994.99, 1995, 1999.99, 2000, 2004.99, 2005, 2009.99,
                 2010, 2014.99, 2015, 2019.99, 2020, 2024.99, 2025, 2029.99, 2030, 2034.99, 2035, 2039.99,
                 2040, 2044.99, 2045, 2049.99, 2050, 2054.99, 2055, 2059.99, 2060, 2064.99, 2065, 2069.99,
                 2070, 2074.99, 2075, 2079.99, 2080, 2084.99, 2085, 2089.99, 2090, 2094.99, 2095, 2099.99]
        self.assertEqual(distribution.population_groups[1], times)

        self.assertEqual(distribution.result_scale_factor, 2.73972602739726e-06)
        self.assertEqual(distribution.result_units, "annual births per 1000 individuals")

        # ensuring dimensions and (blind) spot-checking arbitrary values from file
        self.assertEqual(len(distribution.result_values), len(ages))
        for index in range(len(distribution.result_values)):
            self.assertEqual(len(distribution.result_values[index]), len(times))
        self.assertEqual(distribution.result_values[1][9], 181.8)  # should be 19.99 year-olds, at year 1974.99
        self.assertEqual(distribution.result_values[10][20], 75.9)  # should be 40 year-olds, at year 2000

    def test_parsed_and_reloaded_fertility(self):
        node_id = 0
        fertility_path = Path(parent, 'inputs', 'parsed_fertility.csv')
        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        demographics.set_fertility(path_to_csv=fertility_path, node_ids=[node_id])
        node = demographics.get_node_by_id(node_id=node_id)
        distribution = node.individual_attributes.fertility_distribution
        # first, ensure non-specified node(s) are unaffected
        self.assertEqual(demographics.get_node_by_id(node_id=1).individual_attributes.fertility_distribution, None)

        # now verify format/data
        self.assertTrue(isinstance(distribution, IndividualAttributes.FertilityDistribution))
        self.assertEqual(distribution.axis_names, ["age", "year"])
        self.assertEqual(distribution.axis_scale_factors, [365, 1])
        self.assertEqual(distribution.axis_units, ["years", "simulation_year"])

        self.assertEqual(len(distribution.population_groups), 2)  # first for age, second for years
        ages = [15, 19.99, 20, 24.99, 25, 29.99, 30, 34.99, 35, 39.99, 40, 45.99, 45, 49.99]
        self.assertEqual(distribution.population_groups[0], ages)
        # 1950-2100 by 5 year bins (and .99 entries to stair-step)
        times = [1950, 1954.99, 1955, 1959.99, 1960, 1964.99, 1965, 1969.99, 1970, 1974.99, 1975, 1979.99,
                 1980, 1984.99, 1985, 1989.99, 1990, 1994.99, 1995, 1999.99, 2000, 2004.99, 2005, 2009.99,
                 2010, 2014.99, 2015, 2019.99, 2020, 2024.99, 2025, 2029.99, 2030, 2034.99, 2035, 2039.99,
                 2040, 2044.99, 2045, 2049.99, 2050, 2054.99, 2055, 2059.99, 2060, 2064.99, 2065, 2069.99,
                 2070, 2074.99, 2075, 2079.99, 2080, 2084.99, 2085, 2089.99, 2090, 2094.99, 2095, 2099.99]
        self.assertEqual(distribution.population_groups[1], times)

        self.assertEqual(distribution.result_scale_factor, 2.73972602739726e-06)
        self.assertEqual(distribution.result_units, "annual births per 1000 individuals")

        # ensuring dimensions and (blind) spot-checking arbitrary values from file
        self.assertEqual(len(distribution.result_values), len(ages))
        for index in range(len(distribution.result_values)):
            self.assertEqual(len(distribution.result_values[index]), len(times))
        self.assertEqual(distribution.result_values[1][9], 189.1)  # 181.8)  # should be 19.99 year-olds, at year 1974.99
        self.assertEqual(distribution.result_values[10][20], 88.3)  # 75.9)  # should be 40 year-olds, at year 2000

    def test_from_template_node(self):
        lat = 11
        lon = 22
        pop = 999
        name = "test_name"
        forced_id = 101
        demog = HIVDemographics.from_template_node(lat=lat, lon=lon, pop=pop, name=name, forced_id=forced_id,
                                                   default_society_template='PFA-Southern-Africa')

        self.assertTrue(isinstance(demog, HIVDemographics))
        self.assertEqual(len(demog.nodes), 1)

        self.default_test(demog)

        nodes = demog.nodes
        node_attributes = nodes[0].to_dict()['NodeAttributes']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].forced_id, forced_id)
        self.assertEqual(nodes[0].name, name)
        self.assertEqual(node_attributes['InitialPopulation'], pop)
        self.assertEqual(node_attributes["Latitude"], lat)
        self.assertEqual(node_attributes["Longitude"], lon)

    def default_test(self, demog):
        defaults = demog.default_node.to_dict()  # ['Defaults']
        self.assertIn('NodeAttributes', defaults)
        self.assertIn('IndividualAttributes', defaults)
        self.assertIn('Society', defaults)

    def _check_mortality_distribution(self, distribution, result_scale_factor, expected_values: List[float]):
        """
                        {'NumPopulationGroups': list(female_data.shape),
                       'AxisNames': ['age', 'year'],
                       'AxisScaleFactors': [365.0, 1],
                       'AxisUnits': ['years', 'years'],
                       'NumDistributionAxes': 2,
                       'PopulationGroups': [age_out_female, years_out_female],
                       'ResultScaleFactor': results_scale_factor,
                       'ResultUnits': 'annual deaths per capita',
                       'ResultValues': female_output.tolist()
                       }
        """
        self.assertEqual(distribution.axis_names, ['age', 'year'])
        self.assertEqual(distribution.axis_scale_factors, [365.0, 1])
        self.assertEqual(distribution.axis_units, ['years', 'years'])  # TODO: change to simulation_year
        self.assertEqual(distribution.result_scale_factor, result_scale_factor)
        self.assertEqual(distribution.result_units, 'annual deaths per capita')

        # now for population groups
        ages = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 100]
        # midpoints of the requested 5-year bins
        years = [1952.5, 1957.5, 1962.5, 1967.5, 1972.5, 1977.5, 1982.5, 1987.5, 1992.5, 1997.5, 2002.5, 2007.5, 2012.5, 2017.5, 2022.5, 2027.5, 2032.5, 2037.5, 2042.5, 2047.5, 2052.5, 2057.5]
        self.assertEqual(len(distribution.population_groups), 2)
        self.assertEqual(distribution.population_groups[0], ages)
        self.assertEqual(distribution.population_groups[1], years)

        # now for result values
        self.assertEqual(len(distribution.result_values), len(ages))  # age-major ordering
        for index in range(len(distribution.result_values)):
            self.assertEqual(len(distribution.result_values[index]), len(years))

        # a couple of regression values here (they are computed from file input, so they are not verification that
        # these values are RIGHT, just that they aren't CHANGING.
        self.assertAlmostEqual(distribution.result_values[5][5], expected_values[0], places=ROUNDING_DIGITS)
        self.assertAlmostEqual(distribution.result_values[6][13], expected_values[1], places=ROUNDING_DIGITS)

    def test_mortality(self):
        node_id = None  # the default node, testing some other bits of code by passing None
        results_scale_factor = 1.0/340.0
        horizon = 2060
        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        demographics.set_mortality(file_male=Path(parent, "inputs", "Malawi_male_mortality.csv"),
                                   file_female=Path(parent, "inputs", "Malawi_female_mortality.csv"),
                                   predict_horizon=horizon, results_scale_factor=results_scale_factor,
                                   node_ids=[node_id])
        node = demographics.get_node_by_id(node_id=node_id)
        male_distribution = node.individual_attributes.mortality_distribution_male
        female_distribution = node.individual_attributes.mortality_distribution_female
        expected_values = [0.00716, 0.002239999999999999]  # indicies [5, 5] and [6, 13]
        self._check_mortality_distribution(distribution=male_distribution, result_scale_factor=results_scale_factor,
                                           expected_values=expected_values)
        expected_values = [0.006369999999999964, 0.002310000000000001]
        self._check_mortality_distribution(distribution=female_distribution, result_scale_factor=results_scale_factor,
                                           expected_values=expected_values)

    def test_parsed_and_mortality_data(self):
        # verify that a known input mortality json is turned into a known input mortality csv file properly.

        # TODO: move this script to somewhere else when there is time
        from inputs import fert_mort_from_json
        input_demographics_file = Path(parent, 'inputs', 'Demographics--mortality_parsing_test.json')
        expected_male_mortality_file = Path(parent, 'inputs', 'expected_male_mortality.csv')
        expected_female_mortality_file = Path(parent, 'inputs', 'expected_female_mortality.csv')

        parsed_df = fert_mort_from_json.parse_mortality_data(source_file=input_demographics_file, gender='Male')
        expected_df = pd.read_csv(expected_male_mortality_file)
        self.assertTrue(parsed_df.eq(expected_df).values.all())

        parsed_df = fert_mort_from_json.parse_mortality_data(source_file=input_demographics_file, gender='Female')
        expected_df = pd.read_csv(expected_female_mortality_file)
        self.assertTrue(parsed_df.eq(expected_df).values.all())

        # now ensure a demographics object can be updated with this mortality data without failing
        node_id = None
        results_scale_factor = 1.0/340.0
        horizon = 2060
        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        demographics.set_mortality(file_male=expected_male_mortality_file,
                                   # yes, I'm using male twice, this is because the infer_natural_mortality() function
                                   # requires identical sets of age/year data for males and females (which my made up
                                   # test does not have, to ensure the parsing code works right).
                                   file_female=expected_male_mortality_file,
                                   predict_horizon=horizon, results_scale_factor=results_scale_factor,
                                   node_ids=[node_id], interval_fit=[1995, 2020])

    def test_assortivity(self):
        # using the default node (specifying no node(s) means the default node)
        rel_type = RelationshipTypes.transitory.value
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1,
                                                   default_society_template='PFA-Southern-Africa')
        matrix = [[0.3, 0.1, 0.5], [0.4, 0.2, 0.25], [0.2, 0.7, 0.8]]

        demog.set_pair_formation_parameters(relationship_type=RelationshipTypes.transitory.value, assortivity_matrix=matrix)

        output = demog.get_node_by_id(node_id=None).to_dict()
        assortivity_area = output["Society"][rel_type]["Pair_Formation_Parameters"]["Assortivity"]

        self.assertEqual(["LOW", "MEDIUM", "HIGH"], assortivity_area["Axes"])
        self.assertEqual("INDIVIDUAL_PROPERTY", assortivity_area["Group"])
        self.assertEqual("Risk", assortivity_area["Property_Name"])
        self.assertEqual(matrix, assortivity_area["Weighting_Matrix_RowMale_ColumnFemale"])

        for row in assortivity_area["Weighting_Matrix_RowMale_ColumnFemale"]:
            for number in row:
                self.assertTrue(isinstance(number, float), msg=f"Value {number} in matrix is Not a number")

    def test_assortivity_columns_exception(self):
        node_id = 0
        rel_type = RelationshipTypes.transitory.value
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        big_matrix = [[0.3, 0.1, 0.5, 0.6], [0.4, 0.2, 0.25, 0.7], [0.2, 0.7, 0.8, 0.8]]

        with self.assertRaises(ValueError):
            demog.set_pair_formation_parameters(relationship_type=rel_type, assortivity_matrix=big_matrix, node_ids=[node_id])

    def test_assortivity_rows_exception(self):
        node_id = 0
        rel_type = RelationshipTypes.transitory.value
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        too_many_lists = [[0.3, 0.1, 0.4], [0.3, 0.2, 0.4], [0.5, 0.1, 0.4], [0.6, 0.1, 0.4]]

        with self.assertRaises(ValueError):
            demog.set_pair_formation_parameters(relationship_type=rel_type, assortivity_matrix=too_many_lists, node_ids=[node_id])

    def test_set_concurrency_params_by_type_and_risk(self):
        node_id = 0
        rel_type = RelationshipTypes.commercial.value
        risk = "HIGH"
        max_simul_rels_male = 100
        max_simul_rels_female = 10
        prob_xtra_rel_male = 0.1
        prob_xtra_rel_female = 0.9
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1,
                                                   default_society_template='PFA-Southern-Africa')
        demog.set_concurrency_params_by_type_and_risk(relationship_type=rel_type,
                                                      risk_group=risk,
                                                      max_simul_rels_male=max_simul_rels_male,
                                                      max_simul_rels_female=max_simul_rels_female,
                                                      prob_xtra_rel_male=prob_xtra_rel_male,
                                                      prob_xtra_rel_female=prob_xtra_rel_female,
                                                      node_ids=[node_id])

        output = demog.get_node_by_id(node_id=node_id).to_dict()
        concurrency_params = output["Society"][rel_type]['Concurrency_Parameters'][risk]

        self.assertEqual(concurrency_params['Max_Simultaneous_Relationships_Male'], max_simul_rels_male)
        self.assertEqual(concurrency_params['Max_Simultaneous_Relationships_Female'], max_simul_rels_female)
        self.assertEqual(concurrency_params['Prob_Extra_Relationship_Male'], prob_xtra_rel_male)
        self.assertEqual(concurrency_params['Prob_Extra_Relationship_Female'], prob_xtra_rel_female)

        # should not change the default values of other relationship type
        for other_rel_type in RelationshipTypes:
            if other_rel_type.value != rel_type:
                concurrency_params = output["Society"][other_rel_type.value]['Concurrency_Parameters']
                # self.assertNotIn(ip_value, concurrency_params.keys())
                concurrency_params = concurrency_params[risk]
                self.assertNotEqual(concurrency_params['Max_Simultaneous_Relationships_Male'], max_simul_rels_male)
                self.assertNotEqual(concurrency_params['Max_Simultaneous_Relationships_Female'], max_simul_rels_female)
                self.assertNotEqual(concurrency_params['Prob_Extra_Relationship_Male'], prob_xtra_rel_male)
                self.assertNotEqual(concurrency_params['Prob_Extra_Relationship_Female'], prob_xtra_rel_female)

    def test_set_pair_form_params(self):
        node_id = 0
        rel_type = RelationshipTypes.marital.value
        new_constant_rate = 0.05
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1,
                                                   default_society_template='PFA-Southern-Africa')
        demog.set_pair_formation_parameters(relationship_type=rel_type, formation_rate=new_constant_rate,
                                            node_ids=[node_id])

        output = demog.get_node_by_id(node_id=node_id).to_dict()
        pair_form_params = output["Society"][rel_type]['Pair_Formation_Parameters']
        self.assertEqual(pair_form_params['Formation_Rate_Type'], 'CONSTANT')
        self.assertEqual(pair_form_params['Formation_Rate_Constant'], new_constant_rate)

        # should not change the default values of other relationship type
        for other_rel_type in RelationshipTypes:
            if other_rel_type.value != rel_type:
                pair_form_params = output["Society"][other_rel_type.value]['Pair_Formation_Parameters']
                self.assertNotEqual(pair_form_params['Formation_Rate_Constant'], new_constant_rate)

    def test_set_coital_act_rate(self):
        node_id = 0
        rel_type = RelationshipTypes.informal.value
        rate = 0.9
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1,
                                                   default_society_template='PFA-Southern-Africa')
        demog.set_relationship_parameters(relationship_type=rel_type, coital_act_rate=rate, node_ids=[node_id])
        output = demog.get_node_by_id(node_id=node_id).to_dict()
        relationship_params = output["Society"][rel_type]['Relationship_Parameters']
        self.assertEqual(relationship_params['Coital_Act_Rate'], rate)

        # should not change the default values of other relationship type
        for other_rel_type in RelationshipTypes:
            if other_rel_type.value != rel_type:
                relationship_params = output["Society"][other_rel_type.value]['Relationship_Parameters']
                self.assertNotEqual(relationship_params['Coital_Act_Rate'], rate)

    def test_set_condom_usage_probs(self):
        node_id = 0
        rel_type = RelationshipTypes.transitory.value
        min_value = 0.2
        mid_value = 2005
        max_value = 0.8
        new_rate = 0.5
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1,
                                                   default_society_template='PFA-Southern-Africa')
        demog.set_relationship_parameters(relationship_type=rel_type, condom_usage_min=min_value,
                                          condom_usage_mid=mid_value, condom_usage_max=max_value,
                                          condom_usage_rate=new_rate, node_ids=[node_id])
        output = demog.get_node_by_id(node_id=node_id).to_dict()
        condom_usage_probs = output["Society"][rel_type]['Relationship_Parameters']['Condom_Usage_Probability']
        self.assertEqual(condom_usage_probs['Min'], min_value)
        self.assertEqual(condom_usage_probs['Max'], max_value)
        self.assertEqual(condom_usage_probs['Mid'], mid_value)
        self.assertEqual(condom_usage_probs['Rate'], new_rate)

        # should not change the default values of other relationship type
        for other_rel_type in RelationshipTypes:
            if other_rel_type.value != rel_type:
                condom_usage_probs = output["Society"][other_rel_type.value]['Relationship_Parameters'][
                    'Condom_Usage_Probability']
                self.assertNotEqual(condom_usage_probs['Min'], min_value)
                self.assertNotEqual(condom_usage_probs['Max'], max_value)
                self.assertNotEqual(condom_usage_probs['Mid'], mid_value)
                self.assertNotEqual(condom_usage_probs['Rate'], new_rate)

    def test_relationship_duration(self):
        node_id = 1
        duration_scale = 0.1234
        duration_heterogeneity = 0.5678
        relationship_type = RelationshipTypes.informal.value

        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name='some_name', forced_id=1,
                                                   default_society_template='PFA-Southern-Africa')
        # we will use this later to ensure default node is unaltered
        default_relationship_parameters = demog.get_node_by_id(node_id=0).society.get_relationship_parameters_by_relationship_type(relationship_type=relationship_type)
        default_lambda = default_relationship_parameters.duration['Lambda']
        default_kappa = default_relationship_parameters.duration['Kappa']

        demog.set_relationship_parameters(relationship_type=relationship_type,
                                          duration_scale=duration_scale,
                                          duration_heterogeneity=duration_heterogeneity,
                                          node_ids=[node_id])
        node = demog.get_node_by_id(node_id=node_id)
        relationship_parameters = node.society.get_relationship_parameters_by_relationship_type(relationship_type=relationship_type)
        self.assertEqual(relationship_parameters.duration['Lambda'], duration_scale)
        self.assertEqual(relationship_parameters.duration['Kappa'], duration_heterogeneity ** -1)

        # ensure default node was not modified
        default_relationship_parameters = demog.get_node_by_id(node_id=0).society.get_relationship_parameters_by_relationship_type(relationship_type=relationship_type)
        self.assertEqual(default_relationship_parameters.duration['Lambda'], default_lambda)
        self.assertEqual(default_relationship_parameters.duration['Kappa'], default_kappa)

    def test_ensure_default_and_regular_nodes_are_updated_independently(self):
        # checks to ensure that when the default node is altered, nodes 1+ are not and vice versa (one test per
        # society data chunk)

        #
        # pair formation parameters test
        #

        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        relationship_type = RelationshipTypes.transitory.value
        matricies_by_node = {0: [[0.31, 0.1, 0.5], [0.41, 0.2, 0.25], [0.21, 0.7, 0.8]],
                             1: [[0.25, 0.1, 0.5], [0.45, 0.2, 0.25], [0.5, 0.7, 0.8]]}

        # This is crazy, but doing the setting TWICE, forward and backward, to ensure neither node-setting overrides
        # the other (both are given a chance to erroneously override the other
        items = list(matricies_by_node.items())
        # forward
        for node_id, matrix in items:
            demographics.set_pair_formation_parameters(relationship_type=relationship_type, assortivity_matrix=matrix,
                                                       node_ids=[node_id])
        # verify each node is still right
        for node_id, matrix in items:
            node = demographics.get_node_by_id(node_id=node_id)
            pfp = node.society.get_pair_formation_parameters_by_relationship_type(relationship_type=relationship_type)
            self.assertEqual(pfp.Assortivity.matrix, matrix)

        # backward
        for node_id, matrix in list(reversed(items)):
            demographics.set_pair_formation_parameters(relationship_type=relationship_type, assortivity_matrix=matrix,
                                                       node_ids=[node_id])
        # verify each node is still right
        for node_id, matrix in list(reversed(items)):
            node = demographics.get_node_by_id(node_id=node_id)
            pfp = node.society.get_pair_formation_parameters_by_relationship_type(relationship_type=relationship_type)
            self.assertEqual(pfp.Assortivity.matrix, matrix)

        #
        # concurrency parameters
        #

        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        relationship_type = RelationshipTypes.informal.value
        risk = 'MEDIUM'
        values_by_node = {0: {'max_simul_rels_male': 1000, 'max_simul_rels_female': 1001,
                              'prob_xtra_rel_male': 1002.0, 'prob_xtra_rel_female': 1003.0},
                          1: {'max_simul_rels_male': 1004, 'max_simul_rels_female': 1005,
                              'prob_xtra_rel_male': 1006.0, 'prob_xtra_rel_female': 1007.0}}
        renaming_dict = {
            'max_simul_rels_male': 'max_simultaneous_relationships_male',
            'max_simul_rels_female': 'max_simultaneous_relationships_female',
            'prob_xtra_rel_male': 'probability_extra_relationship_male',
            'prob_xtra_rel_female': 'probability_extra_relationship_female'
        }
        # This is crazy, but doing the setting TWICE, forward and backward, to ensure neither node-setting overrides
        # the other (both are given a chance to erroneously override the other
        items = list(values_by_node.items())
        # forward
        for node_id, value_dict in items:
            demographics.set_concurrency_params_by_type_and_risk(relationship_type=relationship_type, risk_group=risk,
                                                                 node_ids=[node_id], **value_dict)
        # verify each node is still right
        for node_id, value_dict in items:
            node = demographics.get_node_by_id(node_id=node_id)
            cp = node.society.get_concurrency_parameters_by_relationship_type_and_risk(relationship_type=relationship_type,
                                                                                       risk=risk)
            for attribute, value in value_dict.items():
                self.assertEqual(getattr(cp, renaming_dict[attribute]), value)

        # backward
        for node_id, value_dict in list(reversed(items)):
            demographics.set_concurrency_params_by_type_and_risk(relationship_type=relationship_type, risk_group=risk,
                                                                 node_ids=[node_id], **value_dict)
        # verify each node is still right
        for node_id, value_dict in list(reversed(items)):
            node = demographics.get_node_by_id(node_id=node_id)
            cp = node.society.get_concurrency_parameters_by_relationship_type_and_risk(relationship_type=relationship_type,
                                                                                       risk=risk)
            for attribute, value in value_dict.items():
                self.assertEqual(getattr(cp, renaming_dict[attribute]), value)

        #
        # relationship parameters
        #

        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        relationship_type = RelationshipTypes.marital.value
        values_by_node = {0: {'coital_act_rate': 500, 'condom_usage_min': 501, 'condom_usage_mid': 502,
                              'condom_usage_max': 503, 'condom_usage_rate': 504, 'duration_scale': 505,
                              'duration_heterogeneity': 506},
                          1: {'coital_act_rate': 507, 'condom_usage_min': 508, 'condom_usage_mid': 509,
                              'condom_usage_max': 510, 'condom_usage_rate': 511, 'duration_scale': 512,
                              'duration_heterogeneity': 513}
                          }
        # This is crazy, but doing the setting TWICE, forward and backward, to ensure neither node-setting overrides
        # the other (both are given a chance to erroneously override the other
        items = list(values_by_node.items())
        # forward
        for node_id, value_dict in items:
            demographics.set_relationship_parameters(relationship_type=relationship_type, node_ids=[node_id],
                                                     **value_dict)
        # verify each node is still right
        for node_id, value_dict in items:
            node = demographics.get_node_by_id(node_id=node_id)
            rp = node.society.get_relationship_parameters_by_relationship_type(relationship_type=relationship_type)
            comparable = {
                'coital_act_rate': getattr(rp, 'coital_act_rate'),
                'condom_usage_min': rp.condom_usage.min,
                'condom_usage_mid': rp.condom_usage.mid,
                'condom_usage_max': rp.condom_usage.max,
                'condom_usage_rate': rp.condom_usage.rate,
                'duration_scale': rp.duration['Lambda'],
                'duration_heterogeneity': rp.duration['Kappa'] ** -1
            }
            for attribute, value in value_dict.items():
                # self.assertEqual(comparable[attribute], value)
                self.assertEqual(round(comparable[attribute], ROUNDING_DIGITS), round(value, ROUNDING_DIGITS))

        # backward
        for node_id, value_dict in list(reversed(items)):
            demographics.set_relationship_parameters(relationship_type=relationship_type, node_ids=[node_id],
                                                     **value_dict)
        # verify each node is still right
        for node_id, value_dict in list(reversed(items)):
            node = demographics.get_node_by_id(node_id=node_id)
            rp = node.society.get_relationship_parameters_by_relationship_type(relationship_type=relationship_type)
            comparable = {
                'coital_act_rate': getattr(rp, 'coital_act_rate'),
                'condom_usage_min': rp.condom_usage.min,
                'condom_usage_mid': rp.condom_usage.mid,
                'condom_usage_max': rp.condom_usage.max,
                'condom_usage_rate': rp.condom_usage.rate,
                'duration_scale': rp.duration['Lambda'],
                'duration_heterogeneity': rp.duration['Kappa'] ** -1
            }
            for attribute, value in value_dict.items():
                # self.assertEqual(comparable[attribute], value)
                self.assertEqual(round(comparable[attribute], ROUNDING_DIGITS), round(value, ROUNDING_DIGITS))

    def test_adding_an_IP_distribution(self):
        # testing the core function called by adding risk/HCA/cascade distributions
        node_id = 0
        property_name = "Washington State"
        values = ["West of Cascades", "East of Cascades"]
        distribution = [0.7, 0.3]
        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        demographics._add_or_update_individual_property_distribution(property_name=property_name,
                                                                     values=values,
                                                                     distribution=distribution,
                                                                     node_ids=[0])
        node = demographics.get_node_by_id(node_id=node_id)
        self.assertTrue(node.has_individual_property(property_key=property_name))
        ip = node.get_individual_property(property_key=property_name)
        self.assertEqual(ip.property, property_name)
        self.assertEqual(ip.values, ip.values)
        self.assertEqual(ip.initial_distribution, distribution)

        # ensure adding again causes no problems; just overwrites the existing one
        values = ["San Juan Islands", "Everything else"]
        distribution = [0.01, 0.99]
        demographics._add_or_update_individual_property_distribution(property_name=property_name,
                                                                     values=values,
                                                                     distribution=distribution,
                                                                     node_ids=[0])
        node = demographics.get_node_by_id(node_id=node_id)
        self.assertTrue(node.has_individual_property(property_key=property_name))
        ip = node.get_individual_property(property_key=property_name)
        self.assertEqual(ip.property, property_name)
        self.assertEqual(ip.values, ip.values)
        self.assertEqual(ip.initial_distribution, distribution)

    def test_nonexistant_node_access_throws_exception(self):
        node_id = 99
        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)
        self.assertRaises(HIVDemographics.UnknownNodeException, demographics.get_node_by_id, node_id=node_id)

    def test_from_population_dataframe(self):
        csv_file = Path(parent, 'inputs', 'initial_population.csv')
        df = pd.read_csv(csv_file)
        demographics = HIVDemographics.from_population_dataframe(df=df, default_society_template='PFA-Southern-Africa')

        self.assertEqual(len(demographics.implicits), 1)  # enable births
        self.assertEqual(len(demographics.migration_files), 0)
        self.assertEqual(len(demographics.nodes), 10)

        # Expected node populations & names
        expected = {
            1: {'population': 304498, 'name': 'Central'},
            2: {'population': 459461, 'name': 'Copperbelt'},
            3: {'population': 371018, 'name': 'Eastern'},
            4: {'population': 231074, 'name': 'Luapula'},
            5: {'population': 510456, 'name': 'Lusaka'},
            6: {'population': 165784, 'name': 'Muchinga'},
            7: {'population': 169368, 'name': 'Northwestern'},
            8: {'population': 257607, 'name': 'Northern'},
            9: {'population': 370381, 'name': 'Southern'},
            10: {'population': 210352, 'name': 'Western'},
        }
        for node_id, expected_dict in expected.items():
            node = demographics.get_node_by_id(node_id=node_id)
            self.assertEqual(node.id, node_id)
            self.assertEqual(node.name, expected_dict['name'])
            self.assertEqual(node.pop, expected_dict['population'])

        # todo: what should the default node values be in this test, if any?
        # TODO: add check of individual attributes on the nodes
        # TODO: add check of individual properties on the nodes
        # TODO: maybe just these on test_load_zambia_country_model_alpha?

    def test_ensure_raw_use_is_prevented(self):
        # testing the core function called by adding risk/HCA/cascade distributions
        demographics = HIVDemographics.from_template_node(lat=0, lon=0, pop=100000, name="some_name", forced_id=1)

        # This attribute of emod-api Demographics is forcefully deprecated to prevent data loss in HIV
        access_raw_attribute = lambda: demographics.raw
        self.assertRaises(AttributeError, access_raw_attribute)

    # @unittest.skip(reason='Incomplete test for now')
    def test_load_zambia_country_model_alpha(self):
        from emodpy_hiv.demographics.country_models import load_country_model_demographics_default
        demographics = load_country_model_demographics_default(country_model='zambia')
        self.assertEqual(len(demographics.implicits), 5)  # enable_births, age_complex, fertility_age_year, and 2xmortality_age_gend_y
        self.assertEqual(len(demographics.migration_files), 0)

        # load the source demographics file for regression checking
        regression_file = Path(parent, 'inputs', 'Demographics--zambia_regression.json')
        with open(regression_file, 'rb') as f:
            expected = json.load(f)

        # check important per-node information
        self.assertEqual(len(demographics.nodes), len(expected['Nodes']))

        expected_nodes_by_id = {node_dict['NodeID']: node_dict for node_dict in expected['Nodes']}
        for node in demographics.nodes:
            expected_node = expected_nodes_by_id[node.id]
            self.assertEqual(node.id, expected_node['NodeID'])
            self.assertEqual(node.name, expected_node['NodeName'])
            self.assertEqual(node.pop, expected_node['NodeAttributes']['InitialPopulation'])

        # ensure the expected IPs are set (for zambia, all on the default node)
        for node in demographics.nodes:
            self.assertEqual(len(node.individual_properties), 0)
        expected_ips_by_key = {ip_dict['Property']: ip_dict for ip_dict in expected['Defaults']['IndividualProperties']}
        self.assertEqual(len(demographics.default_node.individual_properties), len(expected_ips_by_key))
        for ip in demographics.default_node.individual_properties:
            expected_ip = expected_ips_by_key[ip.property]
            self.assertEqual(ip.property, expected_ip['Property'])
            self.assertEqual(ip.values, expected_ip['Values'])
            self.assertEqual(ip.initial_distribution, expected_ip['Initial_Distribution'])
            transitions = [] if ip.transitions is None else ip.transitions
            self.assertEqual(transitions, expected_ip.get('Transitions', []))
            transmission_matrix = [] if ip.transmission_matrix is None else ip.transmission_matrix
            self.assertEqual(transmission_matrix, expected_ip.get('TransmissionMatrix', []))

        # check all the individual attributes and ensure none are on non-default node (as is the case for zambia)
        individual_attributes = demographics.default_node.individual_attributes
        # TODO: another way to do this?
        # self.assertEqual(len(individual_attributes), 4)  # fertility, age distribution, male mortality, female mortality
        # for node in demographics.nodes:
        #     self.assertEqual(len(node.individual_attributes), 0)

        # TODO: finish the below

        # verify fertility data is the same
        expected_fertility = expected['Defaults']['IndividualAttributes']['FertilityDistribution']
        fertility = demographics.default_node.individual_attributes.fertility_distribution
        self.assertEqual(fertility.axis_names, expected_fertility['AxisNames'])
        self.assertEqual(fertility.axis_units, expected_fertility['AxisUnits'])
        self.assertEqual(fertility.axis_scale_factors, expected_fertility['AxisScaleFactors'])
        self.assertEqual(fertility.result_units, expected_fertility['ResultUnits'])
        self.assertAlmostEqual(fertility.result_scale_factor, expected_fertility['ResultScaleFactor'],
                               places=ROUNDING_DIGITS)
        # self.assertEqual(fertility.population_groups, expected_fertility['PopulationGroups'])  # TODO: off by .009
        # TODO: fertility result values mismatch with regression file. 'expected' value seems off
        # self.assertEqual(fertility.result_values, expected_fertility['ResultValues'])

        # verify the male mortality data is the same
        expected_male_mortality = expected['Defaults']['IndividualAttributes']['MortalityDistributionMale']
        male_mortality = demographics.default_node.individual_attributes.mortality_distribution_male
        self.assertEqual(male_mortality.axis_names, expected_male_mortality['AxisNames'])
        # TODO: this line is broken; need to decide on years vs simulation_year and fix-up emod-api, then restore this test line
        # self.assertEqual(male_mortality.axis_units, expected_male_mortality['AxisUnits'])
        self.assertEqual(male_mortality.axis_scale_factors, expected_male_mortality['AxisScaleFactors'])

        self.assertEqual(male_mortality.result_units, expected_male_mortality['ResultUnits'])
        self.assertAlmostEqual(male_mortality.result_scale_factor, expected_male_mortality['ResultScaleFactor'],
                               places=ROUNDING_DIGITS)
        # self.assertEqual(male_mortality.population_groups, expected_male_mortality['PopulationGroups'])  # TODO: difference in length of years list, difference in age bins (expected include 0 and all .999's and has fewer year bins)
        # self.assertEqual(male_mortality.result_values, expected_male_mortality['ResultValues'])  # TODO: values are not the same, independent of the PopulationGroups

        # verify the female mortality data is the same
        expected_female_mortality = expected['Defaults']['IndividualAttributes']['MortalityDistributionFemale']
        female_mortality = demographics.default_node.individual_attributes.mortality_distribution_female
        self.assertEqual(female_mortality.axis_names, expected_female_mortality['AxisNames'])
        # TODO: this line is broken; need to decide on years vs simulation_year and fix-up emod-api, then restore this test line
        # self.assertEqual(female_mortality.axis_units, expected_female_mortality['AxisUnits'])
        self.assertEqual(female_mortality.axis_scale_factors, expected_female_mortality['AxisScaleFactors'])

        self.assertEqual(female_mortality.result_units, expected_female_mortality['ResultUnits'])
        self.assertAlmostEqual(female_mortality.result_scale_factor, expected_female_mortality['ResultScaleFactor'],
                               places=ROUNDING_DIGITS)
        # self.assertEqual(female_mortality.population_groups, expected_female_mortality['PopulationGroups'])  # TODO: difference in length of years list, difference in age bins (expected include 0 and all .999's and has fewer year bins)
        # self.assertEqual(female_mortality.result_values, expected_female_mortality['ResultValues'])  # TODO: values are not the same, independent of the PopulationGroups

        # verify the age distributions are the same
        expected_age_distribution = expected['Defaults']['IndividualAttributes']['AgeDistribution']
        age_distribution = demographics.default_node.individual_attributes.age_distribution
        # missing in emod-api but not significant, just in-file documentation

        # self.assertEqual(age_distribution.result_units, expected_age_distribution['ResultUnits'])
        self.assertAlmostEqual(age_distribution.result_scale_factor, expected_age_distribution['ResultScaleFactor'],
                               places=ROUNDING_DIGITS)
        self.assertEqual(age_distribution.result_values, expected_age_distribution['ResultValues'])
        self.assertEqual([round(value, ROUNDING_DIGITS) for value in age_distribution.distribution_values],
                         [round(value, ROUNDING_DIGITS) for value in expected_age_distribution['DistributionValues']])


        # ensure there are no node attributes (by default in zambia model)

        # # default build has no node attribtues on any node
        # for node in demographics._all_nodes:
        #     node_attributes = node.node_attributes.to_dict()
        #     self.assertEqual(node.node_attributes.to_dict(), {})

        # TODO: now dump to a dict and compare (should still work out)
        # raise NotImplementedError('In progress test development (but currently skipping, so it is fine, right??')


if __name__ == '__main__':
    unittest.main()

