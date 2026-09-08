"""Test licenses are standardized to SPDX."""

import importlib.util
import unittest

from bioregistry.license_standardizer import NONSTANDARD, REVERSE_LICENSES, get_spdx_ids


class TestLicenses(unittest.TestCase):
    """Test licenses are standardized to SPDX."""

    @unittest.skipUnless(importlib.util.find_spec("pyobo"), "PyOBO is needed for SPDX test")
    def test_licenses(self) -> None:
        """Test licenses are SPDX-compliant."""
        spdx_ids = get_spdx_ids()
        for key in REVERSE_LICENSES:
            if key is None or key in NONSTANDARD:
                continue
            with self.subTest(key=key):
                self.assertIn(key, spdx_ids)
