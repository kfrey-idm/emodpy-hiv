from functools import partial
import unittest
import sys
from pathlib import Path
import json
import pandas as pd
import pprint as pretty
import datetime as datetime
from idmtools.core import ItemType
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

# emodpy
import emodpy_hiv.emod_task as emod_task
from emodpy.utils import EradicationBambooBuilds
import emod_api.campaign as camp
import emod_api.interventions.common as common
import emod_api.schema_to_class

from emodpy_hiv.demographics.hiv_demographics import HIVDemographics
import emodpy_hiv.interventions.outbreak as ob
import emodpy_hiv.interventions.stipostdebut as stipostdebut
import emodpy_hiv.interventions.setsexualdebut as setsexualdebut

parent = Path(__file__).resolve().parent
sys.path.append(parent)
# import conf as conf
import manifest

import os
dir_path = os.path.dirname(os.path.realpath(__file__))
import emod_hiv.bootstrap as dtk


class TC:
        # Test Case parameters - generic
        Start_Year = 1950.5
        End_Year = 2050.0
        Target_Age_Max = None   # This is user specified, it should not be provided??
        Target_Age_Min = None   # This is user specified, it should not be provided??
        Update_Period = 30.416667
        Distributed_Event_Trigger = "Setting_Age_Sexual_Debut"

class Files():
    config = "config.json"
    campaign = "campaign.json"
    ReportEventRecorder = "output/ReportEventRecorder.csv"
    ReportHIVByAgeAndGender = "output/ReportHIVByAgeAndGender.csv"
files = Files()

filenames = [files.config,
                files.campaign,
                files.ReportEventRecorder,
                files.ReportHIVByAgeAndGender]

