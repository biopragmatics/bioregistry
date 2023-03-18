"""Test the integrity of the usages annotations.

Use ``npx prettier --write _data/usages.yml``
"""

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
                msg = f"\n\nSee {record['homepage']}"
                self.assertTrue("wikidata" in record or "repository" in record, msg=msg)
                self.assertIn("type", record, msg=msg)
                self.assertIn(
                    record["type"], {"organization", "project", "package", "analysis"}, msg=msg
                )
                self.assertIn("uses", record, msg=msg)
                for use in record["uses"]:
                    self.assertIn("description", use, msg=msg)
