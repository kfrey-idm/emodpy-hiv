import unittest
import pandas as pd

from emod_api import campaign
from emodpy_hiv.interventions import nchooser, malecirc
from pathlib import Path
import sys

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))
import manifest


class TestNChooserEvent(unittest.TestCase):
    def setUp(self):
        # Create a campaign object for testing
        self.campaign_obj = campaign
        self.campaign_obj.reset()
        self.campaign_obj.schema_path = manifest.schema_path

    def test_new_target_distribution(self):
        # Example parameters for testing
        age_ranges_years = [
            [0.99999, 14.9999999, 49.9999, 64.9999],  # Max ages
            [0, 1, 15, 50]  # Min ages
        ]
        num_targeted_females = [0, 0, 0, 0]
        num_targeted_males = [0, 8064.777513, 25054.39959, 179.0207223]

        # Call the function to create a target distribution
        distribution = nchooser.new_target_distribution(
            camp=self.campaign_obj,
            age_ranges_years=age_ranges_years.copy(),
            start_year=2010.0,
            end_year=2010.999,
            num_targeted_females=num_targeted_females.copy(),
            num_targeted_males=num_targeted_males.copy(),
            target_disease_state=[["Not_Have_Intervention"]],
            target_disease_state_has_intervention_name="DMPA_or_control"
        )

        # Perform assertions to check if the distribution was created correctly
        self.assertIsInstance(distribution, dict)  # Check if the result is a dictionary
        self.assertIn("Age_Ranges_Years", distribution)  # Check if the dictionary contains the expected keys

        age_ranges_years_list = []
        for max_age, min_age in zip(*age_ranges_years):
            age_ranges_years_list.append({'Max': max_age, 'Min': min_age})
        self.assertListEqual(distribution['Age_Ranges_Years'], age_ranges_years_list)
        self.assertEqual(distribution['Start_Year'], 2010.0)
        self.assertEqual(distribution['End_Year'], 2010.999)
        self.assertListEqual(distribution['Num_Targeted_Females'], num_targeted_females)
        self.assertListEqual(distribution['Num_Targeted_Males'], num_targeted_males)
        self.assertListEqual(distribution['Target_Disease_State'], [["Not_Have_Intervention"]])
        self.assertEqual(distribution['Target_Disease_State_Has_Intervention_Name'], 'DMPA_or_control')

    def test_add_nchooser_event(self):
        # Create intervention configuration
        intervention_config = malecirc.new_intervention(self.campaign_obj)

        # Create target distributions (use targetdist.new_target_distribution)
        age_ranges_years = [
            [0.99999, 24.9999999, 44.9999, 64.9999],  # Max ages
            [0, 1, 25, 45]  # Min ages
        ]
        num_targeted_females = [0, 0, 0, 0]
        num_targeted_males = [0, 8064.777513, 25054.39959, 179.0207223]
        distribution_1 = nchooser.new_target_distribution(
            camp=self.campaign_obj,
            age_ranges_years=age_ranges_years,
            start_year=2010.0,
            end_year=2010.999,
            num_targeted_females=num_targeted_females,
            num_targeted_males=num_targeted_males,
            target_disease_state=[["Not_Have_Intervention"]],
            target_disease_state_has_intervention_name="DMPA_or_control")
        num_targeted_females_2 = [0, 100, 2000, 300]
        num_targeted_males_2 = [0, 0, 0, 0]
        distribution_2 = nchooser.new_target_distribution(
            camp=self.campaign_obj,
            age_ranges_years=age_ranges_years,
            start_year=2011.0,
            end_year=2011.999,
            num_targeted_females=num_targeted_females_2,
            num_targeted_males=num_targeted_males_2,
            target_disease_state=[["Not_Have_Intervention"]],
            target_disease_state_has_intervention_name="DMPA_or_control")
        distributions = [distribution_1, distribution_2]

        # Add NChooser event to the campaign
        nchooser.add_nchooser_event(self.campaign_obj, distributions, intervention_config, start_day=365)

        # Perform assertions to check if the event was added correctly
        events = self.campaign_obj.campaign_dict['Events']
        self.assertTrue(len(events) == 1)  # Check if one event is added
        added_event = events[0]  # Get the added event
        self.assertEqual(added_event.Start_Day, 365)  # Check the start day
        self.assertEqual(added_event.Nodeset_Config['class'], 'NodeSetAll')

        self.assertEqual(added_event['Event_Coordinator_Config']['class'], 'NChooserEventCoordinatorHIV')
        # Check the 2 Distributions
        actual_distributions = added_event['Event_Coordinator_Config']['Distributions']
        self.assertEqual(len(actual_distributions), 2)
        self.assertDictEqual(distributions[0], actual_distributions[0])
        self.assertDictEqual(distributions[1], actual_distributions[1])
        # Check the 'MaleCircumcision' intervention
        actual_intervention = added_event['Event_Coordinator_Config']['Intervention_Config']
        self.assertEqual(actual_intervention['class'], 'MaleCircumcision')

        # Save json file to disk for debugging.
        self.campaign_obj.save("Nchooser.json")

    def test_add_nchooser_distributed_circumcision_event(self):
        target_disease_state = [["HIV_Negative", "Not_Have_Intervention"]]
        has_intervention_name_exclusion = 'Any_MC'
        data = {'year': [2010, 2010, 2011, 2011],
                'min_age': [1, 15, 1, 15],
                'max_age': [14.999, 49.999, 14.999, 49.999],
                'n_circumcisions': [200, 1300, 290, 1490]}
        distributions = pd.DataFrame.from_dict(data)
        event_name = 'Reference tracking of VMMC'
        # Add NChooser event with male circumcision to the campaign
        nchooser.add_nchooser_distributed_circumcision_event(self.campaign_obj, target_disease_state.copy(),
                                                             has_intervention_name_exclusion, distributions,
                                                             circumcision_reduced_acquire=0.7,
                                                             distributed_event_trigger='Program_VMMC',
                                                             start_day=1, event_name=event_name, node_ids=[1, 2])
        # Perform assertions to check if the event was added correctly
        events = self.campaign_obj.campaign_dict['Events']
        self.assertTrue(len(events) == 1)  # Check if one event is added
        added_event = events[0]  # Get the added event
        self.assertEqual(added_event.Start_Day, 1)  # Check the start day
        self.assertEqual(added_event.Nodeset_Config.Node_List, [1, 2])

        self.assertEqual(added_event['Event_Coordinator_Config']['class'], 'NChooserEventCoordinatorHIV')

        # Check the 2 Distributions
        actual_distributions = added_event['Event_Coordinator_Config']['Distributions']
        self.assertEqual(len(actual_distributions), 2)
        for idx, distribution in enumerate(actual_distributions):
            self.assertEqual(distribution['Target_Disease_State_Has_Intervention_Name'], has_intervention_name_exclusion)
            self.assertEqual(distribution['Target_Disease_State'], target_disease_state)
            age_ranges_years_list = [{'Max': 14.999, 'Min': 1},
                                     {'Max': 49.999, 'Min': 15}]
            self.assertListEqual(distribution['Age_Ranges_Years'], age_ranges_years_list)
            self.assertEqual(distribution['Start_Year'], 2010.0 if idx == 0 else 2011.0)
            self.assertEqual(distribution['End_Year'], 2010.999 if idx == 0 else 2011.999)
            self.assertListEqual(distribution['Num_Targeted_Females'], [0] * 2)
            self.assertListEqual(distribution['Num_Targeted_Males'], [200, 1300] if idx == 0 else [290, 1490])

        # Check the 'MaleCircumcision' intervention
        actual_intervention = added_event['Event_Coordinator_Config']['Intervention_Config']
        self.assertEqual(actual_intervention['class'], 'MaleCircumcision')
        self.assertEqual(actual_intervention['Circumcision_Reduced_Acquire'], 0.7)
        self.assertEqual(actual_intervention['Distributed_Event_Trigger'], 'Program_VMMC')
        self.assertEqual(actual_intervention['Intervention_Name'], has_intervention_name_exclusion)

        self.campaign_obj.save("Nchooser_distributed_circumcision.json")


if __name__ == '__main__':
    unittest.main()
