"""Test importing a resource from a LinkML configuration."""

import unittest

import bioregistry
from bioregistry.curation.add_linkml import get_resource_from_linkml


class TestImportLinkML(unittest.TestCase):
    """Test importing a resource from a LinkML configuration."""

    def test_catcore(self) -> None:
        """Test getting CatCore."""
        url = "https://github.com/HendrikBorgelt/CatCore/raw/refs/heads/main/src/catcore/schema/catcore.yaml"
        resource = bioregistry.Resource(
            prefix="catcore",
            name="CatCore Metadata Reference Model",
            description="The CatCore describes the minimum information which must be reported with research data concerning the field of catalysis. This guideline helps to handle and standardize data based on the FAIR principle (Findable, Accessible, Interoperable, Reusable).",
            license="CC-BY-4.0",
            version="1.0.0",
            uri_format="https://w3id.org/nfdi4cat/catcore/$1",
            example="CatCoreEntity",
            # TODO add depends_on from the `prefixes` list?
        )
        self.assertEqual(
            resource.model_dump(exclude_unset=True, exclude_none=True),
            get_resource_from_linkml(url).model_dump(exclude_unset=True, exclude_none=True),
        )
