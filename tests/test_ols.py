"""Tests for the OLS."""

import json
import unittest

from bioregistry.external.ols import OLS_PROCESSING, VersionType


class TestOLS(unittest.TestCase):
    """Tests for the OLS."""

    def test_version_types(self):
        """Test all processing configurations have valid version types."""
        data = json.loads(OLS_PROCESSING.read_text())
        for entry in data["configurations"]:
            prefix = entry["prefix"]
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(getattr(VersionType, entry["version_type"]))
