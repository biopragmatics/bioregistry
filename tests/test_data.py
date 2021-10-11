# -*- coding: utf-8 -*-

"""Tests for data integrity."""

import logging
import unittest
from collections import defaultdict
from typing import Mapping

import bioregistry
from bioregistry.export.prefix_maps import get_obofoundry_prefix_map
from bioregistry.export.rdf_export import resource_to_rdf_str
from bioregistry.schema.utils import EMAIL_RE
from bioregistry.utils import _norm, is_mismatch

logger = logging.getLogger(__name__)


class TestRegistry(unittest.TestCase):
    """Tests for the registry."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.registry = bioregistry.read_registry()
        self.metaregistry = bioregistry.read_metaregistry()

    def test_keys(self):
        """Check the required metadata is there."""
        keys = {
            # Required
            "description",
            "homepage",
            "name",
            # Recommended
            "contact",
            "download_obo",
            "download_owl",
            "example",
            "pattern",
            "type",
            "url",
            # Only there if true
            "no_own_terms",
            "not_available_as_obo",
            "namespaceEmbeddedInLui",
            # Only there if false
            # Lists
            "appears_in",
            # Other
            "deprecated",
            "banana",
            "mappings",
            "ols_version_date_format",
            "ols_version_prefix",
            "ols_version_suffix_split",
            "ols_version_type",
            "part_of",
            "provides",
            "references",
            "synonyms",
            "comment",
            "contributor",
            "reviewer",
            "proprietary",
            "has_canonical",
            "preferred_prefix",
            "providers",
        }
        keys.update(bioregistry.read_metaregistry())
        for prefix, entry in self.registry.items():
            extra = {k for k in set(entry.dict()) - keys if not k.startswith("_")}
            if not extra:
                continue
            with self.subTest(prefix=prefix):
                self.fail(f"had extra keys: {extra}")

    def test_names(self):
        """Test that all entries have a name."""
        for prefix, entry in self.registry.items():
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(entry.get_name(), msg=f"{prefix} is missing a name")

    def test_name_expansions(self):
        """Test that default names are not capital acronyms."""
        for prefix in bioregistry.read_registry():
            if bioregistry.is_deprecated(prefix):
                continue
            entry = bioregistry.get_resource(prefix)
            if entry.name:
                continue
            name = bioregistry.get_name(prefix)
            if prefix == name.lower() and name.upper() == name:
                with self.subTest(prefix=prefix):
                    self.fail(msg=f"{prefix} acronym ({name}) is not expanded")

            if "." in prefix and prefix.split(".")[0] == name.lower():
                with self.subTest(prefix=prefix):
                    self.fail(msg=f"{prefix} acronym ({name}) is not expanded")

    def test_has_description(self):
        """Test that all non-deprecated entries have a description."""
        for prefix in bioregistry.read_registry():
            if bioregistry.is_deprecated(prefix):
                continue
            with self.subTest(prefix=prefix, name=bioregistry.get_name(prefix)):
                self.assertIsNotNone(bioregistry.get_description(prefix))

    def test_has_homepage(self):
        """Test that all non-deprecated entries have a homepage."""
        for prefix in bioregistry.read_registry():
            if bioregistry.is_deprecated(prefix):
                continue
            with self.subTest(prefix=prefix, name=bioregistry.get_name(prefix)):
                self.assertIsNotNone(bioregistry.get_homepage(prefix))

    def test_homepage_http(self):
        """Test that all homepages start with http."""
        for prefix in bioregistry.read_registry():
            homepage = bioregistry.get_homepage(prefix)
            if homepage is None or homepage.startswith("http") or homepage.startswith("ftp"):
                continue
            with self.subTest(prefix=prefix):
                self.fail(msg=f"malformed homepage: {homepage}")

    def test_email(self):
        """Test that the email getter returns valid email addresses."""
        for prefix in bioregistry.read_registry():
            if prefix in {"ato", "bootstrep", "dc_cl"}:
                # FIXME these are known problematic, and there's a PR on
                #  https://github.com/OBOFoundry/OBOFoundry.github.io/pull/1534
                continue
            resource = bioregistry.get_resource(prefix)
            self.assertIsNotNone(resource)
            email = resource.get_prefix_key("contact", ("obofoundry", "ols"))
            if email is None or EMAIL_RE.match(email):
                continue
            with self.subTest(prefix=prefix):
                self.fail(msg=f"bad email: {email}")

    def test_no_redundant_acronym(self):
        """Test that there is no redundant acronym in the name.

        For example, "Amazon Standard Identification Number (ASIN)" is a problematic
        name for prefix "asin".
        """
        for prefix in bioregistry.read_registry():
            if bioregistry.is_deprecated(prefix):
                continue
            entry = bioregistry.get_resource(prefix)
            if "name" in entry:
                continue
            name = bioregistry.get_name(prefix)

            try:
                _, rest = name.rstrip(")").rsplit("(", 1)
            except ValueError:
                continue
            if rest.lower() == prefix.lower():
                with self.subTest(prefix=prefix):
                    self.fail(msg=f'{prefix} has redundant acronym in name "{name}"')

    def test_format_urls(self):
        """Test that entries with a format URL are formatted right (yo dawg)."""
        for prefix, entry in self.registry.items():
            url = entry.url
            if not url:
                continue
            with self.subTest(prefix=prefix):
                self.assertIn("$1", url, msg=f"{prefix} format does not have a $1")

    def test_own_terms_conflict(self):
        """Test there is no conflict between no own terms and having an example."""
        for prefix, resource in self.registry.items():
            if bioregistry.has_no_terms(prefix):
                with self.subTest(prefix=prefix):
                    self.assertIsNone(bioregistry.get_example(prefix))
                    self.assertIsNone(resource.url)

    def test_patterns(self):
        """Test that all prefixes are norm-unique."""
        for prefix, entry in self.registry.items():
            pattern = entry.get_pattern()
            if pattern is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertTrue(
                    pattern.startswith("^"), msg=f"{prefix} pattern {pattern} should start with ^"
                )
                self.assertTrue(
                    pattern.endswith("$"), msg=f"{prefix} pattern {pattern} should end with $"
                )
                # TODO after it's time for curation, activate this test
                # self.assertFalse(
                #     pattern.casefold().startswith(f"^{prefix.casefold()}"),
                #     msg=f"pattern should represent a local identifier,
                #     not a CURIE\nprefix: {prefix}\npattern: {pattern}",
                # )

    def test_examples(self):
        """Test examples for the required conditions.

        1. All resources must have an example, with the following exceptions:
           - deprecated resources
           - resources that are marked as not having their own terms (e.g., ChIRO)
           - resources that are providers for other resources (e.g., CTD Gene)
           - proprietary resources (e.g., Eurofir)
        2. Examples are stored in normal form (i.e., no redundant prefixes)
        3. Examples pass the regular expression pattern for the resource, if available
        """
        for prefix, entry in self.registry.items():
            if (
                bioregistry.has_no_terms(prefix)
                or bioregistry.is_deprecated(prefix)
                or bioregistry.get_provides_for(prefix)
                or bioregistry.is_proprietary(prefix)
            ):
                continue
            if prefix in {
                "obo",
                "pspub",
                "unpd",
                "span",
            }:  # FIXME the minting of this prefix for PyOBO needs to be reinvestigated
                continue
            with self.subTest(prefix=prefix, name=bioregistry.get_name(prefix)):
                msg = f"{prefix} is missing an example local identifier"
                if entry.ols:
                    msg += (
                        f'\nSee: https://www.ebi.ac.uk/ols/ontologies/{entry.ols["prefix"]}/terms'
                    )
                example = entry.get_example()
                self.assertIsNotNone(example, msg=msg)
                self.assertEqual(entry.clean_identifier(example), example)

                pattern = entry.get_pattern_re()
                if pattern is not None:
                    # TODO update all regexes to actually match LOCAL identifiers, not CURIEs
                    if not bioregistry.validate(prefix, example):
                        self.assertRegex(example, pattern, msg=f"Failed on prefix={prefix}")

    def test_is_mismatch(self):
        """Check for mismatches."""
        self.assertTrue(is_mismatch("geo", "ols", "geo"))
        self.assertFalse(is_mismatch("geo", "miriam", "geo"))

    def test_own_terms(self):
        """Test own terms."""
        self.assertFalse(bioregistry.has_no_terms("chebi"), msg="ChEBI should be marked as false")
        self.assertTrue(bioregistry.has_no_terms("chiro"), msg="CHIRO has no terms")
        self.assertFalse(
            bioregistry.has_no_terms("nope"), msg="Missing prefix should be false by definition"
        )

    def test_get_nope(self):
        """Test when functions don't return."""
        self.assertIsNone(bioregistry.get_banana("nope"))
        self.assertIsNone(bioregistry.get_description("nope"))
        self.assertIsNone(bioregistry.get_homepage("nope"))
        self.assertIsNone(bioregistry.get_format("gmelin"))  # no URL
        self.assertIsNone(bioregistry.get_format("nope"))
        self.assertIsNone(bioregistry.get_version("nope"))
        self.assertIsNone(bioregistry.get_name("nope"))
        self.assertIsNone(bioregistry.get_example("nope"))
        self.assertIsNone(bioregistry.get_email("nope"))
        self.assertIsNone(bioregistry.get_mappings("nope"))
        self.assertIsNone(bioregistry.get_fairsharing_prefix("nope"))
        self.assertIsNone(bioregistry.get_obofoundry_prefix("nope"))
        self.assertIsNone(bioregistry.get_obofoundry_format("nope"))
        self.assertIsNone(bioregistry.get_obo_download("nope"))
        self.assertIsNone(bioregistry.get_owl_download("nope"))
        self.assertIsNone(bioregistry.get_ols_iri("nope", ...))
        self.assertIsNone(bioregistry.get_obofoundry_iri("nope", ...))
        self.assertFalse(bioregistry.is_deprecated("nope"))
        self.assertIsNone(bioregistry.get_provides_for("nope"))
        self.assertIsNone(bioregistry.get_version("gmelin"))
        self.assertIsNone(bioregistry.validate("nope", ...))
        self.assertIsNone(bioregistry.get_default_iri("nope", ...))
        self.assertIsNone(bioregistry.get_identifiers_org_iri("nope", ...))
        self.assertIsNone(bioregistry.get_n2t_iri("nope", ...))
        self.assertIsNone(bioregistry.get_bioportal_iri("nope", ...))
        self.assertIsNone(bioregistry.get_bioportal_iri("gmelin", ...))
        self.assertIsNone(bioregistry.get_identifiers_org_iri("nope", ...))
        self.assertIsNone(bioregistry.get_identifiers_org_iri("pid.pathway", ...))
        self.assertIsNone(bioregistry.get_identifiers_org_iri("gmelin", ...))
        self.assertIsNone(bioregistry.get_iri("gmelin", ...))

    def test_get(self):
        """Test getting resources."""
        self.assertIsInstance(bioregistry.get_description("chebi"), str)

        # No OBO Foundry format for dbSNP b/c not in OBO Foundry (and probably never will be)
        self.assertIsNone(bioregistry.get_obofoundry_format("dbsnp"))

        self.assertEqual("FAIRsharing.mya1ff", bioregistry.get_fairsharing_prefix("ega.dataset"))

        self.assertEqual(
            "https://meshb.nlm.nih.gov/record/ui?ui=D010146",
            bioregistry.get_iri("mesh", "D010146"),
        )

    def test_get_rdf(self):
        """Test conversion to RDF."""
        s = resource_to_rdf_str("chebi")
        self.assertIsInstance(s, str)

    @unittest.skip(
        """\
        Not sure if this test makes sense - some of the resources, like
        datanator_gene and datanator_metabolite are part of a larger resources,
        but have their own well-defined endpoints.
        """
    )
    def test_parts(self):
        """Make sure all part of relations point to valid prefixes."""
        for prefix, resource in self.registry.items():
            if bioregistry.is_deprecated(prefix) or bioregistry.get_provides_for(prefix):
                continue
            if resource.part_of is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertIn(
                    resource.part_of, self.registry, msg="super-resource is not a valid prefix"
                )

    def test_provides(self):
        """Make sure all provides relations point to valid prefixes."""
        for prefix, resource in self.registry.items():
            if resource.provides is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertIn(resource.provides, self.registry)

    def test_has_canonical(self):
        """Make sure all has_canonical relations point to valid prefixes."""
        for prefix, resource in self.registry.items():
            if resource.has_canonical is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertIn(resource.has_canonical, self.registry)

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

    def test_default_prefix_map_no_miriam(self):
        """Test no identifiers.org URI prefixes get put in the prefix map."""
        self.assert_no_idot(bioregistry.get_prefix_map())
        # self.assert_no_idot(bioregistry.get_prefix_map(include_synonyms=True))

    def test_obo_prefix_map(self):
        """Test the integrity of the OBO prefix map."""
        obofoundry_prefix_map = get_obofoundry_prefix_map()
        self.assert_no_idot(obofoundry_prefix_map)
        self.assertIn("FlyBase", set(obofoundry_prefix_map))

        self.assert_no_idot(get_obofoundry_prefix_map(include_synonyms=True))

    def assert_no_idot(self, prefix_map: Mapping[str, str]) -> None:
        """Assert none of the URI prefixes have identifiers.org in them."""
        for prefix, uri_prefix in prefix_map.items():
            if prefix in {"idoo", "miriam.collection", "mir", "identifiers.namespace"}:
                # allow identifiers.org namespaces since this actually should be here
                continue
            with self.subTest(prefix=prefix):
                self.assertNotIn("identifiers.org", uri_prefix, msg=uri_prefix)

    def test_preferred_prefix(self):
        """Test the preferred prefix matches the normalized prefix."""
        for prefix, resource in self.registry.items():
            if bioregistry.is_deprecated(prefix):
                continue
            pp = resource.get_preferred_prefix()
            if pp is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertEqual(prefix.replace(".", ""), _norm(pp))
                # TODO consider later if preferred prefix should
                #  explicitly not be mentioned in synonyms
                # self.assertNotIn(pp, resource.get_synonyms())

    def test_mappings(self):
        """Make sure all mapping keys are valid metaprefixes."""
        for prefix, resource in self.registry.items():
            if not resource.mappings:
                continue
            with self.subTest(prefix=prefix):
                for metaprefix in resource.mappings:
                    self.assertIn(metaprefix, self.metaregistry)

    def test_provider_codes(self):
        """Make sure provider codes are unique."""
        for prefix, resource in self.registry.items():
            if not resource.providers:
                continue
            with self.subTest(prefix=prefix):
                for provider in resource.providers:
                    self.assertNotEqual(provider.code, prefix)
                    self.assertNotIn(provider.code, resource.get_mappings())
                    self.assertNotIn(provider.code, {"custom", "default"})

    def test_namespace_in_lui(self):
        """Test having the namespace in LUI requires a banana annotation.

        This is required because the annotation from MIRIAM is simply not granular enough
        to support actual use cases.
        """
        for prefix, resource in self.registry.items():
            if not resource.namespace_in_lui():
                continue
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(
                    resource.get_banana(),
                    msg=f"If there is a namespace in LUI annotation,"
                    f" then there must be a banana\nregex: {resource.get_pattern()}",
                )
