import unittest

from emod_api import campaign
from emodpy_hiv.interventions import hivmuxer
from pathlib import Path
import sys

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))
import manifest


class TestHIVMuxerEvent(unittest.TestCase):
    def setUp(self):
        # Create a campaign object for testing
        self.campaign_obj = campaign
        self.campaign_obj.reset()
        self.campaign_obj.schema_path = manifest.schema_path

    def test_add_hiv_muxer_event_with_trigger(self):
        start_day = 10
        triggers = ['NewInfectionEvent']
        broadcast_event = 'HCTUptakePostDebut2'
        disqualifying_properties = [
            "CascadeState:LostForever",
            "CascadeState:OnART",
            "CascadeState:LinkingToART",
        ]
        muxer_name = 'HCTUptakePostDebut'
        new_property_value = 'CascadeState:HCTUptakePostDebut'
        delay_distribution = 'EXPONENTIAL_DISTRIBUTION'
        delay_period_exponential = 0.5
        coverage = 0.6
        node_ids = [1, 2, 3]

        # Call the function to add an HIVMuxer event to the campaign
        hivmuxer.add_hiv_muxer_event_with_trigger(
            self.campaign_obj,
            start_day=start_day,
            event_trigger_list=triggers.copy(),
            delay_complete_event=broadcast_event,
            muxer_name=muxer_name,
            delay_distribution=delay_distribution,
            delay_period_exponential=delay_period_exponential,
            disqualifying_properties=disqualifying_properties.copy(),
            demographic_coverage=coverage,
            new_property_value=new_property_value,
            node_ids=node_ids
        )

        # Perform assertions to check if the event was added correctly
        events = self.campaign_obj.campaign_dict['Events']
        self.assertTrue(len(events) == 1)  # Check if one event is added
        added_event = events[0]  # Get the added event
        self.assertEqual(added_event.Start_Day, start_day)  # Check the start day
        # Add more assertions as needed to validate the added event
        self.assertEqual(added_event['Nodeset_Config']['Node_List'], node_ids)
        self.assertEqual(added_event['Event_Coordinator_Config']['Intervention_Config']['Demographic_Coverage'],
                         coverage)

        # Check the HIVMuxer intervention
        actual_intervention = added_event['Event_Coordinator_Config']['Intervention_Config'][
            'Actual_IndividualIntervention_Config']
        self.assertEqual(actual_intervention['class'], 'HIVMuxer')
        self.assertEqual(actual_intervention['Broadcast_Event'], broadcast_event)
        self.assertEqual(actual_intervention['Delay_Period_Distribution'], delay_distribution)
        self.assertEqual(actual_intervention['Delay_Period_Exponential'], delay_period_exponential)
        self.assertEqual(actual_intervention['Disqualifying_Properties'], disqualifying_properties)
        self.assertEqual(actual_intervention['Muxer_Name'], muxer_name)
        self.assertEqual(actual_intervention['Max_Entries'], 1)
        self.assertEqual(actual_intervention['New_Property_Value'], new_property_value)
        # Save the file for debugging
        self.campaign_obj.save("Hivmuxer.json")


if __name__ == '__main__':
    unittest.main()
