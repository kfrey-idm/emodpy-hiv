import emod_api

from emodpy_hiv.country_model import Country
from emodpy_hiv.campaign import coc
from typing import Dict, Union
from importlib.abc import Traversable


class ZimbabweTestClass(Country):
    """
    This is a class used for testing the Country class in the emodpy_hiv package.
    """

    def __init__(self):
        super().__init__('Zimbabwe')

    def build_campaign(self,
                       schema_path: str,
                       base_year: float,
                       historical_vmmc_data_filepath: Union[str, Traversable] = None,
                       traditional_male_circumcision_coverages_per_node: Dict[int, float] = None):
        if traditional_male_circumcision_coverages_per_node is None:
            traditional_male_circumcision_coverages_per_node = \
                {1: 0.103}

        return super().build_campaign(schema_path, base_year, historical_vmmc_data_filepath,
                                      traditional_male_circumcision_coverages_per_node)

    def seed_infections(self, campaign):
        """
        Override the default seed_infections method to add one more outbreak individual interventions with coverage 0.1
        to Male individuals aged 15-24 in Risk:HIGH for all nodes.
        """
        # add outbreak individual interventions with coverage 0.1 to all nodes with Risk:HIGH
        coc.seed_infections(campaign=campaign,
                            seeding_node_ids=None,  # all nodes
                            seeding_start_year=1982,
                            seeding_coverage=0.1,
                            seeding_target_property_restrictions=["Risk:HIGH"])
        # add outbreak individual interventions with coverage 0.1 to all nodes with Risk:HIGH and Male individuals
        # aged 15-24.
        coc.seed_infections(campaign=campaign,
                            seeding_node_ids=None,  # all nodes
                            seeding_start_year=1981,
                            seeding_coverage=0.1,
                            seeding_target_property_restrictions=["Risk:HIGH"],
                            seeding_target_gender='Male',
                            seeding_target_min_age=15,
                            seeding_target_max_age=24)

    def add_state_LinkingToART(self, campaign: emod_api.campaign, start_day: int):
        """
        Override the default LinkingToART state to have a ramp_max of 0.95 and ramp_midyear of 2004.
        """
        node_ids = None
        disqualifying_properties = [coc.CascadeState.LOST_FOREVER, coc.CascadeState.ON_ART]
        coc.add_state_LinkingToART(campaign=campaign,
                                   node_ids=node_ids,
                                   disqualifying_properties=disqualifying_properties,
                                   start_day=start_day,
                                   ramp_max=0.95,
                                   ramp_midyear=2004)

