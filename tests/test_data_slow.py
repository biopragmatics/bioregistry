"""Slow test cases."""

import unittest
from collections import defaultdict

import pytest

import bioregistry


class TestDataSlow(unittest.TestCase):
    """Slow tests."""

    @pytest.mark.slow
    def test_parse_http_vs_https(self):
        """Test parsing both HTTP and HTTPS, even when the provider is only set to one."""
        prefix = "neuronames"
        ex = bioregistry.get_example(prefix)
        with self.subTest(protocol="http"):
            a = f"http://braininfo.rprc.washington.edu/centraldirectory.aspx?ID={ex}"
            self.assertEqual((prefix, ex), bioregistry.parse_iri(a))
        with self.subTest(protocol="https"):
            b = f"https://braininfo.rprc.washington.edu/centraldirectory.aspx?ID={ex}"
            self.assertEqual((prefix, ex), bioregistry.parse_iri(b))

    @pytest.mark.slow
    def test_prefix_map_priorities(self):
        """Test that different lead priorities all work for prefix map generation."""
        priorities = [
            "default",
            "miriam",
            "ols",
            "obofoundry",
            "n2t",
            "prefixcommons",
            # "bioportal",
        ]
        for lead in priorities:
            priority = [lead, *(x for x in priorities if x != lead)]
            with self.subTest(priority=",".join(priority)):
                prefix_map = bioregistry.get_prefix_map(uri_prefix_priority=priority)
                self.assertIsNotNone(prefix_map)

    @pytest.mark.slow
    def test_unique_iris(self):
        """Test that all IRIs are unique, or at least there's a mapping to which one is the preferred prefix."""
        # TODO make sure there are also no HTTP vs HTTPS clashes,
        #  for example if one prefix has http://example.org/foo/$1 and a different one
        #  has https://example.org/foo/$1
        prefix_map = bioregistry.get_prefix_map()
        dd = defaultdict(dict)
        for prefix, iri in prefix_map.items():
            resource = bioregistry.get_resource(prefix)
            self.assertIsNotNone(resource)
            if resource.provides is not None:
                # Don't consider resources that are providing, such as `ctd.gene`
                continue
            dd[iri][prefix] = resource

        x = {}
        for iri, resources in dd.items():
            if 1 == len(resources):
                # This is a unique IRI, so no issues
                continue

            # Get parts
            parts = {prefix: resource.part_of for prefix, resource in resources.items()}
            unmapped = [prefix for prefix, part_of in parts.items() if part_of is None]
            if len(unmapped) <= 1:
                continue

            # Get canonical
            canonicals = {prefix: resource.has_canonical for prefix, resource in resources.items()}
            canonical_target = [prefix for prefix, target in canonicals.items() if target is None]
            all_targets = list(
                {target for prefix, target in canonicals.items() if target is not None}
            )
            if (
                len(canonical_target) == 1
                and len(all_targets) == 1
                and canonical_target[0] == all_targets[0]
            ):
                continue

            x[iri] = parts, unmapped, canonical_target, all_targets
        self.assertEqual({}, x)
