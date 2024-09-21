"""
This module contains the classes and functions for creating demographics files
for HIV simulations. For more information on |EMOD_s| demographics files,
see :doc:`emod-hiv:software-demographics`. 
"""

import emod_api.demographics.Demographics as Demog
from emod_api.demographics import DemographicsTemplates as dt
from emodpy_hiv.demographics import DemographicsTemplates as hiv_dt

# the mortality algo has a few options. Might want to make them public module variables
# rather than fill up the function with them.


def _not_none(item):
    return False if item is None else True


class HIVDemographics(Demog.Demographics):
    """
    This class is derived from :py:class:`emod_api:emod_api.demographics.Demographics.Demographics` 
    and sets certain defaults for HIV in construction.

    Args:
        nodes: The number of nodes to create.
        idref: Method describing how the latitude and longitude values are created
            for each of the nodes in a simulation. "Gridded world" values use a grid 
            overlaid across the globe at some arcsec resolution. You may also generate 
            the grid using another tool or coordinate system. For more information,
            see :ref:`emod-hiv:demo-metadata`.
        base_file: A basic demographics file used as a starting point for
            creating more complicated demographics files. For example,
            using a single node file to create a multi-node file for spatial
            simulations. 
        init_prev: The initial HIV prevalence of the population.

    Returns: 
        None 
     """
    def __init__(self, nodes, idref="Gridded world grump2.5arcmin", base_file=None):
        super().__init__(nodes, idref, base_file)
        super().SetDefaultNodeAttributes(birth=True)
        hiv_dt.add_default_society(self)

    def fertility(self, path_to_csv, verbose=False):
        """
        Set fertility based on data. Simulation shall concist of individual pregnancies with rates by 
        woman's age and year-of-simulation using data from provided csv.
        """
        super().SetDefaultFromTemplate(dt.get_fert_dist(path_to_csv, verbose=verbose), dt._set_fertility_age_year)

    def mortality(
                self,
                file_male,
                file_female,
                interval_fit=None,
                which_point='mid',
                predict_horizon=2050,
                csv_out=False,
                n=0,  # I don't know what this means
                results_scale_factor=1.0/365.0):
        """
        For back-compat. This function can go away.
        """
        interval_fit = [1970, 1980] if interval_fit is None else interval_fit

        super().infer_natural_mortality(
                file_male,
                file_female,
                interval_fit=interval_fit,
                which_point=which_point,
                predict_horizon=predict_horizon,
                csv_out=csv_out,
                n=n,
                results_scale_factor=results_scale_factor)

    def apply_assortivity(self, rel_type, matrix=None):
        """
            Add an assortivity matrix to Pair-Forming Algo. Right now only applies to RISK IP.

            Args:
                rel_type: "COMMERCIAL", "INFORMAL", "MARITAL", or "TRANSITORY"
                matrix: 3x3 matrix of assortivity values, row represents male,
                    column represents female.

            Returns:
                N/A.
        """
        if matrix is not None:
            if len(matrix) != 3:
                raise ValueError("You need to have 3 rows in your assortivity matrix.")
            if any(len(row) != 3 for row in matrix):
                raise ValueError("You need to have 3 columns in each row of your assortivity matrix.")
            assortivity = {
                "Axes": ["LOW", "MEDIUM", "HIGH"],
                "Group": "INDIVIDUAL_PROPERTY",
                "Property_Name": "Risk",
                "Weighting_Matrix_RowMale_ColumnFemale": matrix
            }
            self.raw['Defaults']["Society"][rel_type]["Pair_Formation_Parameters"]["Assortivity"].update(assortivity)

    def set_concurrency_params_by_type_and_risk(self, rel_type, ip_value,
                                                max_simul_rels_male=None, max_simul_rels_female=None,
                                                prob_xtra_rel_male=None, prob_xtra_rel_female=None):
        """
        Set concurrent relationship formation params for a given relationship type and risk group. 

        Args:
            rel_type: Relationship category: "COMMERCIAL", "MARITAL", "INFORMAL" or "TRANS"
            ip_value: Usually Risk Group but based on defined IP. "High", "Medium", or "Low"
            max_simul_rels_male: Sets Max_Simultaneous_Relationships_Male.
            max_simul_rels_female: Sets Max_Simultaneous_Relationships_Female.
            prob_xtra_rel_male: Sets Prob_Extra_Relationship_Male.
            prob_xtra_rel_female: Sets Prob_Extra_Relationship_Female.

        Returns:
            Nothing.

        """
        if any([_not_none(p)
                for p in [max_simul_rels_male, max_simul_rels_female, prob_xtra_rel_male, prob_xtra_rel_female]]):
            if rel_type not in self.raw['Defaults']["Society"]:
                raise ValueError(f"Specified relationship_type of {rel_type} is not an existing relationship type: "
                                 f"{list(self.raw['Defaults']['Society'].keys())}.")
            if ip_value not in self.raw['Defaults']["Society"][rel_type]["Concurrency_Parameters"]:
                print(f"{list( self.raw['Defaults']['Society'][rel_type]['Concurrency_Parameters'].keys() )}")
                raise ValueError(f"Risk doesn't seem to be configured in the base Society template you have chosen.")

            # Now update only the parameters that are specified, None meaning "keep the current value"
            ip_dict = {}
            if max_simul_rels_male is not None:
                ip_dict["Max_Simultaneous_Relationships_Male"] = max_simul_rels_male
            if max_simul_rels_female is not None:
                ip_dict["Max_Simultaneous_Relationships_Female"] = max_simul_rels_female
            if prob_xtra_rel_male is not None:
                ip_dict["Prob_Extra_Relationship_Male"] = prob_xtra_rel_male
            if prob_xtra_rel_female is not None:
                ip_dict["Prob_Extra_Relationship_Female"] = prob_xtra_rel_female
            self.raw['Defaults']["Society"][rel_type]["Concurrency_Parameters"][ip_value].update(ip_dict)

    def set_pair_form_params(self, rel_type, new_constant_rate=None):
        """
        Set Formation_Rate_Constant value for the specified relationship type.

        Args:
            rel_type: Relationship Type. E.g., "MARITAL"
            new_constant_rate: New value for Formation_Rate_Constant for the relationship type.

        """
        if new_constant_rate is not None:
            if rel_type not in self.raw['Defaults']["Society"]:
                raise ValueError(f"Specified relationship_type of {rel_type} is not an existing relationship type: "
                                 f"{list(self.raw['Defaults']['Society'].keys())}.")
            pfp = {
                "Formation_Rate_Constant": new_constant_rate,
                "Formation_Rate_Type": "CONSTANT"
            }
            self.raw['Defaults']["Society"][rel_type]["Pair_Formation_Parameters"].update(pfp)

    def set_coital_act_rate(self, rel_type, rate=None):
        """
        Set Coital_Act_Rate value for the specified relationship type.

        Args:
            rel_type: Relationship Type. E.g., "MARITAL"
            rate: New value for Coital_Act_Rate for the relationship type.

        """
        if rate is not None:
            if rel_type not in self.raw['Defaults']["Society"]:
                raise ValueError(f"Specified relationship_type of {rel_type} is not an existing relationship type: "
                                 f"{list(self.raw['Defaults']['Society'].keys())}.")
            self.raw['Defaults']["Society"][rel_type]["Relationship_Parameters"]["Coital_Act_Rate"] = rate

    def set_condom_usage_probs(self, rel_type, min=None, mid=None, max=None, rate=None):
        """
        Set Condom_Usage_Probability values for the specified relationship type using 4 values to configure a sigmoid.

        Args:
            rel_type: Relationship Type. E.g., "MARITAL"
            min: "Min" (a probability)
            mid: "Mid" (a year)
            max: "Max" (a probability)
            rate: "Rate" (a probability)

        """
        if any([_not_none(p)
                for p in [min, mid, max, rate]]):
            if rel_type not in self.raw['Defaults']["Society"]:
                raise ValueError(f"Specified relationship_type of {rel_type} is not an existing relationship type: "
                                 f"{list(self.raw['Defaults']['Society'].keys())}.")
            prob = {}
            if min is not None:
                prob["Min"] = min
            if mid is not None:
                prob["Mid"] = mid
            if max is not None:
                prob["Max"] = max
            if rate is not None:
                prob["Rate"] = rate
            self.raw['Defaults']["Society"][rel_type]["Relationship_Parameters"]["Condom_Usage_Probability"].update(prob)

    def set_relationship_duration(self, rel_type, weibull_scale=None, weibull_heterogeneity=None):
        """
        Set the Weibull configuration values for the draw that determines the duration of relationships of the specified type.

        Args:
            rel_type: Relationship Type. E.g., "MARITAL"
            weibull_scale: value of Duration_Weibull_Scale
            weibull_heterogeneity: value of Duration_Weibull_Heterogeneity

        """
        if any([_not_none(p)
                for p in [weibull_scale, weibull_heterogeneity]]):
            if rel_type not in self.raw['Defaults']["Society"]:
                raise ValueError(f"Specified relationship_type of {rel_type} is not an existing relationship type: "
                                 f"{list(self.raw['Defaults']['Society'].keys())}.")

            if weibull_heterogeneity is not None:
                self.raw['Defaults']["Society"][rel_type]["Relationship_Parameters"]["Duration_Weibull_Heterogeneity"] = weibull_heterogeneity
            if weibull_scale is not None:
                self.raw['Defaults']["Society"][rel_type]["Relationship_Parameters"]["Duration_Weibull_Scale"] = weibull_scale

    def add_or_update_initial_risk_distribution(self, distribution=None):
        property = 'Risk'
        if distribution is not None:
            property_exists = property in [item['Property'] for item in self.raw['Defaults']['IndividualProperties']]
            if property_exists:
                # remove it so we can add it again
                ip_list = [item for item in self.raw['Defaults']['IndividualProperties']
                           if item['Property'] is not property]
                self.raw['Defaults']['IndividualProperties'] = ip_list

            # (Re-)add the requested property
            self.AddIndividualPropertyAndHINT(Property=property,
                                              Values=["LOW", "MEDIUM", "HIGH"],
                                              InitialDistribution=distribution)


