import emod_api.interventions.outbreak as ob
from emod_api import schema_to_class as s2c

def new_intervention(timestep, camp, coverage=0.01):
    """
    Seed HIV infection at a certain timestep, with a certain prevalence.

    Parameters:
        timestep (float): When? Timestep at which outbreak should occur.
        camp: emod_api.campaign object that has schema_path.
        coverage: How Much? The intended level of initial prevalance.

    Returns: 
        event: event as dict
    """
    event = ob.seed_by_coverage( camp, timestep, coverage )
    # add h-o specific Target_Config
    from . import utils as hiv_utils
    hiv_utils.declutter( event )
    return event
    
def seed_infections( camp, start_day=365, coverage=0.075, target_properties=None, target_min_age=0, target_max_age=125, target_gender="All"):
    """
    Create outbreak event with more targeting than 'new_intervention'.
    """
    import emod_api.campaign as camp
    import emod_api.interventions.common as common
    from emodpy_hiv.interventions import utils as hiv_utils

    outbreak = s2c.get_class_with_defaults( "OutbreakIndividual", camp.schema_path )
    outbreak['Intervention_Name'] = "Seeding"
    event = common.ScheduledCampaignEvent( camp, start_day, Demographic_Coverage=coverage, Intervention_List=[ outbreak ], Target_Age_Min=target_min_age*365, Target_Age_Max=target_max_age*365, Target_Gender=target_gender, Property_Restrictions=target_properties )
    hiv_utils.declutter( event )
    return event

