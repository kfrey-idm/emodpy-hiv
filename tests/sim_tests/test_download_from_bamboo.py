import os
import shutil
import unittest
from pathlib import Path
import sys
from abc import ABC, abstractmethod

from emodpy.utils import download_latest_schema, download_latest_eradication, \
    download_latest_reporters, EradicationBambooBuilds, bamboo_api_login, download_from_url
from emodpy.bamboo import get_model_files

parent = Path(__file__).resolve().parent
sys.path.append(parent)
import manifest, manifest2


class TestBambooDownload(unittest.TestCase, ABC):
    """
        Base test class to test bamboo features in emodpy.utils
    """
    @abstractmethod
    def define_test_environment(self):
        self.plan = EradicationBambooBuilds.HIV_LINUX
        self.eradication_path = manifest.eradication_path
        self.schema_path = manifest.schema_file
        self.reporter_path = manifest.plugins_folder
        self.plugins = ['lib_kml_demo_reporter.so',
                        'libcustomreport_HIV_WHO2015.so',
                        'libreportpluginbasic.so',
                        'libstirelationshipqueuereporter.so']

    def setUp(self) -> None:
        self.define_test_environment()
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName
        print(self.case_name)
        print('login to bamboo...')
        bamboo_api_login()

    def get_eradication_test(self):
        if self.eradication_path.is_file():
            self.eradication_path.unlink()
        download_latest_eradication(
            plan=self.plan, scheduled_builds_only=False, out_path=str(self.eradication_path)
        )
        self.assertTrue(self.eradication_path.is_file(), msg=f'{self.eradication_path} does not exist.')

    def get_schema_test(self):
        if self.schema_path.is_file():
            self.schema_path.unlink()
        download_latest_schema(
            plan=self.plan, scheduled_builds_only=False, out_path=str(self.schema_path)
        )
        self.assertTrue(self.schema_path.is_file(), msg=f'{self.schema_path} does not exist.')

    def get_reporter_test(self):
        shutil.rmtree(self.reporter_path, ignore_errors=True)
        download_latest_reporters(
            plan=self.plan, scheduled_builds_only=False, out_path=str(self.reporter_path)
        )
        reporter_files = os.listdir(self.reporter_path)
        self.assertTrue(len(reporter_files) > 0, msg=f'{self.reporter_path} is empty.')
        for file in self.plugins:
            self.assertIn(file, reporter_files, msg=f"{file} does not exist.")
            reporter_files.remove(file)
        if reporter_files:
            print(f"Warning: extra reporter plugins are downloaded: {reporter_files}.")


class TestBambooDownloadWin(TestBambooDownload):
    """
    Tested with Windows version of HIV bamboo plan
    """
    def define_test_environment(self):
        self.plan = EradicationBambooBuilds.HIV_WIN
        self.eradication_path = manifest.eradication_path_win
        self.schema_path = manifest.schema_path_win
        self.reporter_path = manifest.plugins_folder_win
        self.plugins = ['lib_kml_demo_reporter.dll',
                        'libcustomreport_HIV_WHO2015.dll',
                        'libreportpluginbasic.dll',
                        'libstirelationshipqueuereporter.dll']

    def test_bamboo_download_eradication_gen_win(self):
        super().get_eradication_test()

    def test_bamboo_download_schema_gen_win(self):
        super().get_schema_test()

    def test_bamboo_download_reporter_gen_win(self):
        super().get_reporter_test()


class TestBambooDownloadLinux(TestBambooDownload):
    """
    Tested with Linux version of HIV bamboo plan
    """
    def define_test_environment(self):
        super().define_test_environment()
        from enum import Enum

        class MyEradicationBambooBuilds(Enum):  # EradicationBambooBuilds
            HIV_LINUX = "DTKHIVONGOING-SCONSRELLNXSFT"

        self.plan = MyEradicationBambooBuilds.HIV_LINUX

    def test_bamboo_download_eradication_gen_linux(self):
        super().get_eradication_test()

    def test_bamboo_download_schema_gen_linux(self):
        super().get_schema_test()

    def test_bamboo_download_reporter_gen_linux(self):
        super().get_reporter_test()

    def test_bamboo_download_get_model_files(self):

        shutil.rmtree(manifest2.eradication_path, ignore_errors=True)
        shutil.rmtree(manifest2.schema_file, ignore_errors=True)
        shutil.rmtree(manifest2.plugins_folder, ignore_errors=True)

        get_model_files(
            plan=self.plan, manifest=manifest2, scheduled_builds_only=False
        )

        # Make sure eradication is downloaded
        self.assertTrue(os.path.isfile(manifest2.eradication_path), msg=f'{manifest2.eradication_path} does not exist.')

        # Make sure schema file is downloaded
        self.assertTrue(os.path.isfile(manifest2.schema_file), msg=f'{manifest2.schema_file} does not exist.')

        # Make sure reporter plugins are downloaded
        reporter_files = os.listdir(manifest2.plugins_folder)
        self.assertTrue(len(reporter_files) > 0, msg=f'{manifest2.plugins_folder} is empty.')
        for file in self.plugins:
            self.assertIn(file, reporter_files, msg=f"{file} does not exist.")
            reporter_files.remove(file)
        if reporter_files:
            print(f"Warning: extra reporter plugins are downloaded: {reporter_files}.")


if __name__ == '__main__':
    unittest.main()

