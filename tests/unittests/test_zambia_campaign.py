import unittest

from emodpy_hiv.country_model import Zambia, DefaultZambiaData
import emodpy_hiv.country_data.zambia as zambia_data

from importlib import resources
from pathlib import Path
import sys
import json
import os

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))
import manifest
from country_test import ZimbabweTestClass


class CountryModuleTests(unittest.TestCase):
    def setUp(self):
        print(f"running test: {self._testMethodName}")

    def load_json(self, file_path):
        """Load JSON data from a file."""
        with open(file_path, 'r') as file:
            return json.load(file)

    def count_string_in_json(self, obj, target_string):
        """Recursively count occurrences of target_string in the JSON object."""
        count = 0

        if isinstance(obj, dict):
            for key, value in obj.items():
                count += self.count_string_in_json(key, target_string)
                count += self.count_string_in_json(value, target_string)
        elif isinstance(obj, list):
            for item in obj:
                count += self.count_string_in_json(item, target_string)
        elif isinstance(obj, str):
            if obj == target_string:
                count += 1

        return count

    def search_key_value_pair(self, json_obj, target_key, target_value):
        """Recursively search for a key-value pair in the JSON object."""
        if isinstance(json_obj, dict):
            for key, value in json_obj.items():
                if key == target_key and value == target_value:
                    return True
                if self.search_key_value_pair(value, target_key, target_value):
                    return True
        elif isinstance(json_obj, list):
            for item in json_obj:
                if self.search_key_value_pair(item, target_key, target_value):
                    return True
        return False

    def json_files_not_same(self, file1, file2):
        # Load the JSON files
        json1 = self.load_json(file1)
        json2 = self.load_json(file2)

        # Assert that the JSON data is not the same
        self.assertNotEqual(json1, json2, f"The JSON files: {file1}, {file2} are the same, but they should not be.")
        outbreak_count = self.count_string_in_json(json2, "OutbreakIndividual")
        self.assertEqual(outbreak_count, 2, f"The JSON file: {file2} should contain 2 instances of 'OutbreakIndividual'.")


class TestZambia(CountryModuleTests):
    def setUp(self):
        self.zambia = Zambia()
        self.regression_campaign = Path(__file__).parent.joinpath('inputs/zambia_campaign_regression.json')
        print(f"running test: {self._testMethodName}")

    def test_zambia_build_campaign(self):
        schema_path = manifest.schema_path
        camp = self.zambia.build_campaign(schema_path)
        camp.save('zambia_campaign.json')

        zambia_regression_json = self.load_json(self.regression_campaign)
        zambia_json = self.load_json('zambia_campaign.json')

        # Assert that the campaigns match the regression file
        self.assertDictEqual(zambia_regression_json, zambia_json,
                             "The campaign did not match the regression file.")

        pass


class TestZimbabwe(CountryModuleTests):
    def setUp(self):
        self.zimbabwe = ZimbabweTestClass()
        print(f"running test: {self._testMethodName}")

    def test_zimbabwe_build_campaign(self):
        schema_path = manifest.schema_path
        base_year = 1961
        data_file = resources.files(zambia_data).joinpath("historical_vmmc_data.csv")
        camp = self.zimbabwe.build_campaign(schema_path, base_year, data_file)
        camp.save('zimbabwe_campaign.json')
        pass

    def test_override_seed_infections(self):
        zambia = Zambia()
        zambia_campaign = zambia.build_campaign(manifest.schema_path, 1960.5, DefaultZambiaData.historical_vmmc_data_file)
        zambia_campaign.save('zambia_campaign_2.json')

        zimbabwe = ZimbabweTestClass()
        zimbabwe_campaign = zimbabwe.build_campaign(manifest.schema_path, 1960.5, DefaultZambiaData.historical_vmmc_data_file)
        zimbabwe_campaign.save('zimbabwe_campaign_2.json')

        zambia_json = self.load_json('zambia_campaign_2.json')
        zimbabwe_json = self.load_json('zimbabwe_campaign_2.json')

        # Assert that the campaigns are not the same
        self.assertNotEqual(zambia_json, zimbabwe_json, "The campaigns are the same, but they should not be.")

        # Assert the number of OutbreakIndividuals in the campaigns
        outbreak_count_zimbabwe = self.count_string_in_json(zimbabwe_json, "OutbreakIndividual")
        self.assertEqual(outbreak_count_zimbabwe, 2, "The zimbabwe campaign should contain 2 instances of 'OutbreakIndividual'.")
        outbreak_count_zambia = self.count_string_in_json(zambia_json, "OutbreakIndividual")
        self.assertEqual(outbreak_count_zambia, 1, "The zambia campaign should contain 1 instances of 'OutbreakIndividual'.")

    def test_override_add_state_LinkingToART(self):
        zimbabwe = ZimbabweTestClass()
        data_file = resources.files(zambia_data).joinpath("historical_vmmc_data.csv")
        zimbabwe_campaign = zimbabwe.build_campaign(manifest.schema_path, 1960.5, data_file)
        self.assertTrue(self.search_key_value_pair(zimbabwe_campaign.campaign_dict, "Ramp_Max", 0.95),
                        'The campaign should contain a HIVSigmoidByYearAndSexDiagnostic with "Ramp_Max": 0.95')
        self.assertTrue(self.search_key_value_pair(zimbabwe_campaign.campaign_dict, "Ramp_MidYear", 2004),
                        'The campaign should contain a HIVSigmoidByYearAndSexDiagnostic with "Ramp_MidYear": 2004')
        self.assertFalse(self.search_key_value_pair(zimbabwe_campaign.campaign_dict, "Ramp_Max", 0.8507390283),
                        'The campaign should not contain a HIVSigmoidByYearAndSexDiagnostic with "Ramp_Max": 0.8507390283')
        self.assertFalse(self.search_key_value_pair(zimbabwe_campaign.campaign_dict, "Ramp_MidYear", 1997.4462231708),
                        'The campaign should not contain a HIVSigmoidByYearAndSexDiagnostic with "Ramp_MidYear": 1997.4462231708')


class TestDefaultZambiaData(unittest.TestCase):
    def setUp(self):
        print(f"running test: {self._testMethodName}")

    def test_default_zambia_data(self):
        self.assertTrue(os.path.isdir(DefaultZambiaData.data_root),
                        'DefaultZambiaData.data_root should be a directory')
        self.assertTrue(os.path.isfile(DefaultZambiaData.historical_vmmc_data_file),
                        'historical_vmmc_data.csv is not in the package.')
        self.assertTrue(os.path.isfile(DefaultZambiaData.initial_age_distribution_file),
                        'initial_age_distribution.csv is not in the package.')
        self.assertTrue(os.path.isfile(DefaultZambiaData.initial_population_file),
                        'initial_population.csv is not in the package.')
        self.assertTrue(os.path.isfile(DefaultZambiaData.female_mortality_file),
                        'Uganda_female_mortality.csv is not in the package.')
        self.assertTrue(os.path.isfile(DefaultZambiaData.male_mortality_file),
                        'Uganda_male_mortality.csv is not in the package.')
        self.assertTrue(os.path.isfile(DefaultZambiaData.fertility_file),
                        'Uganda_Fertility_Historical_Projection.csv is not in the package.')


if __name__ == '__main__':
    unittest.main()
