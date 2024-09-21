from pathlib import Path
from typing import Dict

import pandas as pd

from emod_api.demographics.PropertiesAndAttributes import IndividualAttributes, IndividualProperty

from emodpy_hiv.demographics import DemographicsTemplates
from emodpy_hiv.demographics.hiv_demographics import HIVDemographics

from emodpy_hiv.country_model import DefaultZambiaData
_data_root = DefaultZambiaData.data_root.parent


# TODO: yeah, yeah, this shouldn't be represented like this. Just a convenient way to organize during development.
_registry = {
    "zambia": {
        "initial_population_file": "initial_population.csv",
        "age_distribution_file": "initial_age_distribution.csv",
        "fertility_file": "parsed_fertility.csv",
        "male_mortality_file": "parsed_mortality--male.csv",
        "female_mortality_file": "parsed_mortality--female.csv",
        "default_society_template": "PFA-Southern-Africa",
        "individual_properties": [
            {
                "property": "Risk",
                "values": ["LOW", "MEDIUM", "HIGH"],
                "initial_distribution": [0.85, 0.15, 0],
                "transitions": None,
                "transmission_matrix": None
            },
            {
                "property": "CascadeState",
                "values": ["", "ARTStaging", "ARTStagingDiagnosticTest", "LinkingToART", "LinkingToPreART", "OnART", "OnPreART",
                  "HCTTestingLoop", "HCTUptakeAtDebut", "HCTUptakePostDebut", "TestingOnANC", "TestingOnChild6w",
                  "TestingOnSymptomatic", "LostForever"],
                "initial_distribution": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "transitions": None,
                "transmission_matrix": None
            },
            {
                "property": "Accessibility",
                "values": ["Yes", "No"],
                "initial_distribution": [0.8, 0.2],
                "transitions": None,
                "transmission_matrix": None
            }
        ],
        "node_attributes": []  # TODO: how to include/load node properties? (node attributes?)
    }
}

########################################################################################################################
# TODO:
#  NOTE: The following is simply copy/pasted in for now to enable sketch of 'country models' to work. This is NOT
#  the canonical place for this code.

import re


class AgeBin:

    class InvalidAgeBinFormat(Exception): pass
    class NotMergeable(Exception): pass

    STR_FORMAT = '[%s%s%s)'
    # e.g. [15, 49) -> [(15)(, )(49))  delimiter must contain no numeric characters or '.'
    SPLIT_REGEX = re.compile('^\[(?P<start>[0-9.]+)(?P<delimiter>[^0-9.]+)(?P<end>[0-9.]+)\)$')
    DEFAULT_DELIMITER = ':'
    ALL = 'all'

    def __init__(self, start, end, delimiter=None):
        try:
            self.start = int(start)
        except ValueError:
            self.start = float(start)

        try:
            self.end = int(end)
        except ValueError:
            self.end = float(end)

        self.delimiter = delimiter or self.DEFAULT_DELIMITER

    def merge(self, other_bin):
        """
        Create a single AgeBin representing two adjacent AgeBins. Keeps delimiter of 'self'.
        :param other_bin: merge self with this other AgeBin object (self is lower age than other_bin)
        :return: an AgeBin object with delimiter set to self.delimiter (not other_bin.delimiter)
        """
        other_bin = other_bin if isinstance(other_bin, AgeBin) else AgeBin.from_string(other_bin)
        if self.end != other_bin.start:
            raise self.NotMergeable('AgeBin objects must be age-adjacent to be merged: %s %s' % (self, other_bin))
        return type(self)(start=self.start, end=other_bin.end, delimiter=self.delimiter)

    def contains(self, other_bin):
        """
        Is other_bin contained within the bounds of self?
        :param other_bin: an AgeBin object
        :return: True/False
        """
        other_bin = other_bin if isinstance(other_bin, AgeBin) else AgeBin.from_string(other_bin)
        return self.start <= other_bin.start and self.end >= other_bin.end

    def to_tuple(self):
        return tuple([self.start, self.end])

    def __str__(self):
        return self.STR_FORMAT % (self.start, self.delimiter, self.end)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        return not (self == other)

    @classmethod
    def _split_string(cls, str):
        match = cls.SPLIT_REGEX.match(str)
        return match['start'], match['delimiter'], match['end']

    @classmethod
    def from_string(cls, str):
        try:
            start, delimiter, end = cls._split_string(str=str)
        except (KeyError, IndexError, TypeError) as e:
            example = cls(15,49)
            raise cls.InvalidAgeBinFormat('Required AgeBin format is e.g.: %s' % example)
        return cls(start=start, end=end, delimiter=delimiter)

    @classmethod
    def merge_bins(cls, bins):
        if len(bins) == 0:
            raise cls.NotMergeable('No AgeBins provided for merging.')

        # tolerant of string and object representations
        bins = [bin if isinstance(bin, AgeBin) else cls.from_string(bin) for bin in bins]
        bins = sorted(bins, key=lambda b: b.start)

        merged_bin = bins[0]
        for bin in bins[1:]:
            merged_bin = merged_bin.merge(bin)
        return merged_bin

    @classmethod
    def can_upsample_bins(cls, bins, target_bin):
        # tolerant of string and object representations
        bins = [bin if isinstance(bin, AgeBin) else cls.from_string(bin) for bin in bins]
        target_bin = target_bin if isinstance(target_bin, AgeBin) else cls.from_string(target_bin)

        # remove bins not within our target age range
        bins = [bin for bin in bins if target_bin.contains(bin)]

        # merge what is left over to see if it matches target_bin
        try:
            merged_bin = cls.merge_bins(bins)
        except cls.NotMergeable as e:
            return False

        return True if merged_bin == target_bin else False