def from_template_node(lat=0, lon=0, pop=1e6, name=1, forced_id=1):
    """
    Create a single-node :py:class:`~emodpy_hiv.demographics.HIVDemographics`
    instance from the parameters you supply.

    Args:
        lat: Latitude of the centroid of the node to create.
        lon: Longitude of the centroid of the node to create.
        pop: Human population of the node. 
        name: The name of the node. This may be a characteristic of the 
            node, such as "rural" or "urban", or an identifying integer.
        forced_id: The node ID for the single node.

    Returns:
        A :py:class:`~emodpy_malaria.demographics.HIVDemographics` instance.
    """
    new_nodes = [Demog.Node(lat=lat, lon=lon, pop=pop, name=name, forced_id=forced_id)]
    return HIVDemographics(nodes=new_nodes)


def from_pop_csv(pop_filename_in, pop_filename_out="spatial_gridded_pop_dir", site="No_Site"):
    """
    Create a multi-node :py:class:`~emodpy_hiv.demographics.HIVDemographics`
    instance from a CSV file describing a population.

    Args:
        pop_filename_in: The path to the demographics file to ingest.
        pop_filename_out: The path to the file to output.
        site: A string to identify the country, village, or trial site.

    Returns:
        A :py:class:`~emodpy_hiv.demographics.HIVDemographics` instance.
    """
    generic_demog = Demog.from_pop_csv(pop_filename_in=pop_filename_in, pop_filename_out=pop_filename_out, site=site)
    nodes = generic_demog.nodes
    return HIVDemographics(nodes=nodes, idref=site)


def from_params(tot_pop=1e6, num_nodes=100, frac_rural=0.3, id_ref="from_params"):
    """
    Create a multi-node :py:class:`~emodpy_hiv.demographics.HIVDemographics`
    instance as a synthetic population based on a few parameters.

    Args:
        tot_pop: The total human population in the node.
        num_nodes: The number of nodes to create.
        frac_rural: The fraction of the population that is rural.
        id_ref: Method describing how the latitude and longitude values are created
            for each of the nodes in a simulation. "Gridded world" values use a grid 
            overlaid across the globe at some arcsec resolution. You may also generate 
            the grid using another tool or coordinate system. For more information,
            see :ref:`emod-hiv:demo-metadata`.

    Returns:
        A :py:class:`~emodpy_hiv.demographics.HIVDemographics` instance.
    """
    generic_demog = Demog.from_params(tot_pop, num_nodes, frac_rural, id_ref)
    nodes = generic_demog.nodes
    return HIVDemographics(nodes=nodes, idref=id_ref)