class TestDebutInterventions(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # this test will use the latest eradication build saved in the repo under latest folder
        print("Test class started")
        starting_dir = os.getcwd()
        dtk.setup(manifest.emod_hiv_path)
        os.chdir(starting_dir)  # because of dumb bug in emod-hiv chdirs in setup

    def setUp(self):

        self.example_path = os.path.dirname(os.path.realpath(__file__))
        self.eradication = manifest.emod_hiv_eradication
        self.schema_path = manifest.emod_hiv_schema
        self.sif_file = manifest.sif_path
        self.config_path = os.path.join(self.example_path, "config.json")
        self.platform = Platform("SLURMStage") #"Calculon", node_group="idm_48cores", priority="Highest"

    def update_sim_random_seed(self, simulation, value):
        simulation.task.config.parameters.Run_Number = value
        return {"Run_Number": value}
    
    def update_demographic_filename(self, simulation, value):
        filename = f"demographics_{value}_PFARates.json"
        simulation.task.config.parameters.Demographics_Filenames = [ filename ]
        return {"PFA_RelForm_Case": value}
    
    def global_build_demog_from_template_node(self):
        demog = HIVDemographics.from_template_node(lat=0, lon=0, pop=1000, name=1, forced_id=1,
                                                   default_society_template="PFA-Southern-Africa")
        return demog

    # def global_build_demog_from_params(self):
    #     totpop = 9876
    #     num_nodes = 199
    #     frac_rural = 0.3
    #     demog = HIVDemographics.from_params(tot_pop=totpop, num_nodes=num_nodes, frac_rural=frac_rural)
    #     # print(demog.to_dict())
    #     return demog

    @staticmethod
    def global_set_param_fn(config, duration=24000, timestep=30):  
        config.parameters.Simulation_Type = "HIV_SIM" # this should be set in the package.
        config.parameters.Simulation_Duration = duration # maybe this should be a team-wide default?
        config.parameters.Simulation_Timestep = timestep
        config.parameters.Enable_Demographics_Reporting = 1  # just because I don't like our default for this
        # config hacks until schema fixes arrive
        config.parameters.pop( "Serialized_Population_Filenames" )
        config.parameters.pop( "Serialization_Time_Steps" )
        config.parameters.Report_HIV_Event_Channels_List = []
        config.parameters.Male_To_Female_Relative_Infectivity_Ages = [ 15,25,35 ]
        config.parameters.Male_To_Female_Relative_Infectivity_Multipliers = [ 5, 1, 0.5 ]
        config.parameters.Maternal_Infection_Transmission_Probability = 0
        config.parameters['logLevel_default'] = "WARNING" # 'LogLevel_Default' is not in scheme, so need to use the old style dict keys
        config.parameters.Incubation_Period_Distribution = "CONSTANT_DISTRIBUTION"
        config.parameters.Custom_Individual_Events = [
            "Setting_Age_Sexual_Debut",
            "Birth_SetSexualDebutAge_Event",
            "Male_tracking_SetSexualDebutAge_Event",
            "Female_tracking_SetSexualDebutAge_Event",
            "All_SetSexualDebutAge_Event",
            "Male_SetSexualDebutAge_Event",
            "Female_SetSexualDebutAge_Event",
            "All_tracking_SetSexualDebutAge_Event",
            "Birth_Male_SetSexualDebutAge_Event",
            "Birth_Female_SetSexualDebutAge_Event",
            "STIDebutMale_SetSexualDebutAge_Event",
            "STIDebutFemale_SetSexualDebutAge_Event"
        ]

        config.parameters.Report_HIV_ByAgeAndGender = 1
        config.parameters.Report_Event_Recorder = 1
        config.parameters.Report_Event_Recorder_Events = [
                "Setting_Age_Sexual_Debut",
                "Birth_SetSexualDebutAge_Event",
                "STIDebut",
                "STIDebutMale_SetSexualDebutAge_Event",
                "STIDebutFemale_SetSexualDebutAge_Event",
                "Male_tracking_SetSexualDebutAge_Event",
                "Female_tracking_SetSexualDebutAge_Event",
                "All_SetSexualDebutAge_Event",
                "Male_SetSexualDebutAge_Event",
                "Female_SetSexualDebutAge_Event",
                "All_tracking_SetSexualDebutAge_Event",
                "Birth_Male_SetSexualDebutAge_Event",
                "Birth_Female_SetSexualDebutAge_Event",
            ]
        config.parameters.Report_HIV_Event_Channels_List = []
        config.parameters.Report_HIV_Period = 30.416667

        config.parameters.Report_HIV_ByAgeAndGender = 1
        config.parameters.Report_HIV_ByAgeAndGender_Start_Year= 1960
        config.parameters.Report_HIV_ByAgeAndGender_Stop_Year= 2100
        config.parameters.Report_HIV_ByAgeAndGender_Collect_Gender_Data= 1
        config.parameters.Report_HIV_ByAgeAndGender_Collect_Age_Bins_Data= [ 0, 12, 13, 15, 16, 17, 18, 19, 20, 25, 30 ]
        config.parameters.Report_HIV_ByAgeAndGender_Add_Relationships             = 1
        config.parameters.Report_HIV_ByAgeAndGender_Add_Concordant_Relationships = 0
        config.parameters.Base_Year=1950
        
        # Intervention specific parameters
        # config.parameters.Custom_Individual_Events.append("Setting_Age_Sexual_Debut")
        # config.parameters.Report_Event_Recorder_Events.append("Setting_Age_Sexual_Debut")
        config.parameters.Simulation_Duration=24000
        config.parameters.Simulation_Timestep=30
        # config.parameters.Demographics_Filenames = [ "demographics_Normal_PFARates.json" ]

        return config
    
    #--------------------------------------------
    # Tests sex debut with a WEIBULL distribution
    #--------------------------------------------
    def test_sexualdebut_WEIBULL(self):
        camp.schema_path = str(self.schema_path)
        start_day = 2
        test_name = self.id().split('.')[-1]

        def build_camp():
            # No events, just a default campaign
            return camp

        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)

            return config
        
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=F"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = [files.ReportEventRecorder, files.ReportHIVByAgeAndGender, files.config, files.campaign]
        sims = self.platform.get_children_by_object(experiment)
        
        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # To create a unique folder name (for plotting)
        output_path = parent / "inputs" / testtime
        
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames, output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_reports_basics(local_path, [files.ReportEventRecorder, files.ReportHIVByAgeAndGender])
            self.validate_ReportEventRecorder(local_path)
            self.validate_simulation_config_file(local_path, "WEIBULL")

    #------------------------------------------------------------
    # SETSEXUALDEBUT test with StandardEventCoordinator  --- 
    #------------------------------------------------------------
    
    def test_setsexualdebut_New_intervention_event_w_DEFAULTS(self):
        import emodpy_hiv.interventions.setsexualdebut as setsexualdebut
        camp.schema_path = str(self.schema_path)
        start_day = 2
        test_name = self.id().split('.')[-1]

        def build_camp():
            """ DEFAULT VALUES...
            Testing:  Base case campaign with 1 intervention and 1 event
            Values:     Default values
            Method Signature: 
                    new_intervention_event( camp, 
                                            start_day=1, 
                                            coverage=1.0,
                                            target_gender="All",
                                            target_demographic="Everyone",
                                            node_ids=None):
            """
           
            outbreak_event = ob.new_intervention(start_day - 2, camp=camp, coverage=0.4) 
            camp.add(event = outbreak_event, first=True)

            debut_event = setsexualdebut.new_intervention_event(camp=camp)
            camp.add(debut_event, first=False)
            return camp

        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)
            config.parameters.Sexual_Debut_Age_Setting_Type = "FROM_INTERVENTION"
            return config
        
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )

        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=f"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = [files.ReportEventRecorder,
                     files.ReportHIVByAgeAndGender,
                     files.config,
                     files.campaign]

        sims = self.platform.get_children_by_object(experiment)

        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # Adding a more intuitive folder name.
        output_path = parent / "inputs" / testtime

        for simulation in sims:
            # download simulation's output files from COMPS 
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_reports_basics(local_path, [files.ReportEventRecorder, files.ReportHIVByAgeAndGender])
            self.validate_ReportEventRecorder(local_path)
            self.validate_simulation_config_file(local_path, "FROM_INTERVENTION")
            
    #------------------------------------------------------------
    
    def test_setsexualdebut_FROM_FILE(self):
        from emodpy.emod_campaign import EMODCampaign
        camp.schema_path = str(self.schema_path)
        start_day = 2
        test_name = self.id().split('.')[-1]

        def build_camp():
            # No events, just a default campaign
            file = setsexualdebut.new_intervention_as_file(camp=camp, start_day=start_day, filename=os.path.join(parent,"SexualDebut.json"))
            return camp
        

        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)
            config.parameters.Sexual_Debut_Age_Setting_Type= "FROM_INTERVENTION"
            return config
        
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        # get the path of this script
        
        task.campaign.clear()   # First it Clears the campaign from the task
        task.campaign = EMODCampaign.load_from_file(os.path.join(parent, "SexualDebut.json"))

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))


        experiment = Experiment.from_builder(builder, task, name=f"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = [files.ReportEventRecorder,
                     files.ReportHIVByAgeAndGender,
                     files.config,
                     files.campaign]

        sims = self.platform.get_children_by_object(experiment)
        
        # output_path = parent / "inputs"
        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # To create a unique folder name (for plotting)
        output_path = parent / "inputs" / testtime

        for simulation in sims:
            # download simulation's output files from COMPS 
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_reports_basics(local_path, [files.ReportEventRecorder, files.ReportHIVByAgeAndGender])
            self.validate_ReportEventRecorder(local_path)
            self.validate_simulation_config_file(local_path, "FROM_INTERVENTION")
    

    def test_setsexualdebut_New_intervention_event_USER_SPECIFIED(self):
        camp.schema_path = str(self.schema_path)
        start_day = 2
        # assign the current test method name to a variable
        test_name = self.id().split('.')[-1]

        def build_camp():
            event_start_day = 60
            coverage = 0.9
            maledebut_event = setsexualdebut.new_intervention_event(camp=camp, 
                                                          Event_Start_Day=event_start_day, 
                                                          Coverage=coverage, 
                                                          Target_Gender="Male",
                                                          Target_Demographic="ExplicitGender",
                                                          Setting_Type="USER_SPECIFIED",
                                                          Age_Years=18,
                                                          node_ids=None)
            camp.add(event = maledebut_event, first=True)

            event_start_day = 120
            coverage = 0.9
            femaledebut_event = setsexualdebut.new_intervention_event(camp=camp, 
                                                          Event_Start_Day=event_start_day, 
                                                          Coverage=coverage, 
                                                          Target_Gender="Female",
                                                          Target_Demographic="ExplicitGender",
                                                          Setting_Type="USER_SPECIFIED",
                                                          Age_Years=15,
                                                          node_ids=None)
            camp.add(event = femaledebut_event, first=False)

            return camp

        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)
            config.parameters.Sexual_Debut_Age_Setting_Type= "FROM_INTERVENTION"
            return config
        
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=f"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = [files.ReportEventRecorder,
                     files.ReportHIVByAgeAndGender,
                     files.config,
                     files.campaign]

        sims = self.platform.get_children_by_object(experiment)
        
        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # To create a unique folder name (for plotting)
        output_path = parent / "inputs" / testtime
        for simulation in sims:
            # download simulation's output files from COMPS 
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_reports_basics(local_path, [files.ReportEventRecorder, files.ReportHIVByAgeAndGender])
            self.validate_ReportEventRecorder(local_path)
            self.validate_simulation_config_file(local_path, "FROM_INTERVENTION")
            self.validate_HIVByAgegender_UserSpecified(local_path,  target_gender = ['Male', 'Female'])
         
   
    def SKIP_BUG174_test_track_sexual_debut_intervention_DEFAULTS(self):
        # 2)- ValueError( f"You set param {nuke_key} but it was disabled and is not being used." )
        #     ValueError: You set param Target_Age_Max but it was disabled and is not being used.
        
        camp.schema_path = str(self.schema_path)
        start_day = 2
        test_name = self.id().split('.')[-1]

        def build_camp():
            
            # region -- DEFAULTS--

            """
            -- DEFAULTS--
            Start_Year = "1960.5",          # Logged datatype bug and using workaround
            End_Year = "2050",              # Logged datatype bug and using workaround
            node_ids = None,
            Target_Age_Max = 125,           # Logged bug and using workaround
            Target_Age_Min = 0,
            Target_Demographic = "Everyone",
            Target_Gender = "All",
            Update_Period = 30.416667,
            Distributed_Event_Trigger = "Setting_Age_Sexual_Debut",
            Setting_Type = "CURRENT_AGE",
            Age_Years = None
            """
            # endregion
            
            Time_Value_Map = {"1960": 0.1, "1970": 0.2, "1980": 0.3}

            sexdeb_iv_event = setsexualdebut.track_sexual_debut_intervention(camp, 
                                                                            # Target_Age_Max=None,  # <- This is currently the way to workaround the bug
                                                                            YearSexualDebutRatios = Time_Value_Map
                                                                          )

            camp.add(event=sexdeb_iv_event, first=True)
            return camp

        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)

            return config
        
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=f"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv",
                     "output/ReportHIVByAgeAndGender.csv",
                     "campaign.json",
                     "config.json"]

        sims = self.platform.get_children_by_object(experiment)
        
        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # To create a unique folder name (for plotting)
        output_path = parent / "inputs" / testtime
        for simulation in sims:
            # download simulation's output files from COMPS 
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_tracker_events_report_output_file(local_path)
            self.validate_HIVByAgegender_UserSpecified(local_path,  target_gender = ['Male', 'Female'])
            self.validate_simulation_config_file(local_path, "FROM_INTERVENTION")
    
    def test_track_sexual_debut_intervention_CURRENTAGE(self):
        # TODO: Bugs logged: 1) - Wrong Start and End Year data type, 2)- Target_Age_Max not used. 
        camp.schema_path = str(self.schema_path)
        start_day = 2
        test_name = self.id().split('.')[-1]
        args = [[1, {"1960": 0.1, "1970": 0.1, "1980": 0.1}],
                [2, {"1960": 0.3, "1970": 0.3, "1980": 0.3}],
                [3, {"1960": 0.8, "1970": 0.5, "1980": 0.2}]]

        def build_camp(args = [0, {"1960": 0.1, "1970": 0.1, "1980": 0.1}]):
            """
            -- DEFAULTS--
            Start_Year = 1960.5,          
            End_Year = 2050,             
            node_ids = None,
            Target_Age_Max = 125,
            Target_Age_Min = 0,
            Target_Demographic = "Everyone",
            Target_Gender = "All",
            Update_Period = 30.416667,
            Distributed_Event_Trigger = "Setting_Age_Sexual_Debut",
            Setting_Type = "CURRENT_AGE",
            Age_Years = None
            """
            print("Starting Test Case:", args[0], args[1])

            sexdeb_iv_event = setsexualdebut.track_sexual_debut_intervention(camp, 
                                                                          YearSexualDebutRatios=args[1],
                                                                          Start_Year= TC.Start_Year,
                                                                          End_Year= TC.End_Year,
                                                                          Target_Age_Max=None,
                                                                          Setting_Type = "CURRENT_AGE"
                                                                          )

            camp.add(event=sexdeb_iv_event, first=True)
            return camp

        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)
            config.parameters.Sexual_Debut_Age_Setting_Type= "FROM_INTERVENTION"
            # config.parameters.Demographics_Filenames = [ "demographics_Normal_PFARates.json" ]
            return config

        def update_campaign(simulation, args):
            #   This callback function updates the coverage of the campaign. Function: "build_camp02"
            build_campaign_partial = partial(build_camp, args)
            simulation.task.create_campaign_from_callback(build_campaign_partial)
            tag_value = args[1]
            # Return a tag that will be added to the simulation run.
            return {"Test_Case": tag_value}
        
                
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string
        # get the path of this script
        CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
        INPUT_DEMOG_PATH = os.path.join(CURRENT_DIRECTORY, "inputs", "demographic_files")
        demog_files = [os.path.join(INPUT_DEMOG_PATH, "demographics_Normal_PFARates.json"),
                      os.path.join(INPUT_DEMOG_PATH, "demographics_Low_PFARates.json"),
                      os.path.join(INPUT_DEMOG_PATH, "demographics_High_PFARates.json")]

        task.demographics.clear()   # First it Clears the demographics from the task
        for demog in demog_files:
            task.simulation_demographics.add_demographics_from_file(demog)

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1)) # Runs
        builder.add_sweep_definition(self.update_demographic_filename, ["Normal", "Low", "High"])  # Demographics
        builder.add_sweep_definition(update_campaign, [a for a in args])    # Campaign - Year-SexualDebut-Ratios

        experiment = Experiment.from_builder(builder, task, name=f"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        sims = self.platform.get_children_by_object(experiment)
        
        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # To create a unique folder name (for plotting)
        output_path = parent / "inputs" / testtime
        for simulation in sims:
            # download simulation's output files from COMPS 
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_tracker_events_report_output_file(local_path)
            self.validate_HIVByAgegender_CurrentAge(local_path,  genders= [0, 1])
            self.validate_simulation_config_file(local_path, "FROM_INTERVENTION")
    
    def SKIP_BUG179_test_track_sexual_debut_intervention_USER_SPECIFIED(self):
        # https://github.com/InstituteforDiseaseModeling/emodpy-hiv/issues/179
        camp.schema_path = str(self.schema_path)
        start_day = 2
        test_name = self.id().split('.')[-1]
        female_target_age = 15
        male_target_age = 18
        def build_camp():
            
            sexdeb_iv_event_fem = setsexualdebut.track_sexual_debut_intervention(camp, 
                                                                YearSexualDebutRatios = {"1960": 0.4, "1970": 0.4, "1980": 0.4},
                                                                Target_Age_Max=None,            #TODO: CHANGE AFTER BUG FIX
                                                                Target_Age_Min=15,
                                                                Target_Demographic= "ExplicitGender",
                                                                Target_Gender= "Female",
                                                                Setting_Type= "USER_SPECIFIED",
                                                                Age_Years=female_target_age 
                                                                )
            camp.add(event=sexdeb_iv_event_fem, first=True)

            sexdeb_iv_event_male = setsexualdebut.track_sexual_debut_intervention(camp, 
                                                                YearSexualDebutRatios = {"1960": 0.5, "1970": 0.5, "1980": 0.5},
                                                                Target_Age_Max=None,    #TODO: CHANGE AFTER BUG FIX
                                                                Target_Age_Min=18,    
                                                                Target_Demographic= "ExplicitGender",
                                                                Target_Gender= "Male",
                                                                Setting_Type= "USER_SPECIFIED",
                                                                Age_Years=male_target_age
                                                                )
            camp.add(event=sexdeb_iv_event_male, first=False)
            return camp

        # def build_demog(self, case="Normal"):
        #     demog = HIVDemographics.from_file(f"demographics_{case}_PFARates.json")
        #
        #     # print(demog.to_dict())
        #     return demog


        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)
            config.parameters.Report_HIV_ByAgeAndGender_Collect_Age_Bins_Data= [ 13, 15, 16, 17, 18, 19, 20, 25, 30 ]
            return config
        
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=f"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        sims = self.platform.get_children_by_object(experiment)
        
        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # To create a unique folder name (for plotting)
        output_path = parent / "inputs" / testtime
        for simulation in sims:
            # download simulation's output files from COMPS 
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_tracker_events_report_output_file(local_path)
            self.validate_HIVByAgegender_UserSpecified(local_path, cases = [[0, male_target_age], [1, female_target_age]])
            self.validate_simulation_config_file(local_path, "FROM_INTERVENTION")
    
    def test_track_sexual_debut_intervention_CURRENTAGE_STAGGERED(self):
        # local_path = Path(r"E:\GIT\emodpy-hiv\tests\sim_tests\inputs\28_154125\1ce3f49a-478e-ee11-92fe-f0921c167864")
        camp.schema_path = str(self.schema_path)
        start_day = 2
        test_name = self.id().split('.')[-1]
        def build_camp():
            
            sexdeb_iv_event_fem = setsexualdebut.track_sexual_debut_intervention(camp, 
                                                                YearSexualDebutRatios =  {"2000": 0.7, "2001": 0.1, "2003": 0.1, "2004": 0.1, "2005": 0.1, "2007": 0.1, "2009": 0.1, "2010": 0.1, "2012": 0.1, "2014": 0.1, "2016": 0.1, "2017": 0.1},
                                                                Target_Age_Min=None,
                                                                Target_Age_Max=None,
                                                                Target_Demographic= "ExplicitGender",
                                                                Target_Gender= "Female",
                                                                Setting_Type= "CURRENT_AGE",
                                                                )
            camp.add(event=sexdeb_iv_event_fem, first=True)

            sexdeb_iv_event_male = setsexualdebut.track_sexual_debut_intervention(camp, 
                                                                YearSexualDebutRatios = { "2000": 0.1, "2001": 0.1, "2003": 0.1, "2004": 0.1, "2005": 0.1, "2007": 0.1, "2009": 0.9, "2010": 0.1, "2012": 0.1, "2014": 0.1, "2016": 0.1, "2017": 0.1},
                                                                Target_Age_Min=None,
                                                                Target_Age_Max=None,
                                                                Target_Demographic= "ExplicitGender",
                                                                Target_Gender= "Male",
                                                                Setting_Type= "CURRENT_AGE",
                                                                )
            camp.add(event=sexdeb_iv_event_male, first=False)
            return camp
    
        # def build_demog(self, case="Normal"):
        #     demog = HIVDemographics.from_file(f"demographics_{case}_PFARates.json")
        #
        #     # print(demog.to_dict())
        #     return demog


        def setParamfn(config, duration):
            # uses the global set_param_fn to set parameters
            config = self.global_set_param_fn(config)
            config.parameters.Sexual_Debut_Age_Setting_Type= "FROM_INTERVENTION"
            config.parameters.Report_HIV_ByAgeAndGender_Collect_Age_Bins_Data= [ 13, 15, 16, 17, 18, 19, 20, 25, 30 ]
            return config
        
        task = emod_task.EMODHIVTask.from_default(
            config_path="config.json", 
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_path=None,
            demog_builder=self.global_build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=f"HIV {test_name}")
        experiment.run(wait_until_done=True, platform=self.platform)
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")

        sims = self.platform.get_children_by_object(experiment)
        
        testtime = datetime.datetime.now().strftime("%d_%H%M%S")  # To create a unique folder name (for plotting)
        output_path = parent / "inputs" / testtime
        for simulation in sims:
            # download simulation's output files from COMPS 
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            local_path = output_path / str(simulation.uid)
            self.validate_tracker_events_report_output_file(local_path)
            self.validate_HIVByAgegender_CurrentAge(local_path,  genders= [0, 1])
            self.validate_simulation_config_file(local_path,  "FROM_INTERVENTION")
    
    # ------------------ Utility functions ------------------

    def RefTrack_PostProcessing_Validations(self):
        import utils.plots as plots
        day = "03_093712" 
        sim_id = "f8162f36-677a-ee11-92fd-f0921c167864"
        output_path = parent / "inputs" / day / sim_id / "output"
        # self.validate_tracker_HIVByAgegender_UserSpecified(local_path, cases = [[0, 18], [1, 15]])
        event_report = output_path  / "ReportEventRecorder.csv"
        plots.plot_event_report(event_report)
        perc_file = output_path / "ReportHIVByAgeAndGender_percent.csv"
        df = plots.read_ReportHIVByAgeAndGender(perc_file)
        plots.chart_age_gender_byage(df=df, age_array=[18])
        plots.chart_age_gender_sets(df=df, 
                                    sexdebut_series= ['Ratio Has Debuted', 'Ratio First Coital Act'], 
                                    age_gender_sets=[ [18, "Male"], [15, "Female"]])
        plots.chart_age_gender_splitted_subplots(df=df, age_array=[[13,17], [18,20]] )
        self.validate_HIVByAgegender_CurrentAge(output_path,  genders= [0, 1])
        return 
        
    def STDiv_PostProcessing_Validations(self):
        # Rename definition as test_PostProcessing to run 
        local_path = parent / "inputs" / "24_153231" / "3cb3fc2d-bd72-ee11-92fd-f0921c167864"
        self.validate_HIVByAgegender_UserSpecified(local_path, cases = [[0, 18], [1, 15]])
        self.validate_HIVByAgegender_UserSpecified(local_path,  target_gender = ['Male', 'Female'])  

    def validate_reports_basics(self, local_path, reports=[]):
        for filename in reports:
            if filename == files.config:
                continue
            file_path = local_path / filename
            self.assertTrue(file_path.is_file(), msg=f'Test failed: {filename} is not generated.')
            report_df = pd.read_csv(file_path)
            self.assertGreater(len(report_df), 0, msg=f'Test failed: {filename} report should not be empty.')

        return

    def validate_ReportEventRecorder(self, local_path):
        # validate Report Event Recorder file exist
        file_path = local_path / files.ReportEventRecorder
     
        # validate Report Evenet Recorder contents
        report_df = pd.read_csv(file_path)
        sti_debut_df = report_df[report_df['Event_Name'] == 'STIDebut'] 

        # validate if STIDebut event is recorded
        self.assertGreater(len(sti_debut_df), 0, msg=f'Test failed: there are should be some STIDebut events.')
        return 
    def validate_HIVByAgegender_CurrentAge(self, local_path,  genders = []):
        
        #validate if 'ReportHIVByAgeAndGender.csv' is generated
        file_path = local_path / files.ReportHIVByAgeAndGender
        report_df = pd.read_csv(file_path)

        for gender in genders:
            # create a subset of the report_df for the given case
            df = report_df[(report_df[' Gender'] == gender) ]
                        
            hasdeb_mean = df['Has Debuted'].mean()
            hadfirst_mean = df['Had First Coital Act'].mean()
            print(f"Gender: {gender}: Mean of Has Debuted: {hasdeb_mean}, Mean of Had First Coital Act: {hadfirst_mean}\n\n")

            # print(df['Has Debuted'].to_list(),  df['Had First Coital Act'].to_list())
            self.assertGreater(hasdeb_mean, 0, f'Test failed: "Has Debuted" should not be 0 \n\n Age: CurrentAge Gender: {gender} file: {file_path}')
            self.assertGreater(hadfirst_mean, 0, f'Test failed: "Had First Coital Act" should Not be 0 \n\n Age: CurrentAge Gender: {gender} file: {file_path}')
        return  

    def validate_HIVByAgegender_UserSpecified(self, local_path,  target_gender = ['Male', 'Female']):
        # TODO: IMPLEMENT THIS - THIS IS a copy of the 'current age' function

        #validate if 'ReportHIVByAgeAndGender.csv' is generated
        report_path = local_path / files.ReportHIVByAgeAndGender
        report_df = pd.read_csv(report_path)
        
        campaign_path = local_path / files.campaign 
        report_df['Gender'] = report_df[' Gender'].replace({0: 'Male', 1: 'Female'})

        # Validate information is present per gender.
        for case in target_gender:
            gender = case
          
            # create a subset of the report_df for the given case
            df = report_df[(report_df['Gender'] == gender) ]
                        
            hasdeb_mean = df['Has Debuted'].mean()
            hadfirst_mean = df['Had First Coital Act'].mean()
            print(f"Gender: {gender}: Mean of Has Debuted: {hasdeb_mean}, Mean of Had First Coital Act: {hadfirst_mean}\n\n")

            # print(df['Has Debuted'].to_list(),  df['Had First Coital Act'].to_list())
            self.assertGreater(hasdeb_mean, 0, f'Test failed: "Has Debuted" should not be 0 \n\n Age: CurrentAge Gender: {gender}')
            self.assertGreater(hadfirst_mean, 0, f'Test failed: "Had First Coital Act" should Not be 0 \n\n Age: CurrentAge Gender: {gender}')       

        # Validate directly against the campaign configuration
        campaign_obj = pd.read_json(campaign_path)
        events = campaign_obj['Events']  

        for event in events:
            target_age = event['Event_Coordinator_Config']['Intervention_Config']['Age_Years']
            gender = event['Event_Coordinator_Config']['Target_Gender']

            start_day = event['Start_Day']
            print(f"Target Age: {target_age}, Gender: {gender} start_day: {start_day}")
            
            # Create a subset of the report_df looking for Male/Females younger than Age_Years who have debuted
            df = report_df[(report_df[' Age'] < target_age) & (report_df[' Gender'] == gender) & (report_df['Has Debuted'] >0) ]
           
            # Assert if is not empty )there should not be any
            self.assertEqual(len(df), 0, f'Test failed: No {gender} younger than min age should have debuted \n\n Age: {target_age}')
        return  

    def validate_simulation_config_file(self, local_path, setting_type):
        # validate if config.json is generated
        file_path = local_path / files.config
        self.assertTrue(file_path.is_file(), msg=f'Test failed: config.json is not generated.')
        # validate result
        with open(file_path) as f:
            config = json.load(f)
        self.assertEqual(config['parameters']['Sexual_Debut_Age_Setting_Type'], 
                            setting_type, 
                            msg=f'Test failed: Sexual_Debut_Age_Setting_Type should be FROM_INTERVENTION.')
        return 
    
    def validate_tracker_events_report_output_file(self, local_path):
        # validate files exist
        file_path = local_path / 'output' / 'ReportEventRecorder.csv'
        self.assertTrue(file_path.is_file(), msg=f'Test failed: ReportEventRecorder.csv is not generated.')
        
        # validate Report Evenet Recorder contents
        report_df = pd.read_csv(file_path)
        sti_debut_df = report_df[report_df['Event_Name'] == 'STIDebut'] 
        self.assertGreater(len(sti_debut_df), 0, msg=f'Test failed: there are should be some STIDebut events.')
        # validate the existance of Setting_Age_Sexual_Debut events in report_df
        sasd_debut_df = report_df[report_df['Event_Name'] == 'Setting_Age_Sexual_Debut'] 
        self.assertGreater(len(sasd_debut_df), 0, msg=f'Test failed: there are should be some Setting_Age_Sexual_Debut events.')

    def validate_tracker_HIVByAgegender_UserSpecified(self, local_path,  cases):
        #validate if 'ReportHIVByAgeAndGender.csv' is generated
        report_path = local_path / files.ReportHIVByAgeAndGender
        report_df = pd.read_csv(report_path)
       
        for case in cases:
            gender = case[0]
            specified_age = case[1]

            # create a subset of the report_df for the given case
            df = report_df[(report_df[' Age'] == specified_age) & (report_df[' Gender'] == gender)]
            # print(df['Has Debuted'].to_list(),  df['Had First Coital Act'].to_list())
            hasdeb_mean = df['Has Debuted'].mean()
            hadfirst_mean = df['Had First Coital Act'].mean()
            self.assertNotEqual(hasdeb_mean, 0, f'Test failed: "Has Debuted" should not be 0 \n\n Age: {specified_age} Gender: {gender}')
            self.assertNotEqual(hadfirst_mean, 0, f'Test failed: "Had First Coital Act" should not be 0 \n\n Age: {specified_age} Gender: {gender}')
            print(f"For Gender: {gender} & Age {specified_age}: Mean of Has Debuted: {hasdeb_mean}, Mean of Had First Coital Act: {hadfirst_mean}\n\n")


            df = report_df[(report_df[' Age'] < specified_age) & (report_df[' Gender'] == gender)]
            hasdeb_mean = df['Has Debuted'].mean()
            hadfirst_mean = df['Had First Coital Act'].mean()
            # print(df['Has Debuted'].to_list(),  df['Had First Coital Act'].to_list())
            self.assertEqual(hasdeb_mean, 0, f'Test failed: "Has Debuted" should be 0 \n\n For age less than: {specified_age} and Gender: {gender}')
            self.assertEqual(hadfirst_mean, 0, f'Test failed: "Had First Coital Act" should be 0 \n\n For age less than: {specified_age} and Gender: {gender}')       
        return


if __name__ == '__main__':
    unittest.main()