# TODO: move this into emodpy-hiv/emod-api?? Will need to move the AgeBin class, too
# TODO: add file format verification checks (e.g. consecutive age bins, totals add up to 1.0, etc)
# TODO: document file format
def _age_distributions_from_df(df: pd.DataFrame) -> Dict[int, IndividualAttributes.AgeDistribution]:
    node_column = 'node_id'
    age_bin_column = 'age_bin'
    fraction_column = 'population_fraction'

    # process the dataframe by node_id so that we can set per-node and/or Default (global) age fraction data
    age_distributions = {}
    groups = df.groupby(node_column)
    for node_id, node_table in groups:
        node_id = None if node_id == 0 else node_id  # mapping 0 (all nodes) to None
        age_bins = [AgeBin.from_string(s) for s in node_table[age_bin_column]]
        pop_fractions = node_table[fraction_column]

        # generating the format used by EMOD
        output_ages = [age_bin.start for age_bin in age_bins]
        output_ages.append(age_bins[-1].end)

        # generate the per-(end_age) cumulative fraction of the population
        cumulative_fractions = [0]
        cumulative_fraction = 0
        for pop_fraction in pop_fractions:
            cumulative_fraction += pop_fraction
            cumulative_fractions.append(cumulative_fraction)
        # just in case of odd floating point issues
        cumulative_fractions[-1] = 1

        ages_and_fractions = {
            'ResultValues': output_ages,
            'DistributionValues': cumulative_fractions,
            'NumDistributionAxes': 0,
            'ResultUnits': 'years',
            'ResultScaleFactor': 365
        }
        age_distribution = IndividualAttributes.AgeDistribution()
        age_distribution.from_dict(ages_and_fractions)
        age_distributions[node_id] = age_distribution
    return age_distributions
########################################################################################################################


