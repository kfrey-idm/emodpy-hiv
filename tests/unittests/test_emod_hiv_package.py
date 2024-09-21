import emod_hiv.bootstrap as dtk

import os
import unittest
from pathlib import Path
import sys

parent = Path(__file__).resolve().parent
sys.path.append(str(parent))
import manifest


class TestDownloadFromPackage(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        manifest.delete_existing_file(manifest.eradication_path)
        manifest.delete_existing_file(manifest.schema_path)
        dtk.setup(manifest.package_folder)
        pass

    def test_eradication(self):
        target_path = manifest.eradication_path
        self.assertTrue(os.path.exists(target_path), msg=f"Failed to get {target_path}")

    def test_schema(self):
        target_path = manifest.schema_path
        self.assertTrue(os.path.exists(target_path), msg=f"Failed to get {target_path}")


if __name__ == '__main__':
    unittest.main()
