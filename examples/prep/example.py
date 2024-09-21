#!/usr/bin/env python

import pathlib # for a join
from functools import partial  # for setting Run_Number. In Jonathan Future World, Run_Number is set by dtk_pre_proc based on generic param_sweep_value...

# idmtools ...
from idmtools.assets import Asset, AssetCollection  #
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools_platform_comps.utils.python_requirements_ac.requirements_to_asset_collection import RequirementsToAssetCollection
from idmtools_models.templated_script_task import get_script_wrapper_unix_task

# emodpy
from emodpy_hiv.emod_task import EMODHIVTask
from emodpy.utils import EradicationBambooBuilds
from emodpy.bamboo import get_model_files
from emodpy_hiv.interventions.cascade_helpers import *
from emod_api.interventions.common import *

import params
import manifest

# ****************************************************************
#  Read experiment info from a config (py) file
#  Add Eradication as an asset (Experiment level)
#  Add Custom file as an asset (Simulation level)
#  Add the local asset directory to the task
#  Use builder to sweep simulations
#  How to run dtk_pre_process.py as pre-process
#  Save experiment info to file
# ****************************************************************

def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}

def print_params():
    """
    Just a useful convenience function for the user.
    """
    # Display exp_name and nSims
    # TBD: Just loop through them
    print("exp_name: ", params.exp_name)
    print("nSims: ", params.nSims)

def set_param_fn( config ):
    config.parameters.Simulation_Type = "HIV_SIM" # this should be set in the package.
    config.parameters.Simulation_Duration = 10*365.0 # maybe this should be a team-wide default?
    #config.parameters.Base_Infectivity = 3.5 
    config.parameters.Enable_Demographics_Reporting = 0  # just because I don't like our default for this

    config.parameters.Report_Event_Recorder_Events = ["NewInfectionEvent","PrEPDistributed"]

    # config hacks until schema fixes arrive
    config.parameters.Incubation_Period_Exponential = 30 # this should NOT be necessary
    config.parameters.pop( "Serialized_Population_Filenames" )
    config.parameters.pop( "Serialization_Time_Steps" )
    config.parameters.Report_HIV_Event_Channels_List = []
    config.parameters.Male_To_Female_Relative_Infectivity_Ages = [] # 15,25,35 ]
    config.parameters.Male_To_Female_Relative_Infectivity_Multipliers = [] # 5, 1, 0.5 ]
    # This one is crazy! :(
    config.parameters.Maternal_Infection_Transmission_Probability = 0
    config.parameters['logLevel_default'] = "WARNING" # 'LogLevel_Default' is not in scheme, so need to use the old style dict keys
    

    return config


def build_camp( coverage=1.0 ):
    """
    Build a campaign input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    """
    import emod_api.campaign as camp
    import emodpy_hiv.interventions.outbreak as ob 

    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    camp.set_schema( manifest.schema_file )
   
    """
    365 :: AllPlaces :: 1.0% :: OutbreakIndividual
    1 :: AllPlaces :: 90.0%/Female :: NewInfectionEvent->DelayedIntervention(CONSTANT_DISTRIBUTION/6)=>PREP()+BroadcastEvent(PrEPDistributed)
    """
    event = ob.new_intervention( timestep=365, camp=camp, coverage=0.01 )
    camp.add( event )

    import emodpy_hiv.interventions.prep as prep 

    new_iv_signal = BroadcastEvent( camp, 'PrEPDistributed' )
    efficacy_times = [ 0, 3650 ]
    efficacy_values = [ 1, 1 ]
    new_iv = prep.new_intervention( camp, efficacy_times, efficacy_values )
    event = triggered_event_common( camp, 'NewInfectionEvent', [new_iv, new_iv_signal], coverage = coverage, target_sex='Female', delay=6 )

    return camp

def update_campaign(simulation, value):
    """
        This callback function updates the coverage of the campaign.
    Args:
        simulation:
        value: value to which the coverage will be set

    Returns:
        tag that will be added to the simulation run
    """
    build_campaign_partial = partial(build_camp, coverage=value)
    simulation.task.create_campaign_from_callback(build_campaign_partial)
    return {"coverage": value}

def build_demog():
    """
    Build demographics.
    """
    from emodpy_hiv.demographics.hiv_demographics import HIVDemographics # OK to call into emod-api

    demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=10000, name='1', forced_id=1,
                                               default_society_template="PFA-Southern-Africa")
    return demog

def run_test():
    """
    This function is designed to be a parameterized version of the sequence of things we do 
    every time we run an emod experiment. 
    """
    # Create a platform
    # Show how to dynamically set priority and node_group
    platform = Platform("Calculon", node_group="idm_48cores", priority="Highest") 

    task = EMODHIVTask.from_default(config_path="config.json",
                                    eradication_path=manifest.eradication_path,
                                    campaign_builder=build_camp,
                                    demog_builder=build_demog,
                                    schema_path=manifest.schema_file,
                                    param_custom_cb=set_param_fn,
                                    ep4_path=None)
    task.set_sif(str(manifest.sif_path))  # set_sif() expects a string

    # Create simulation sweep with builder
    builder = SimulationBuilder()
    builder.add_sweep_definition( update_campaign, [ x*0.1 for x in range(params.nSims) ] )

    # create experiment from builder
    experiment  = Experiment.from_builder(builder, task, name=params.exp_name) 

    # The last step is to call run() on the ExperimentManager to run the simulations.
    experiment.run(wait_until_done=True, platform=platform)

    # Check result
    if not experiment.succeeded:
        print(f"Experiment {experiment.uid} failed.\n")
        exit()

    print(f"Experiment {experiment.uid} succeeded.")

    # Save experiment id to file
    with open("COMPS_ID", "w") as fd:
        fd.write(experiment.uid.hex)
    print()
    print(experiment.uid.hex)
    assert experiment.succeeded
    
def run():
    import emod_hiv.bootstrap as dtk
    dtk.setup(pathlib.Path(manifest.eradication_path).parent)
    run_test()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # parser.add_argument('-v', '--use_vpn', action='store_true',
    #                     help='get model files from Bamboo(needs VPN)')
    parser.add_argument('-v', '--use_vpn', type=str, default='No', choices=['No', "Yes"],
                        help='get model files from Bamboo(needs VPN) or Pip installation(No VPN)')
    args = parser.parse_args()
    if args.use_vpn.lower() == "yes":
        from enum import Enum, Flag, auto
        class MyEradicationBambooBuilds(Enum): # EradicationBambooBuilds
            HIV_LINUX = "DTKHIVONGOING-SCONSRELLNXSFT"

        plan = MyEradicationBambooBuilds.HIV_LINUX
        get_model_files( plan, manifest, False )
        run_test()
    else:
        run()