# TODO: this is the "Standard Model" for country X
def load_country_model_demographics_default(country_model: str) -> HIVDemographics:
    country_model_dict = _registry.get(country_model, None)
    if country_model_dict is None:
        available = ", ".join(list(_registry.keys()))
        raise ValueError(f"Unknown country model named: {country_model} . Available models: {available}")
    country_data_root = _data_root.joinpath(country_model)
    population_file = Path(country_data_root, country_model_dict["initial_population_file"])
    df = pd.read_csv(population_file)
    demographics = HIVDemographics.from_population_dataframe(df=df)

    # apply the selected society template
    society = DemographicsTemplates.get_society_dict(society_name=country_model_dict["default_society_template"])
    demographics.society = society
        
    demographics.set_concurrency_params_by_type_and_risk("COMMERCIAL", "LOW",     0,  0, 1, 1, None )
    demographics.set_concurrency_params_by_type_and_risk("COMMERCIAL", "MEDIUM",  0,  0, 1, 1, None )
    demographics.set_concurrency_params_by_type_and_risk("COMMERCIAL", "HIGH",   59, 59, 1, 1, None )
    demographics.set_concurrency_params_by_type_and_risk("TRANSITORY", "LOW",     2,  2, 0.3556898557563289, 0.11640023094861798, None )
    demographics.set_concurrency_params_by_type_and_risk("TRANSITORY", "MEDIUM",  2.8758243237888,  2.8758243237888, 0.7875892836289242, 0.7430282943619352, None )
    demographics.set_concurrency_params_by_type_and_risk("TRANSITORY", "HIGH",    1,  1, 1, 1, None )

    demographics.set_concurrency_params_by_type_and_risk("INFORMAL", "LOW",     1.3185438939448315,  1.3185438939448315, 0.512265014420052, 0.28546727987372494, None )
    demographics.set_concurrency_params_by_type_and_risk("INFORMAL", "MEDIUM",  2.4343140081277106,  2.4343140081277106, 0.32876586481783143, 0.42145844365099366, None )
    demographics.set_concurrency_params_by_type_and_risk("INFORMAL", "HIGH",   1, 1, 1, 1, None )

    demographics.set_concurrency_params_by_type_and_risk("MARITAL", "LOW",    1, 1, 0, 0, None )
    demographics.set_concurrency_params_by_type_and_risk("MARITAL", "MEDIUM", 1.203640498339868, 1.203640498339868, 1, 1, None )
    demographics.set_concurrency_params_by_type_and_risk("MARITAL", "HIGH",   1, 1, 1, 1, None )

    assortivity_tim = [ [ 0.7032523334501651,  0.29674766654983487, 0 ], 
                        [ 0.29674766654983487, 0.7032523334501651,  0.7032523334501651  ], 
                        [ 0,                   0.7032523334501651,  0.29674766654983487 ]
                      ]
    assortivity_com = [ [ 1, 1, 1 ], 
                        [ 1, 1, 1 ],
                        [ 1, 1, 1 ]
                      ]

    demographics.set_pair_formation_parameters( "TRANSITORY", 0.0011197414231317777,  assortivity_matrix=assortivity_tim, node_ids=None )
    demographics.set_pair_formation_parameters( "INFORMAL",   0.0001561736059703799,  assortivity_matrix=assortivity_tim, node_ids=None )
    demographics.set_pair_formation_parameters( "MARITAL",    0.00018145743996196627, assortivity_matrix=assortivity_tim, node_ids=None )
    demographics.set_pair_formation_parameters( "COMMERCIAL", 0.15,                   assortivity_matrix=assortivity_com, node_ids=None )

    condom_usage_max_by_rel_type_by_node = [
        [ 0.7433197389199494,  0.5229475709021313,   0.3, 0.85 ],
        [ 0.46623684268980436, 0.26419727712640767,  0.3, 0.85 ],
        [ 0.46130107019244415, 0.042222393165696724, 0.3, 0.85 ],
        [ 0.7400316675706575,  0.5597670617942341,   0.3, 0.85 ],
        [ 0.3079437471527026,  0.5632160018635154,   0.3, 0.85 ],
        [ 0.4992941638997009,  0.2448900326712238,   0.3, 0.85 ],
        [ 0.4917707746908634,  0.3528077863526073,   0.3, 0.85 ],
        [ 0.538504255943748,   0.5079383809835986,   0.3, 0.85 ],
        [ 0.7479019895876177,  0.5714360413594817,   0.3, 0.85 ],
        [ 0.4713025697735299,  0.10411030389531929,  0.3, 0.85 ]
    ]

    tmp_node_id = 1
    for condom_usage_max_by_rel_type in condom_usage_max_by_rel_type_by_node:
        demographics.set_relationship_parameters( "TRANSITORY",
                                                coital_act_rate=0.33,
                                                condom_usage_min=0,
                                                condom_usage_mid=2003.4846871749717,
                                                condom_usage_max=condom_usage_max_by_rel_type[0],
                                                condom_usage_rate=2.6862110225260216,
                                                duration_scale=0.956774771214,
                                                duration_heterogeneity=0.833333333,
                                                node_ids=[tmp_node_id] )
        demographics.set_relationship_parameters( "INFORMAL",
                                                coital_act_rate=0.33,
                                                condom_usage_min=0,
                                                condom_usage_mid=1992.052744500361,
                                                condom_usage_max=condom_usage_max_by_rel_type[1],
                                                condom_usage_rate=0.2952473824125923,
                                                duration_scale=2.03104913138,
                                                duration_heterogeneity=0.75,
                                                node_ids=[tmp_node_id] )
        demographics.set_relationship_parameters( "MARITAL",
                                                coital_act_rate=0.33,
                                                condom_usage_min=0,
                                                condom_usage_mid=1995.8605054635884,
                                                condom_usage_max=condom_usage_max_by_rel_type[2],
                                                condom_usage_rate=1.6202355778150024,
                                                duration_scale=22.154455184937,
                                                duration_heterogeneity=0.666666667,
                                                node_ids=[tmp_node_id] )
        demographics.set_relationship_parameters( "COMMERCIAL",
                                                coital_act_rate=0.0027397260273972603,
                                                condom_usage_min=0.5,
                                                condom_usage_mid=1999.5,
                                                condom_usage_max=condom_usage_max_by_rel_type[3],
                                                condom_usage_rate=1,
                                                duration_scale=0.01917808219,
                                                duration_heterogeneity=1,
                                                node_ids=[tmp_node_id] )
        tmp_node_id += 1

    # initialize starting age distributions from file data
    age_distribution_file = Path(country_data_root, country_model_dict["age_distribution_file"])
    df = pd.read_csv(age_distribution_file)
    age_distributions = _age_distributions_from_df(df=df)
    for node_id, age_distribution in age_distributions.items():
        node_ids = node_id if node_id is None else [node_id]
        demographics.SetAgeDistribution(distribution=age_distribution, node_ids=node_ids)

    # load and apply fertility and mortality data
    fertility_file = Path(country_data_root, country_model_dict["fertility_file"])
    demographics.set_fertility(path_to_csv=fertility_file)
    male_mortality_file = Path(country_data_root, country_model_dict["male_mortality_file"])
    female_mortality_file = Path(country_data_root, country_model_dict["female_mortality_file"])
    demographics.set_mortality(file_male=male_mortality_file, file_female=female_mortality_file)

    # Load initial individual properties
    # TODO: ensure that in hiv_workflow that when we set IPs, (e.g. Accessibility) we don't overwrite this data by default (modify only)
    ips = [IndividualProperty.from_dict(ip_dict) for ip_dict in country_model_dict["individual_properties"]]
    demographics.default_node.individual_properties.individual_properties = ips
    return demographics
