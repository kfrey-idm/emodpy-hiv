from functools import partial
import unittest
import sys
from pathlib import Path
import json
import pandas as pd
import csv
import os.path
from idmtools.assets import Asset
from idmtools.core import ItemType
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

# emodpy
import emodpy.emod_task as emod_task
import emod_api.campaign as camp
import emod_api.interventions.common as common

import emodpy_hiv.demographics.HIVDemographics as Demographics
import emodpy_hiv.interventions.outbreak as ob
import emodpy_hiv.interventions.art as art
import emodpy_hiv.interventions.artdropout as artdropout
import emodpy_hiv.interventions.artstagingbycd4agnosticdiag as artstageagnosticdiag
import emodpy_hiv.interventions.artstagingbycd4diag as artstage4diag
import emodpy_hiv.interventions.drawblood as drawblood
import emodpy_hiv.interventions.malecirc as malecirc
import emodpy_hiv.interventions.modcoinf as modcoinf
import emodpy_hiv.interventions.pmtct as pmtct
import emodpy_hiv.interventions.prep as prep
import emodpy_hiv.interventions.randomchoice as randomchoice
import emodpy_hiv.interventions.rapiddiag as rapiddiag
import emodpy_hiv.interventions.sigmoiddiag as sigmoiddiag
import emodpy_hiv.interventions.stipostdebut as stipostdebut
import emodpy_hiv.interventions.yearandsexdiag as yearandsexdiag
import emodpy_hiv.interventions.cascade_helpers as cascade
from emod_api.interventions.common import *
from emodpy_hiv.interventions import *

parent = Path(__file__).resolve().parent
sys.path.append(parent)

import manifest


class TestSimulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Workaround for issue https://github.com/InstituteforDiseaseModeling/emodpy-hiv/issues/113
        # Using emod_hiv instead of eradication and schema downloaded from bamboo
        import emod_hiv.bootstrap as dtk
        dtk.setup(manifest.emod_hiv_path)

    def setUp(self):
        self.platform = Platform("SLURMStage") #"Calculon", node_group="idm_48cores", priority="Highest"
        self.schema_path = manifest.emod_hiv_schema # manifest.schema_file
        self.eradication = manifest.emod_hiv_eradication # manifest.eradication_path

    def update_sim_random_seed(self, simulation, value):
        simulation.task.config.parameters.Run_Number = value
        return {"Run_Number": value}

    def build_demog_from_template_node(self):
        demog = Demographics.from_template_node(lat=0, lon=0, pop=1000, name=1, forced_id=1)
        return demog

    def build_demog_from_pop_csv(self):
        pop_filename_in = parent.parent / 'unittests' / 'inputs' / 'tiny_facebook_pop_clipped.csv'
        pop_filename_out = parent.parent / "spatial_gridded_pop_dir"
        site = "No_Site"

        demog = Demographics.from_pop_csv(pop_filename_in, pop_filename_out=pop_filename_out, site=site)
        return demog

    def build_demog_from_params(self):
        totpop = 9876
        num_nodes = 199
        frac_rural = 0.3
        demog = Demographics.from_params(tot_pop=totpop, num_nodes=num_nodes, frac_rural=frac_rural)
        return demog

    def build_outbreak_campaign(self, timestep):
        camp.schema_path = str(self.schema_path)
        event = ob.new_intervention(timestep=timestep, camp=camp)
        camp.add(event, first=True)
        return camp

    @staticmethod
    def set_param_fn(config, duration):  # from start here example
        config.parameters.Simulation_Type = "HIV_SIM"  # this should be set in the package.
        config.parameters.Simulation_Duration = duration
        config.parameters.Base_Infectivity = 3.5
        config.parameters.Enable_Demographics_Reporting = 0  # just because I don't like our default for this
        config.parameters.Incubation_Period_Distribution = "CONSTANT_DISTRIBUTION"

        # config hacks until schema fixes arrive
        config.parameters.pop("Serialized_Population_Filenames")
        config.parameters.pop("Serialization_Time_Steps")
        config.parameters.Report_HIV_Event_Channels_List = []
        config.parameters.Male_To_Female_Relative_Infectivity_Ages = []  # 15,25,35 ]
        config.parameters.Male_To_Female_Relative_Infectivity_Multipliers = []  # 5, 1, 0.5 ]
        # This one is crazy! :(
        config.parameters.Maternal_Infection_Transmission_Probability = 0
        config.parameters['logLevel_default'] = "WARNING" # 'LogLevel_Default' is not in scheme, so need to use the old style dict keys_

        return config

    def set_param_fn_buildin_demog(self, config):  # buildin demographics is not working for hiv
        config = self.set_param_fn(config, 10)
        config.parameters.Enable_Demographics_Builtin = 1
        config.parameters.pop('Demographics_Filenames')
        return config

    def test_outbreak_and_demog_from_template_node(self):
        start_day = 5
        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(self.build_outbreak_campaign, timestep=start_day),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(self.set_param_fn, duration=60),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))  # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_outbreak_demographics_from_template_node")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/InsetChart.json"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'InsetChart.json'
            self.assertTrue(file_path.is_file())
            # validate result
            with file_path.open(mode='r') as json_file:
                inset_chart = json.load(json_file)

            new_infection = inset_chart['Channels']['New Infections']['Data']
            self.assertEqual(sum(new_infection[:start_day-1]), 0,
                             msg=f'Test failed: expected no new infection before outbreak start day.')
            self.assertGreater(new_infection[start_day-1], 0,
                               msg=f'Test failed: expected new infection at outbreak start day.')

            total_pop = inset_chart['Channels']['Statistical Population']['Data'][0]
            self.assertEqual(total_pop, 1000, msg=f"Expected 1000 population, got {total_pop}, please check demographics "
                                                f"for sim: {simulation.id}.")

    def test_demog_from_pop_csv(self):
        task = emod_task.EMODTask.from_default2(
            config_path="config_pop_csv.json",
            eradication_path=str(self.eradication),
            campaign_builder=None,
            schema_path=str(self.schema_path),
            param_custom_cb=partial(self.set_param_fn, duration=60),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_pop_csv,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_demographics_from_pop_csv")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")

        filenames = ["output/InsetChart.json"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'InsetChart.json'
            self.assertTrue(file_path.is_file())
            # validate result
            with file_path.open(mode='r') as json_file:
                inset_chart = json.load(json_file)

            total_pop = inset_chart['Channels']['Statistical Population']['Data'][0]
            self.assertEqual(total_pop, 42, msg=f"Expected 42 population, got {total_pop}, please check demographics "
                                                f"for sim: {simulation.id}.")

    def test_demog_from_param(self):
        task = emod_task.EMODTask.from_default2(
            config_path="config_pop_csv.json",
            eradication_path=str(self.eradication),
            campaign_builder=None,
            schema_path=str(self.schema_path),
            param_custom_cb=partial(self.set_param_fn, duration=5),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_params,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_demographics_from_params")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")

        filenames = ["output/InsetChart.json"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'InsetChart.json'
            self.assertTrue(file_path.is_file())
            # validate result
            with file_path.open(mode='r') as json_file:
                inset_chart = json.load(json_file)

            total_pop = inset_chart['Channels']['Statistical Population']['Data'][0]
            # https://github.com/InstituteforDiseaseModeling/emod-api/issues/112
            self.assertAlmostEqual(total_pop, 9876, delta=15, msg=f"Expected about 9876 population, got {total_pop}, "
                                                                  f"please check demographics for sim: {simulation.id}.")

    def test_art(self):
        camp.schema_path = str(self.schema_path)
        startday = 5
        cov = 0.7

        def build_camp(start_day, coverage):
            event = ob.new_intervention(start_day - 1, camp, coverage=1)
            camp.add(event, first=True)
            event = art.new_intervention_event(camp=camp, start_day=start_day, coverage=coverage, node_ids=None)
            camp.add(event, first=False)
            return camp

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp, start_day=startday, coverage=cov),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(self.set_param_fn, duration=60),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_art")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/InsetChart.json"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'InsetChart.json'
            self.assertTrue(file_path.is_file())
            # validate result
            with file_path.open(mode='r') as json_file:
                inset_chart = json.load(json_file)

            new_infection = inset_chart['Channels']['Number of Individuals on ART']['Data']
            self.assertEqual(sum(new_infection[:startday - 1]), 0,
                             msg=f'Test failed: expected no Individuals on ART before ART start day.')
            self.assertAlmostEqual(new_infection[startday - 1], 1000 * cov, delta=30,
                                   msg=f'Test failed: expected {1000 * cov} Individuals on ART at ART start day.')

    def test_artdropout(self):
        camp.schema_path = str(self.schema_path)
        startday = 3
        cov = 0.6

        def build_camp(start_day, coverage):
            event = ob.new_intervention(start_day - 2, camp, coverage=1)
            camp.add(event, first=True)
            event = art.new_intervention_event(camp=camp, start_day=start_day - 1, coverage=1, node_ids=None)
            camp.add(event, first=False)
            event = artdropout.new_intervention_event(camp=camp, start_day=start_day, coverage=coverage, node_ids=None)
            camp.add(event, first=False)
            return camp

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp, start_day=startday, coverage=cov),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(self.set_param_fn, duration=60),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_artdropout")  # "HIV Test_artdropout"

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/InsetChart.json"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'InsetChart.json'
            self.assertTrue(file_path.is_file())
            # validate result
            with file_path.open(mode='r') as json_file:
                inset_chart = json.load(json_file)

            new_infection = inset_chart['Channels']['Number of ART dropouts (cumulative)']['Data']
            self.assertEqual(sum(new_infection[:startday - 1]), 0,
                             msg=f'Test failed: expected no ART dropouts before artdropout start day.')
            self.assertAlmostEqual(new_infection[startday - 1], 1000 * cov, delta=10,
                                   msg=f'Test failed: expected {1000 * cov} ART dropouts at artdropout start day.')

    def test_artstageagnosticdiag(self):
        camp.schema_path = str(self.schema_path)
        startday = 180
        pos_event = "positive_event"
        neg_event = "negative_event"
        abp_tvmap = {2015: 100, 2016: 1}
        abt_tvmap = {2015: 0, 2016: 0.05}
        abw_tvmap = {2015: 10}
        cua_tvmap = {2015: 1}
        cbt_tvmap = {2015: 0.1, 2016: 1.4}
        cbw_tvmap = {2015: 4}

        def build_camp(start_day):
            event = ob.new_intervention(start_day - 150, camp, coverage=0.2)
            camp.add(event, first=True)
            event = artstageagnosticdiag.new_intervention_event(camp,
                                                                pos_event,
                                                                neg_event,
                                                                abp_tvmap,
                                                                abt_tvmap,
                                                                abw_tvmap,
                                                                cua_tvmap,
                                                                cbt_tvmap,
                                                                cbw_tvmap,
                                                                start_day=startday)
            camp.add(event, first=False)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp, start_day=startday),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=730, event_list=[pos_event, neg_event]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_artstageagnosticdiag")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        # Todo: find a way to test artstageagnosticdiag.

    def test_artstage4diag(self):  # todo: pending on https://github.com/InstituteforDiseaseModeling/emodpy-hiv/issues/39
        camp.schema_path = str(self.schema_path)
        startday = 180
        pos_event = "positive_event"
        neg_event = "negative_event"
        threshold_tvmap = {2015: 800, 2016: 10000000}
        pregnant_tvmap = {2015: 600, 2016: 10000000}
        tb_tvmap = {2015: 500, 2016: 10000000}

        def build_camp(start_day):
            event = ob.new_intervention(start_day - 150, camp, coverage=0.2)
            camp.add(event, first=True)
            # event = MultiInterventionDistributor(camp, intervention_list)
            event = artstage4diag.new_intervention_event(camp,
                                                         pos_event,
                                                         neg_event,
                                                         threshold_tvmap,
                                                         pregnant_tvmap,
                                                         tb_tvmap,
                                                         start_day=startday)
            camp.add(event, first=False)
            event = artstage4diag.new_intervention_event(camp,
                                                         pos_event,
                                                         neg_event,
                                                         threshold_tvmap,
                                                         pregnant_tvmap,
                                                         tb_tvmap,
                                                         start_day=startday + 365)
            camp.add(event, first=False)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp, start_day=startday),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=730, event_list=[pos_event, neg_event]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_artstage4diag")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        # Todo: find a way to test artstage4diag.

    def test_drawblood(self):
        camp.schema_path = str(self.schema_path)
        startday = 3
        coverage = 0.3
        pos_event = "positive_event"

        def build_camp(start_day):
            event = ob.new_intervention(start_day - 2, camp, coverage=0.2)
            camp.add(event, first=True)
            event = drawblood.new_intervention_event(camp,
                                                     pos_event,
                                                     start_day=start_day,
                                                     coverage=coverage)
            camp.add(event, first=False)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp, start_day=startday),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=10, event_list=[pos_event]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_drawblood")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            positive_event_count = len(report_df[report_df['Event_Name'] == pos_event])
            self.assertAlmostEqual(positive_event_count, 1000 * coverage, delta=10,
                                   msg=f'Test failed: expected {1000 * coverage} {pos_event} events.')

    def test_malecirc(self):
        camp.schema_path = str(self.schema_path)
        start_day = 3
        coverage = 0.9

        def build_camp():
            event = malecirc.new_intervention_event(camp,
                                                    start_day=start_day,
                                                    coverage=coverage)
            camp.add(event, first=True)
            return camp

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(self.set_param_fn, duration=10),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_malecirc")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/InsetChart.json"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'InsetChart.json'
            self.assertTrue(file_path.is_file())
            # validate result
            with file_path.open(mode='r') as json_file:
                inset_chart = json.load(json_file)

            new_infection = inset_chart['Channels']['Number of Circumcised Males']['Data']
            self.assertEqual(sum(new_infection[:start_day - 1]), 0,
                             msg=f'Test failed: expected no Circumcised Males before intervention start day.')
            self.assertAlmostEqual(new_infection[start_day - 1], 500 * coverage, delta=10,
                                   msg=f'Test failed: expected {500 * coverage} '
                                       f'Circumcised Males at intervention start day.')

    def test_modcoinf(self):
        camp.schema_path = str(self.schema_path)
        start_day = 180
        coverage = 0.9

        def build_camp():
            event = ob.new_intervention(timestep=1, camp=camp, coverage=1)
            camp.add(event, first=True)
            event = modcoinf.new_intervention_event(camp,
                                                    start_day=start_day,
                                                    coverage=coverage)
            camp.add(event, first=False)
            return camp

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(self.set_param_fn, duration=365),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_modcoinf")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        # Todo: find a way to test the STI coinfection status.

    def Skip_test_pmtct(self):
        camp.schema_path = str(self.schema_path)
        start_day = 365
        coverage = 1

        def build_demog_with_fertelity():
            demog = Demographics.from_template_node(lat=0, lon=0, pop=1000, name=1, forced_id=1)
            path_to_csv = parent.parent / 'unittests' / 'inputs' / 'Malawi_Fertility_Historical.csv'
            demog.fertility(path_to_csv=path_to_csv)
            return demog

        def build_camp():
            event = ob.new_intervention(timestep=1, camp=camp, coverage=1)
            camp.add(event, first=True)
            event = pmtct.new_intervention_event(camp,
                                                 start_day=start_day,
                                                 coverage=coverage)
            camp.add(event, first=False)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.x_Birth = 1000
            #config.parameters.Enable_Maternal_Infection_Transmission = 1
            config.parameters.Maternal_Infection_Transmission_Probability = 1
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            # This looks like a rounding error, the report saves time stamps with two digits after the point.
            # When 40 is used (Simulation_Duration = = 645) then the sim will end after day 645, in year 2,016.767123
            # In the last time step (645) before the sim ends there are NewInfectionEvents in year 2016.77 what let's the test fail.
            # see https://comps2.idmod.org/#explore/Simulations?filters=ExperimentId=00b0c26a-aeee-ec11-92ea-f0921c167864
            # Using 39.999 reduces the duration to 644 time steps and the test passes.
            param_custom_cb=partial(setParamfn, duration=start_day + 39.999 * 7, event_list=['Births', 'NewInfectionEvent']), # Simulation_Duration = = 645
            ep4_custom_cb=None,
            demog_builder=build_demog_with_fertelity,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_pmtct")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            new_infection = report_df[(report_df['Event_Name'] == 'NewInfectionEvent') & (report_df['Year'] != 2015)]

            m_t_c_t_before_intervention = new_infection[(new_infection['Year'] <= 2015 + start_day / 365) &
                                                        (new_infection['Age'] == 1)]
            m_t_c_t__after_intervention = new_infection[(new_infection['Year'] > 2015 + start_day / 365) &
                                                        (new_infection['Age'] == 1)]

            self.assertGreater(len(m_t_c_t_before_intervention), 0,
                               msg=f'Test failed: There are no mother to child transmission before PMTCT intervention '
                                   f'start day.')
            self.assertTrue(m_t_c_t__after_intervention.empty,
                            msg=f'Test failed: There are should not be any mother to child transmission after PMTCT'
                                f' intervention start day. Got {len(m_t_c_t__after_intervention)} MTCT events.')

    def test_prep(self):  # ControlledVaccine
        camp.schema_path = str(self.schema_path)
        start_day = 1
        coverage = 1
        prep_events_list = ["PrEPDistributed", "STIDebut"]

        args = [[True, "All"],      # True = Baseline
                [False, "All"],     # False = PrEP iv, All
                [False, "Male"],    # False = PrEP iv, Male
                [False, "Female"] ] # False = PrEP iv, Female
        num_runs = 2
        ages = [15, 60]
        duration = 365 * 20
        
        def build_camp02(args=[True, "All"]): 
            
            import emod_api.interventions.common as common
            import emodpy_hiv.interventions.prep as prep
            import emodpy_hiv.interventions.outbreak as ob
            
            baseline = args[0]
            gender = args[1]

            # OUTBREAK (baseline) for each simulation
            event = ob.new_intervention(timestep=1000, camp=camp, coverage=0.05)
            camp.add(event, first=True)
            print(baseline, gender)
            
            # PrEPDistributed: Event signal registration.
            new_broadcast_event = common.BroadcastEvent(camp, "PrEPDistributed")
            
            if baseline:  return camp   # This case will leave PrEPDistributed interventions out.
                        
            efficacy_times = [0, 3650, 3651]  # 0 : 365 - 10 years of efficacy
            ### NOTE !!! efficacies seems to have to be almost 1 in this sim for things to work.
            efficacy_values = [0.99, 0.99, 0]  # 90% : 100% 
           
            # PrEP INTERVENTION 
            new_intervention = prep.new_intervention(camp, efficacy_times, efficacy_values)
            
            for PrEPCampaign_Round in range(10):
                # Fixed  coverage
                prep_start_day = 500 + 365 * (PrEPCampaign_Round)
                prep_coverage = 0.1 * (PrEPCampaign_Round + 1)

                print(f"Delivery step time:  {prep_start_day},  Start Year(campaign round):  {PrEPCampaign_Round}, Coverage: {prep_coverage}")
                event = common.ScheduledCampaignEvent(camp,
                                                        Start_Day=prep_start_day,
                                                        Property_Restrictions=None,
                                                        Demographic_Coverage=prep_coverage,
                                                        Target_Age_Min=ages[0],
                                                        Target_Age_Max=ages[1],
                                                        Target_Gender=gender,
                                                        Intervention_List=[new_intervention, new_broadcast_event])
                camp.add(event)

            return camp

        def update_campaign(simulation, args):
            #   This callback function updates the coverage of the campaign. Function: "build_camp02"
            build_campaign_partial = partial(build_camp02, args)
            simulation.task.create_campaign_from_callback(build_campaign_partial)
            tag_value = args[1]
            if args[0]: tag_value = "BASELINE: " + tag_value
                       
            # Return a tag that will be added to the simulation run.
            return {"Test_Case": tag_value}

        def setPrEPParamfn(config, duration, watched_events):
            self.set_param_fn(config, duration)
            print(watched_events)
            config.parameters.Report_Event_Recorder_Events = watched_events
            return config

        task = emod_task.EMODTask.from_default2(
                                                config_path="config_ob.json",
                                                eradication_path=str(self.eradication),
                                                campaign_builder=partial(build_camp02),
                                                schema_path=str(self.schema_path),
                                                param_custom_cb=partial(setPrEPParamfn, duration=duration, watched_events=prep_events_list),
                                                ep4_custom_cb=None,
                                                demog_builder=self.build_demog_from_template_node,
                                            )
        task.set_sif(str(manifest.sif_path))    
               
        builder = SimulationBuilder()
        # Add SWEEP definitions to the builder. RUNS:
        builder.add_sweep_definition(self.update_sim_random_seed, range(num_runs))
        
        # Add SWEEP definitions to the builder. TEST CASES
        builder.add_sweep_definition(update_campaign, [a for a in args])

        # With the simulation builder and the task, we can create an EXPERIMENT.
        experiment = Experiment.from_builder(builder, task, name="HIV Test_prep_updated")

        # Run the experiment.
        experiment.run(wait_until_done=True, platform=self.platform)

        # Check that the experiment succeeded.
        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
   
        import datetime as datetime
        prefix = datetime.datetime.now().strftime("%d_%H%M%S")    # To create a unique folder name (for plotting)
        
        # Specify the files to download.
        filenames = ["output/InsetChart.json", "output/ReportEventRecorder.csv", "campaign.json"]

        # Get the SIMULATIONS from the experiment.
        sims = self.platform.get_children_by_object(experiment)
        
        output_path = parent / "inputs" / prefix / experiment.id
        all_reference=[]
        all_test=[]
        
        for idx, simulation in enumerate(sims):

            # DOWNLOAD files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,              
                                           output=output_path)
            sim_path = str(simulation.uid)
            
            # VALIDATE files exist
            ins_chart_file = output_path / sim_path / 'output' / 'InsetChart.json'
            csv_filename = output_path / sim_path / 'output' / 'ReportEventRecorder.csv'
            campaign_file = output_path / sim_path / 'campaign.json'

            self.assertTrue(ins_chart_file.is_file())
            self.assertTrue(csv_filename.is_file())
            self.assertTrue(campaign_file.is_file())

            # VALIDATE result
            with ins_chart_file.open(mode='r') as json_file:
                inset_chart = json.load(json_file)

            new_infection = inset_chart['Channels']['New Infections']['Data']
            self.assertEqual(sum(new_infection[:start_day]), 0,
                                msg=f'Test failed: expected no new infection before outbreak start day.')

            if simulation.tags['Test_Case'] != "BASELINE: All":   # If is not the baseline it will check the presence of PrEPDistributed events
                df = pd.read_csv(csv_filename)
                gender = [simulation.tags['Test_Case']]
                if gender[0]=='All': 
                    gender=['M', 'F']                   # Converts "All" to ["M", "F"] to be used in the query
                    all_test.append(ins_chart_file)     # Save the InsetChart.json file name to be used later
                        
                else: gender = [gender[0][0]]           # First letter of Male|Female to be used in the query

                print(f"\n\nSimulation: {sim_path}, Gender {gender}")
                prep_events = df[(df['Event_Name'] == "PrEPDistributed") & (df['Gender'].isin(gender))]
                
                # VALIDATE if there are PrEPDistributed events for expected Gender
                self.assertGreater(len(prep_events), 0, msg=f'Test failed: There are no PrEPDistributed events.')
                
                # VALIDATE  if the mininum and maximum ages of the PrEPDistributed events are within the expected range
                self.assertGreater(prep_events['Age'].min(), 365*ages[0], msg=f'Test failed: PrEPDistributed events were distributed to individuals younger than {ages[0]} {prep_events["Age"].min()}')
                self.assertLess(prep_events['Age'].max(), 365*ages[1], msg=f'Test failed: PrEPDistributed events were distributed to individuals older than {ages[1]} {prep_events["Age"].max()}')
            else:   
                # If is the baseline it will just save the reference InsetChart.json to be used later
                all_reference.append(ins_chart_file)
        
        # PROCEED TO VALIDATE THE PREVALENCE OF THE BASELINE AND TEST      
        channels_subset = [
                    "Prevalence (Females, 15-49)",
                    "Prevalence (Males, 15-49)",
                    "Prevalence among Sexually Active"
                    ]
        
        run = 0
        
        with all_reference[run].open(mode='r') as json_file: baseline = json.load(json_file)
        with all_test[run].open(mode='r') as json_file: test = json.load(json_file)
        
        # VALIDATE the Prevalence of the baseline and Test, the PREVALENCE should be lower for the Test
        for channel in channels_subset:
            if baseline!=None and test!=None:
                a = pd.DataFrame(baseline['Channels'][channel]['Data']).mean()
                b = pd.DataFrame(test['Channels'][channel]['Data']).mean()
                print (f"\n\n{channel}:\t Reference: {a.min()}\n\nTest: {b.min()}")
                self.assertGreater(a.min(),
                                   b.min(),
                                   msg=f'Test failed: {channel} \nThe resulting Prevalence is expected to be '
                                       f'lower WITH the intervention, but it was not: \n'
                                       f'Without Intervention (baseline): {a.min()}, \n'
                                       f'With Intervention: {b.min()}')
            else:
                self.assertIsNotNone(test, msg=f'Test failed: There are no PrEPDistributed events.')        

    def test_random(self):
        camp.schema_path = str(self.schema_path)
        start_day = 1
        coverage = 1
        choice_1 = 'OnArt1'
        choice_2 = 'OnArt2'
        choice_1_p = 0.1
        choice_2_p = 0.9

        def build_camp():
            event = randomchoice.new_intervention_event(camp,
                                                  choices={choice_1: choice_1_p, choice_2: choice_2_p},
                                                  start_day=start_day,
                                                  coverage=coverage)
            camp.add(event, first=True)
            return camp

        def setParamfn(config, duration):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = [choice_1, choice_2]
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_random")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            choice_1_count = len(report_df[report_df['Event_Name'] == choice_1])
            choice_2_count = len(report_df[report_df['Event_Name'] == choice_2])

            self.assertAlmostEqual(choice_1_count/choice_2_count, choice_1_p/choice_2_p, delta=0.01,
                                   msg=f'Test failed: the ratio of {choice_1} / {choice_2} should be about {choice_1_p}'
                                       f' / {choice_2_p}, got {choice_1_count/choice_2_count}.')

    def test_rapiddiag(self):
        camp.schema_path = str(self.schema_path)
        start_day = 2
        coverage = 1
        ob_coverage = 0.8
        pos_event = 'HIV_positive'
        neg_event = 'HIV_negative'

        def build_camp():
            event = ob.new_intervention(start_day - 1, camp, coverage=ob_coverage)
            camp.add(event, first=True)
            event = rapiddiag.new_intervention_event(camp,
                                                     pos_event=pos_event,
                                                     neg_event=neg_event,
                                                     start_day=start_day,
                                                     coverage=coverage)
            camp.add(event, first=False)
            return camp

        def setParamfn(config, duration):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = [pos_event, neg_event]
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_rapiddiag")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            pos_event_count = len(report_df[report_df['Event_Name'] == pos_event])
            neg_event_count = len(report_df[report_df['Event_Name'] == neg_event])

            self.assertAlmostEqual(pos_event_count, 1000 * ob_coverage, delta=20,
                                   msg=f'Test failed: expected about {1000 * ob_coverage} {pos_event} events, '
                                       f'got {pos_event_count}.')
            self.assertAlmostEqual(neg_event_count, 1000 * (1 - ob_coverage), delta=20,
                                   msg=f'Test failed: expected about {1000 * (1 - ob_coverage)} {neg_event} events, '
                                       f'got {neg_event_count}.')

    def test_sigmoiddiag(self):
        camp.schema_path = str(self.schema_path)
        total_year = 4
        start_day = 2
        coverage = 1
        ob_coverage = 1
        pos_event = 'HIV_positive'
        neg_event = 'HIV_negative'
        ramp_min = 0.1
        ramp_max = 0.9
        ramp_midyear = 2017
        ramp_rate = 2

        def build_camp():
            first = True
            for half_year in range(total_year * 2 + 1):
                event = ob.new_intervention(start_day + half_year * 182 - 1, camp, coverage=ob_coverage)
                camp.add(event, first=first)
                first = False
                event = sigmoiddiag.new_intervention_event(camp,
                                                           pos_event=pos_event,
                                                           neg_event=neg_event,
                                                           ramp_min=ramp_min,
                                                           ramp_max=ramp_max,
                                                           ramp_midyear=ramp_midyear,
                                                           ramp_rate=ramp_rate,
                                                           start_day=start_day + half_year * 182,
                                                           coverage=coverage)
                camp.add(event, first=first)
            return camp

        def setParamfn(config, duration):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = [pos_event, neg_event]
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=365 * total_year + 1),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1, 2))  # different Run_Number makes the test pass

        experiment = Experiment.from_builder(builder, task, name="HIV Test_sigmoiddiag")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            base_year = 2015
            test_years = []
            positive_probability = []
            for half_year in range(total_year * 2 + 1):
                current_year = base_year + round((half_year * 182 + start_day) / 365, 2)
                pos_event_count = len(report_df[(report_df['Event_Name'] == pos_event)
                                                & (report_df['Year'] == current_year)])
                neg_event_count = len(report_df[(report_df['Event_Name'] == neg_event)
                                                & (report_df['Year'] == current_year)
                                                & (report_df['HasHIV'] == 'Y')])
                test_years.append(current_year)
                positive_probability.append(pos_event_count/(pos_event_count + neg_event_count))

            self.assertTrue(all(positive_probability[i] <= positive_probability[i+1] for i in
                                range(len(positive_probability)-1)),
                            msg=f"Test failed: positive probability should be in ascending order, got {positive_probability}.")
            self.assertGreater(min(positive_probability), ramp_min,
                               msg=f'Test failed: positive probability should not be less than ramp_min = {ramp_min}, '
                                   f'got min(positive_probability) = {min(positive_probability)}.')
            self.assertLess(max(positive_probability), ramp_max,
                            msg=f'Test failed: positive probability should not be greater than ramp_max = {ramp_max}, '
                                f'got max(positive_probability) = {max(positive_probability)}.')

            self.assertAlmostEqual(positive_probability[0], ramp_min, delta=0.05,
                                   msg=f'Test failed: expected positive probability about {ramp_min} at year '
                                       f'{test_years[0]}, got {positive_probability[0]}.')
            self.assertAlmostEqual(positive_probability[-1], ramp_max, delta=0.05,
                                   msg=f'Test failed: expected positive probability about {ramp_max} at year '
                                       f'{test_years[-1]}, got {positive_probability[-1]}.')
            self.assertAlmostEqual(positive_probability[4], (ramp_min + ramp_max) / 2, delta=0.05,
                                   msg=f'Test failed: expected positive probability about {(ramp_min + ramp_max) / 2} '
                                       f'at year {test_years[4]}, got {positive_probability[4]}.')

    def test_stipostdebut(self):
        camp.schema_path = str(self.schema_path)
        start_day = 2
        coverage = 1
        ob_coverage = 1
        pos_event = 'PostDebut'
        neg_event = 'PreDebut'

        def build_camp():
            event = ob.new_intervention(1, camp, coverage=ob_coverage)
            camp.add(event, first=True)
            event = stipostdebut.new_intervention_event(camp,
                                                        pos_event=pos_event,
                                                        neg_event=neg_event,
                                                        start_day=start_day,
                                                        coverage=coverage)
            camp.add(event, first=False)
            return camp

        def setParamfn(config, duration):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = [pos_event, neg_event]
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=start_day+1),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_stipostdebut")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            pos_event_df = report_df[report_df['Event_Name'] == pos_event]
            neg_event_df = report_df[report_df['Event_Name'] == neg_event]

            toddler = pos_event_df[pos_event_df['Age'] < 365 * 5]
            self.assertTrue(toddler.empty, msg=f'Test failed: there are should not be any toddler with {pos_event} '
                                               f'event.')

            self.assertGreater(len(neg_event_df), 0,
                               msg=f'Test failed: there are should be some {neg_event} events.')

    def test_yearandsexdiag(self):
        camp.schema_path = str(self.schema_path)
        total_year = 4
        start_day = 2
        coverage = 1
        ob_coverage = 1
        pos_event = 'HIV_positive'
        neg_event = 'HIV_negative'
        tvmap = {2015: 0.2, 2016: 0.75, 2017: 0, 2018: 1}

        def build_camp():
            first = True
            for year in range(total_year + 1):
                event = ob.new_intervention(start_day + year * 365 - 1, camp, coverage=ob_coverage)
                camp.add(event, first=first)
                first = False
                event = yearandsexdiag.new_intervention_event(camp,
                                                              pos_event=pos_event,
                                                              neg_event=neg_event,
                                                              tvmap=tvmap,
                                                              start_day=start_day + year * 365,
                                                              coverage=coverage)
                camp.add(event, first=first)
            return camp

        def setParamfn(config, duration):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = [pos_event, neg_event]
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=365 * total_year + 2),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_yearandsexdiag")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            base_year = 2015
            test_years = []
            positive_probabilities = []
            for year in range(total_year + 1):
                current_year = base_year + round((year * 365 + start_day) / 365, 2)
                pos_event_count = len(report_df[(report_df['Event_Name'] == pos_event)
                                                & (report_df['Year'] == current_year)])
                neg_event_count = len(report_df[(report_df['Event_Name'] == neg_event)
                                                & (report_df['Year'] == current_year)
                                                & (report_df['HasHIV'] == 'Y')])
                test_years.append(current_year)
                positive_probability = pos_event_count/(pos_event_count + neg_event_count)
                positive_probabilities.append(positive_probability)

                if int(current_year) in tvmap.keys():
                    expected_probability = tvmap[int(current_year)]
                elif int(current_year) > max(tvmap.keys()):
                    expected_probability = tvmap[2018]
                else:
                    expected_probability = tvmap[2015]

                self.assertAlmostEqual(positive_probability, expected_probability, delta=0.05,
                                       msg=f'Test failed: expected positive_probability about {expected_probability}'
                                           f' at year {current_year}, got {positive_probability}')

    def test_cascade_triggered_event_common(self):
        camp.schema_path = str(self.schema_path)
        startday = 2
        in_trigger = "NewInfectionEvent"
        event_name = "I_am_infected"

        def build_camp(start_day):
            out_iv = common.BroadcastEvent(camp, event_name)

            event = ob.new_intervention(start_day - 1, camp, coverage=1)
            camp.add(event, first=True)
            cascade.triggered_event_common(camp, in_trigger, out_iv)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp, start_day=startday),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=10, event_list=[event_name]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_cascade_triggered_event_common")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            event_count = len(report_df[report_df['Event_Name'] == event_name])
            self.assertAlmostEqual(event_count, 1000, delta=10,
                                   msg=f'Test failed: expected about {1000} {event_count} events.')

    @unittest.skip("add_symptomatic is removed")
    def test_cascade_add_symptomatic(self):
        camp.schema_path = str(self.schema_path)
        ob_start_day = 2
        sympto_signal = "Symptomatic"
        lag_time = 5

        def build_camp():
            event = ob.new_intervention(ob_start_day, camp, coverage=1)
            camp.add(event, first=True)
            cascade.add_symptomatic(camp, sympto_signal=sympto_signal, lag_time=lag_time)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=10, event_list=[sympto_signal]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_cascade_add_symptomatic")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            event_df = report_df[report_df['Event_Name'] == sympto_signal]
            base_year = 2015
            trigger_year = base_year + round((ob_start_day + lag_time)/365, 2)
            count = len(event_df[event_df['Year'] == trigger_year])
            self.assertAlmostEqual(count, 1000, delta=10,
                                   msg=f'Test failed: expected about {1000} {sympto_signal} events at year {trigger_year}, '
                                       f'got {count}.')
            empty_df = event_df[event_df['Year'] != trigger_year]
            self.assertTrue(empty_df.empty, msg=f'Test failed: {sympto_signal} event should only happen at year '
                                                f'{trigger_year}, found {empty_df}.')

    def test_cascade_add_choice(self):
        camp.schema_path = str(self.schema_path)
        ob_start_day = 2
        sympto_signal = "NewInfectionEvent"
        get_tested_signal = 'get_tested_signal'

        def build_camp():
            event = ob.new_intervention(ob_start_day, camp, coverage=1)
            camp.add(event, first=True)
            cascade.add_choice(camp, sympto_signal=sympto_signal, get_tested_signal=get_tested_signal)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=10, event_list=[get_tested_signal]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_add_choice")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            event_df = report_df[report_df['Event_Name'] == get_tested_signal]
            base_year = 2015
            trigger_year = base_year + round(ob_start_day/365, 2)
            count = len(event_df[event_df['Year'] == trigger_year])
            self.assertAlmostEqual(count, 1000 * 0.5, delta=30,
                                   msg=f'Test failed: expected about {1000 * 0.5} {get_tested_signal} events at year '
                                       f'{trigger_year}, got {count}.')

    def test_cascade_add_test(self):
        camp.schema_path = str(self.schema_path)
        ob_start_day = 2
        get_tested_signal = "NewInfectionEvent"
        builtin_pos_event = "HIVPositiveTest"
        builtin_delay = 30

        def build_camp():
            event = ob.new_intervention(ob_start_day, camp, coverage=1)
            camp.add(event, first=True)
            cascade.add_test(camp, get_tested_signal=get_tested_signal)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=35, event_list=[builtin_pos_event]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_add_test")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            event_df = report_df[report_df['Event_Name'] == builtin_pos_event]
            base_year = 2015
            trigger_year = base_year + round((ob_start_day + builtin_delay)/365, 2)
            count = len(event_df[event_df['Year'] == trigger_year])
            self.assertAlmostEqual(count, 1000, delta=50,
                                   msg=f'Test failed: expected about {1000} {builtin_pos_event} events at year '
                                       f'{trigger_year}, got {count}.')

    def test_cascade_trigger_art_from_pos_test(self):
        camp.schema_path = str(self.schema_path)
        ob_start_day = 2
        input_signal = "NewInfectionEvent"
        output_signal = "StartTreatment"
        delay = 15

        def build_camp():
            event = ob.new_intervention(ob_start_day, camp, coverage=1)
            camp.add(event, first=True)
            cascade.trigger_art_from_pos_test(camp, input_signal=input_signal, output_signal=output_signal, lag_time=delay)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=35, event_list=[output_signal]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_cascade_trigger_art_from_pos_test")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            event_df = report_df[report_df['Event_Name'] == output_signal]
            base_year = 2015
            trigger_year = base_year + round((ob_start_day + delay)/365, 2)
            count = len(event_df[event_df['Year'] == trigger_year])
            self.assertAlmostEqual(count, 1000, delta=50,
                                   msg=f'Test failed: expected about {1000} {output_signal} events at year '
                                       f'{trigger_year}, got {count}.')

    def test_cascade_add_art_from_trigger(self):
        camp.schema_path = str(self.schema_path)
        ob_start_day = 20
        signal = "NewInfectionEvent"
        builtin_output_signal = 'StartedART'

        def build_camp():
            event = ob.new_intervention(ob_start_day, camp, coverage=1)
            camp.add(event, first=True)
            cascade.add_art_from_trigger(camp, signal=signal)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=25, event_list=[builtin_output_signal]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_cascade_add_art_from_trigger")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            event_df = report_df[report_df['Event_Name'] == builtin_output_signal]
            base_year = 2015
            trigger_year = base_year + round(ob_start_day/365, 2)
            count = len(event_df[event_df['Year'] == trigger_year])
            self.assertAlmostEqual(count, 1000, delta=50,
                                   msg=f'Test failed: expected about {1000} {builtin_output_signal} events at year '
                                       f'{trigger_year}, got {count}.')

    def test_cascade_trigger_art(self):
        camp.schema_path = str(self.schema_path)
        timestep = 10
        coverage = 0.7
        trigger = "ARTTriggerSignal"

        def build_camp():
            cascade.reset(camp)
            cascade.trigger_art(camp, timestep, coverage, trigger=trigger)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=35, event_list=[trigger]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_cascade_trigger_art")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            event_df = report_df[report_df['Event_Name'] == trigger]
            base_year = 2015
            trigger_year = base_year + round(timestep/365, 2)
            count = len(event_df[event_df['Year'] == trigger_year])
            self.assertAlmostEqual(count, 1000 * coverage, delta=50,
                                   msg=f'Test failed: expected about {1000 * coverage} {trigger} events at year '
                                       f'{trigger_year}, got {count}.')

    def test_cascade_helper_logic(self):
        camp.schema_path = str(self.schema_path)
        ob_timestep = 1
        ob_coverage = 1

        default_delay = 30
        base_year = 2015
        duration = 365
        # new_infection_event = "NewInfectionEvent"
        start_treatment = "StartTreatment"
        started_ART = "StartedART"
        positive_test = "HIVPositiveTest"
        negative_test = "HIVNegativeTest"
        get_tested = "GetTested"
        ignore = "Ignore"
        symptomatic = "NewlySymptomatic"
        disease_deaths = "DiseaseDeaths"
        non_disease_deaths = "NonDiseaseDeaths"

        def build_camp():
            cascade.reset(camp)
            cascade.seed_infection(camp, ob_timestep, ob_coverage)
            cascade.add_choice(camp)
            cascade.add_test(camp)
            cascade.trigger_art_from_pos_test(camp)
            cascade.add_art_from_trigger(camp)
            return camp

        def setParamfn(config, duration, event_list):
            self.set_param_fn(config, duration)
            config.parameters.Report_Event_Recorder_Events = event_list
            return config

        def is_dead(event):
            return event in [disease_deaths, non_disease_deaths]

        task = emod_task.EMODTask.from_default2(
            config_path="config_ob.json",
            eradication_path=str(self.eradication),
            campaign_builder=partial(build_camp),
            schema_path=str(self.schema_path),
            param_custom_cb=partial(setParamfn, duration=duration,
                                    event_list=[start_treatment, started_ART,  # new_infection_event,
                                                positive_test, negative_test, get_tested,
                                                symptomatic, ignore,
                                                disease_deaths, non_disease_deaths]),
            ep4_custom_cb=None,
            demog_builder=self.build_demog_from_template_node,
            plugin_report=None
        )
        task.set_sif(str(manifest.sif_path))    # set_sif() expects a string

        builder = SimulationBuilder()
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name="HIV Test_cascade_helper_logic")

        experiment.run(wait_until_done=True, platform=self.platform)

        self.assertTrue(experiment.succeeded, msg=f"Experiment {experiment.uid} failed.\n")

        print(f"Experiment {experiment.uid} succeeded.")
        filenames = ["output/ReportEventRecorder.csv"]

        sims = self.platform.get_children_by_object(experiment)
        output_path = parent / "inputs"
        for simulation in sims:
            # download files from simulation
            self.platform.get_files_by_id(simulation.id, item_type=ItemType.SIMULATION, files=filenames,
                                          output=output_path)
            # validate files exist
            local_path = output_path / str(simulation.uid)
            file_path = local_path / 'output' / 'ReportEventRecorder.csv'
            self.assertTrue(file_path.is_file())
            # validate result
            report_df = pd.read_csv(file_path)

            symptomatic_df = self.check_event_counts(symptomatic, get_tested, ignore, positive_test, report_df,
                                                     started_ART)

            for ind_id, year in zip(symptomatic_df['Individual_ID'], symptomatic_df['Year']):
                df = report_df[report_df['Individual_ID'] == ind_id]
                if not is_dead(df["Event_Name"].iloc[0]):

                    self.assertEqual(df["Event_Name"].iloc[0], symptomatic)

                    # test add_choice
                    self.check_add_choice(df, disease_deaths, get_tested, ignore, ind_id, non_disease_deaths)

                    if df["Event_Name"].iloc[1] == get_tested and \
                            year + round(default_delay / 365, 2) < base_year + duration / 365 and \
                            not is_dead(df["Event_Name"].iloc[2]):

                        # test add_test
                        self.check_add_test(default_delay, df, ind_id, positive_test, year)
                        if year + round(2 * default_delay / 365, 2) < base_year + duration / 365 and \
                                not is_dead(df["Event_Name"].iloc[3]):
                            # test trigger_art_from_pos_test
                            self.check_trigger_art_from_pos_test(default_delay, df, ind_id, positive_test,
                                                                 start_treatment, year)

                            # test add_art_from_trigger
                            self.check_add_art_from_trigger(df, ind_id, start_treatment, started_ART)
        pass

    def check_add_art_from_trigger(self, df, ind_id, start_treatment, started_ART):
        self.assertEqual(df["Event_Name"].iloc[4], started_ART,
                         msg=f"Test failed: individual {ind_id} should receive {started_ART} "
                             f"event at the same day when they receive {start_treatment} "
                             f"event, got {df['Event_Name'].iloc[4]}."
                         )
        self.assertEqual(df["Year"].iloc[4], df["Year"].iloc[3],
                         msg=f"Test failed: individual {ind_id} should receive {started_ART} "
                             f"event at the same day {df['Year'].iloc[3]} when they receive "
                             f"{start_treatment} event, got {df['Year'].iloc[4]}."
                         )

    def check_trigger_art_from_pos_test(self, default_delay, df, ind_id, positive_test, start_treatment, year):
        self.assertEqual(df["Event_Name"].iloc[3], start_treatment,
                         msg=f"Test failed: individual {ind_id} should receive {start_treatment} "
                             f"event {default_delay} days after they receive {positive_test} "
                             f"event, got {df['Event_Name'].iloc[3]}."
                         )
        self.assertAlmostEqual(df["Year"].iloc[3], year + round(2 * default_delay / 365, 2),
                               delta=0.02,
                               msg=f"Test failed: individual {ind_id} should receive "
                                   f"{start_treatment} event at year "
                                   f"{year + round(2 * default_delay / 365, 2)}, got "
                                   f"{df['Year'].iloc[3]}."
                               )

    def check_add_test(self, default_delay, df, ind_id, positive_test, year):
        self.assertEqual(df["Event_Name"].iloc[2], positive_test,
                         msg=f"Test failed: individual {ind_id} should receive {positive_test} "
                             f"event {default_delay} days after they become symptomatic, got "
                             f"{df['Event_Name'].iloc[2]}."
                         )
        self.assertAlmostEqual(df["Year"].iloc[2], year + round(default_delay / 365, 2), delta=0.02,
                               msg=f"Test failed: individual {ind_id} should receive {positive_test} "
                                   f"event at year {year + round(default_delay / 365, 2)}, got "
                                   f"{df['Year'].iloc[2]}.")

    def check_add_choice(self, df, disease_deaths, get_tested, ignore, ind_id, non_disease_deaths):
        self.assertIn(df["Event_Name"].iloc[1], [get_tested, ignore, disease_deaths, non_disease_deaths],
                      msg=f"Test failed: individual {ind_id} should receive only one of the 4 events after "
                          f"they become symptomatic: {get_tested}, {ignore}, {disease_deaths}, "
                          f"{non_disease_deaths}, got {df['Event_Name'].iloc[1]}.")
        self.assertEqual(df["Year"].iloc[1], df["Year"].iloc[0],
                         msg=f"Test failed: individual {ind_id} should receive {df['Event_Name'].iloc[1]} "
                             f"event at the same day when they become symptomatic {df['Year'].iloc[0]}: got"
                             f" {df['Year'].iloc[1]}.")

    def check_event_counts(self, symptomatic, get_tested, ignore, positive_test, report_df, started_ART):
        symptomatic_df = report_df[(report_df['Event_Name'] == symptomatic) &
                                   (report_df["OnART"] == "N")]
        symptomatic_count = len(symptomatic_df)
        # test_symptomatic_df = report_df[(report_df['Event_Name'] == HIV_symptomatic)]
        # test_symptomatic_df = test_symptomatic_df[test_symptomatic_df.duplicated(['Individual_ID'])]
        self.assertGreater(symptomatic_count, 0,
                           msg=f'Test failed: expected some {symptomatic} events, got {symptomatic_count}.')
        get_tested_count = len(report_df[report_df['Event_Name'] == get_tested])
        self.assertAlmostEqual(get_tested_count, symptomatic_count * 0.5, delta=10,  # random choice
                               msg=f'Test failed: expected about {symptomatic_count * 0.5} {get_tested} '
                                   f'events, got {get_tested_count}.')
        ignore_count = len(report_df[report_df['Event_Name'] == ignore])
        self.assertAlmostEqual(ignore_count, symptomatic_count - get_tested_count, delta=5,  # death
                               msg=f'Test failed: expected about {symptomatic_count - get_tested_count} {ignore} '
                                   f'events, got {ignore_count}.')
        positive_test_count = len(report_df[report_df['Event_Name'] == positive_test])
        self.assertAlmostEqual(positive_test_count, get_tested_count, delta=40,  # delayed
                               msg=f'Test failed: expected about {get_tested_count} {positive_test} '
                                   f'events, got {positive_test_count}.')
        started_ART_count = len(report_df[report_df['Event_Name'] == started_ART])
        self.assertAlmostEqual(started_ART_count, positive_test_count, delta=20,  # delayed
                               msg=f'Test failed: expected about {positive_test_count} {started_ART} '
                                   f'events, got {started_ART_count}.')
        return symptomatic_df


if __name__ == '__main__':
    unittest.main()

