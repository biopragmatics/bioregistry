"""Test the integrity of the usages annotations."""

import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).parent.resolve()
ROOT = HERE.parent.resolve()
USAGES_PATH = ROOT.joinpath("docs", "_data", "usages.yml")


class TestUsages(unittest.TestCase):
    """Test the integrity of the usages annotations."""

    def test_usages(self):
        """Test the integrity of the usages annotations."""
        data = yaml.safe_load(USAGES_PATH.read_text())
        self.assertIsNotNone(data)
        for record in data:
            self.assertIn("name", record)
            name = record["name"]
            with self.subTest(name=name):
                self.assertIn("homepage", record)
                self.assertIsInstance(record["homepage"], str)
                self.assertIn("type", record)
                self.assertIn(record["type"], {"organization", "project", "package", "analysis"})
                self.assertIn("uses", record)
                for use in record["uses"]:
                    self.assertIn("description", use)
