"""Test alignment."""

import unittest
from typing import Any

from bioregistry import Manager, Resource
from bioregistry.external.alignment_utils import Aligner


class TestAlign(unittest.TestCase):
    """Test align."""

    def test_already_mapped(self) -> None:
        """Test alignment when there's already a mapping, but the data needs to get backfilled."""

        def mock_getter(
            force_download: bool = False, force_process: bool = False
        ) -> dict[str, dict[str, Any]]:
            return {
                "FAIRsharing.Z8OKi5": {
                    "name": "ABCD database",
                }
            }

        class MockAligner(Aligner):
            key = "fairsharing"
            getter = mock_getter
            curation_header = ()

        resource = Resource(prefix="abcd", mappings={"fairsharing": "FAIRsharing.Z8OKi5"})
        registry = {"abcd": resource}
        manager = Manager(registry=registry)
        aligner = MockAligner(manager=manager, force_download=False, force_process=True)
        self.assertEqual({"FAIRsharing.Z8OKi5": "abcd"}, aligner.external_id_to_bioregistry_id)

        self.assertIsNotNone(resource.fairsharing)
        self.assertEqual("ABCD database", resource.fairsharing.get("name"))

    def test_cross_mapped(self) -> None:
        """Test when there are cross-conflicts."""

        def mock_getter(
            force_download: bool = False, force_process: bool = False
        ) -> dict[str, dict[str, Any]]:
            return {"geo": {"name": "geographical entity ontology", "preferred_prefix": "GEO"}}

        class MockAligner(Aligner):
            key = "obofoundry"
            getter = mock_getter
            curation_header = ()

        geo = Resource(prefix="geo", name="gene expression omnibus")
        geogeo = Resource(
            prefix="geogeo", name="geographical entity ontology", mappings={"obofoundry": "geo"}
        )
        registry = {"geo": geo, "geogeo": geogeo}
        manager = Manager(registry=registry)
        aligner = MockAligner(manager=manager, force_download=False, force_process=True)
        self.assertEqual({"geo": "geogeo"}, aligner.external_id_to_bioregistry_id)

        self.assertIsNone(geo.obofoundry)
        self.assertIsNotNone(geogeo.obofoundry)
        self.assertEqual("geo", geogeo.obofoundry.get("prefix"))
