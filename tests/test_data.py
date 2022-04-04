# -*- coding: utf-8 -*-

"""Tests for data integrity."""

import json
import logging
import unittest
from collections import defaultdict
from textwrap import dedent
from typing import Mapping

import bioregistry
from bioregistry import Resource
from bioregistry.constants import BIOREGISTRY_PATH
from bioregistry.export.prefix_maps import get_obofoundry_prefix_map
from bioregistry.export.rdf_export import resource_to_rdf_str
from bioregistry.license_standardizer import REVERSE_LICENSES
from bioregistry.schema.utils import EMAIL_RE
from bioregistry.utils import _norm, curie_to_str, extended_encoder, is_mismatch

logger = logging.getLogger(__name__)


class TestRegistry(unittest.TestCase):
    """Tests for the registry."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.registry = bioregistry.read_registry()
        self.metaregistry = bioregistry.read_metaregistry()

    def test_lint(self):
        """Test that the lint command was run.

        .. seealso:: https://github.com/biopragmatics/bioregistry/issues/180
        """
        text = BIOREGISTRY_PATH.read_text(encoding="utf8")
        linted_text = json.dumps(
            json.loads(text), indent=2, sort_keys=True, ensure_ascii=False, default=extended_encoder
        )
        self.assertEqual(
            linted_text,
            text,
            msg="""

    There are formatting errors in one of the Bioregistry's JSON data files.
    Please lint these files using the following commands in the console:

    $ pip install tox
    $ tox -e bioregistry-lint
    """,
        )

    def test_prefixes(self):
        """Check prefixes aren't malformed."""
        for prefix, resource in self.registry.items():
            with self.subTest(prefix=prefix):
                self.assertEqual(prefix, resource.prefix)
                self.assertEqual(prefix.lower(), prefix, msg="prefix is not lowercased")
                self.assertFalse(prefix.startswith("_"))
                self.assertFalse(prefix.endswith("_"))

    def test_keys(self):
        """Check the required metadata is there."""
        keys = set(Resource.__fields__.keys())
        with open(BIOREGISTRY_PATH, encoding="utf-8") as file:
            data = json.load(file)
        for prefix, entry in data.items():
            extra = {k for k in set(entry) - keys if not k.startswith("_")}
            if not extra:
                continue
            with self.subTest(prefix=prefix):
                self.fail(f"{prefix} had extra keys: {extra}")

    @staticmethod
    def _construct_substrings(x):
        return (
            f"({x.casefold()})",
            f"{x.casefold()}: ",
            f"{x.casefold()}- ",
            f"{x.casefold()} - ",
            # f"{x.casefold()} ontology",
        )

    def test_names(self):
        """Test that all entries have a name."""
        for prefix, entry in self.registry.items():
            with self.subTest(prefix=prefix):
                name = entry.get_name()
                self.assertIsNotNone(name, msg=f"{prefix} is missing a name")

                for ss in self._construct_substrings(prefix):
                    self.assertNotIn(
                        ss,
                        name.casefold(),
                        msg="Redundant prefix appears in name",
                    )
                preferred_prefix = entry.get_preferred_prefix()
                if preferred_prefix is not None:
                    for ss in self._construct_substrings(preferred_prefix):
                        self.assertNotIn(
                            ss,
                            name.casefold(),
                            msg="Redundant preferred prefix appears in name",
                        )
                for alt_prefix in entry.get_synonyms():
                    for ss in self._construct_substrings(alt_prefix):
                        self.assertNotIn(
                            ss,
                            name.casefold(),
                            msg=f"Redundant alt prefix {alt_prefix} appears in name",
                        )

    def test_name_expansions(self):
        """Test that default names are not capital acronyms."""
        for prefix in self.registry:
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
        for prefix in self.registry:
            if bioregistry.is_deprecated(prefix):
                continue
            with self.subTest(prefix=prefix, name=bioregistry.get_name(prefix)):
                self.assertIsNotNone(bioregistry.get_description(prefix))

    def test_has_homepage(self):
        """Test that all non-deprecated entries have a homepage."""
        for prefix in self.registry:
            if bioregistry.is_deprecated(prefix):
                continue
            with self.subTest(prefix=prefix, name=bioregistry.get_name(prefix)):
                self.assertIsNotNone(bioregistry.get_homepage(prefix))

    def test_homepage_http(self):
        """Test that all homepages start with http."""
        for prefix in self.registry:
            homepage = bioregistry.get_homepage(prefix)
            if homepage is None or homepage.startswith("http") or homepage.startswith("ftp"):
                continue
            with self.subTest(prefix=prefix):
                self.fail(msg=f"malformed homepage: {homepage}")

    def test_email(self):
        """Test that the email getter returns valid email addresses."""
        for prefix in self.registry:
            resource = bioregistry.get_resource(prefix)
            self.assertIsNotNone(resource)
            email = resource.get_contact_email()
            if email is None or EMAIL_RE.match(email):
                continue
            with self.subTest(prefix=prefix):
                self.fail(msg=f"bad email: {email}")

    def test_no_redundant_acronym(self):
        """Test that there is no redundant acronym in the name.

        For example, "Amazon Standard Identification Number (ASIN)" is a problematic
        name for prefix "asin".
        """
        for prefix in self.registry:
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
            uri_format = entry.uri_format
            if not uri_format:
                continue
            with self.subTest(prefix=prefix):
                self.assertIn("$1", uri_format, msg=f"{prefix} format does not have a $1")

    def test_uri_format_uniqueness(self):
        """Test URI format uniqueness."""
        dd = defaultdict(set)
        for prefix, entry in self.registry.items():
            if not entry.uri_format:
                continue
            dd[entry.uri_format].add(prefix)
        for uri_format, prefixes in dd.items():
            with self.subTest(uri_format=uri_format):
                if len(prefixes) == 1:
                    continue
                self.assertEqual(
                    len(prefixes) - 1,
                    sum(
                        bioregistry.get_part_of(prefix) in prefixes
                        or bioregistry.get_has_canonical(prefix) in prefixes
                        for prefix in prefixes
                    ),
                    msg="All prefix clusters of size n with duplicated URI format"
                    " strings should have n-1 of their entries pointing towards"
                    " other entries either via the part_of or has_canonical relations",
                )

    def test_own_terms_conflict(self):
        """Test there is no conflict between no own terms and having an example."""
        for prefix, resource in self.registry.items():
            if bioregistry.has_no_terms(prefix):
                with self.subTest(prefix=prefix):
                    self.assertIsNone(bioregistry.get_example(prefix))
                    self.assertIsNone(resource.uri_format)

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
                self.assertFalse(
                    pattern.casefold().startswith(f"^{prefix.casefold()}:"),
                    msg=f"pattern should represent a local identifier, not a CURIE\n"
                    f"prefix: {prefix}\npattern: {pattern}",
                )

    def test_curie_patterns(self):
        """Test that all examples can validate against the CURIE pattern."""
        for prefix, entry in self.registry.items():
            curie_pattern = bioregistry.get_curie_pattern(prefix)
            lui_example = entry.get_example()
            if curie_pattern is None or lui_example is None:
                continue
            pp = bioregistry.get_preferred_prefix(prefix)
            curie_example = curie_to_str(pp or prefix, lui_example)
            with self.subTest(prefix=prefix):
                self.assertRegex(
                    curie_example,
                    curie_pattern,
                    msg=dedent(
                        f"""
                prefix: {prefix}
                preferred prefix: {pp}
                example LUI: {lui_example}
                example CURIE: {curie_example}
                pattern for LUI: {bioregistry.get_pattern(prefix)}
                pattern for CURIE: {curie_pattern}
                """
                    ),
                )

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
                self.assertEqual(entry.standardize_identifier(example), example)

                pattern = entry.get_pattern_re()
                if pattern is not None:
                    self.assert_canonical(prefix, example)

    def assert_canonical(self, prefix: str, example: str) -> None:
        """Assert the identifier is canonical."""
        entry = self.registry[prefix]
        canonical = entry.is_canonical_identifier(example)
        self.assertTrue(canonical is None or canonical, msg=f"Failed on prefix={prefix}")

    def test_extra_examples(self):
        """Test extra examples."""
        for prefix, entry in self.registry.items():
            if not entry.example_extras:
                continue
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(
                    entry.get_example(), msg="entry has extra examples but not primary example"
                )

            for example in entry.example_extras:
                with self.subTest(prefix=prefix, identifier=example):
                    self.assertEqual(entry.standardize_identifier(example), example)
                    self.assert_canonical(prefix, example)

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

    def test_banana(self):
        """Tests for bananas."""
        # Simple scenario
        self.assertIsNone(bioregistry.get_banana("pdb"))

        # OBO Foundry scenario where there should not be a banana
        self.assertIsNone(
            bioregistry.get_banana("ncit"),
            msg="Even though this is OBO foundry, it should not have a banana.",
        )
        self.assertIsNone(
            bioregistry.get_banana("ncbitaxon"),
            msg="Even though this is OBO foundry, it should not have a banana.",
        )

    def test_get_nope(self):
        """Test when functions don't return."""
        self.assertIsNone(bioregistry.get_banana("nope"))
        self.assertIsNone(bioregistry.get_description("nope"))
        self.assertIsNone(bioregistry.get_homepage("nope"))
        self.assertIsNone(bioregistry.get_uri_format("gmelin"))  # no URL
        self.assertIsNone(bioregistry.get_uri_format("nope"))
        self.assertIsNone(bioregistry.get_version("nope"))
        self.assertIsNone(bioregistry.get_name("nope"))
        self.assertIsNone(bioregistry.get_example("nope"))
        self.assertIsNone(bioregistry.get_contact_email("nope"))
        self.assertIsNone(bioregistry.get_mappings("nope"))
        self.assertIsNone(bioregistry.get_fairsharing_prefix("nope"))
        self.assertIsNone(bioregistry.get_obofoundry_prefix("nope"))
        self.assertIsNone(bioregistry.get_obofoundry_uri_prefix("nope"))
        self.assertIsNone(bioregistry.get_obo_download("nope"))
        self.assertIsNone(bioregistry.get_owl_download("nope"))
        self.assertIsNone(bioregistry.get_ols_iri("nope", ...))
        self.assertIsNone(bioregistry.get_obofoundry_iri("nope", ...))
        self.assertFalse(bioregistry.is_deprecated("nope"))
        self.assertIsNone(bioregistry.get_provides_for("nope"))
        self.assertIsNone(bioregistry.get_version("gmelin"))
        self.assertIsNone(bioregistry.is_known_identifier("nope", ...))
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
        self.assertIsNone(bioregistry.get_obofoundry_uri_prefix("dbsnp"))

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
                prefix_map = bioregistry.get_prefix_map(priority=priority)
                self.assertIsNotNone(prefix_map)

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
                self.assertFalse(uri_prefix.startswith("https://identifiers.org"), msg=uri_prefix)
                self.assertFalse(uri_prefix.startswith("http://identifiers.org"), msg=uri_prefix)

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
            if not resource.get_namespace_in_lui():
                continue
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(
                    resource.get_banana(),
                    msg=f"If there is a namespace in LUI annotation,"
                    f" then there must be a banana\nregex: {resource.get_pattern()}",
                )

    def test_licenses(self):
        """Check license keys don't end with trailing slashes."""
        for key, values in REVERSE_LICENSES.items():
            with self.subTest(key=key):
                self.assertEqual(len(values), len(set(values)), msg=f"duplicates in {key}")

    def test_contributors(self):
        """Check contributors have minimal metadata."""
        for prefix, resource in self.registry.items():
            with self.subTest(prefix=prefix):
                if not resource.contributor and not resource.contributor_extras:
                    self.assertNotEqual(0, len(resource.get_mappings()))
                    continue
                if resource.contributor is not None:
                    self.assertIsNotNone(resource.contributor.name)
                    self.assertIsNotNone(resource.contributor.orcid)
                    self.assertIsNotNone(resource.contributor.github)
                for contributor in resource.contributor_extras or []:
                    self.assertIsNotNone(contributor.name)
                    self.assertIsNotNone(contributor.orcid)
                    self.assertIsNotNone(contributor.github)

    def test_reviewers(self):
        """Check reviewers have minimal metadata."""
        for prefix, resource in self.registry.items():
            if not resource.reviewer:
                continue
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(resource.reviewer.name)
                self.assertIsNotNone(resource.reviewer.orcid)
                self.assertIsNotNone(resource.reviewer.github)

    def test_contacts(self):
        """Check contacts have minimal metadata."""
        for prefix, resource in self.registry.items():
            if not resource.contact:
                continue
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(
                    resource.contact.name, msg=f"Contact for {prefix} is missing a label"
                )
                self.assertIsNotNone(
                    resource.contact.email, msg=f"Contact for {prefix} is missing an email"
                )

    def test_wikidata(self):
        """Check wikidata prefixes are written properly."""
        allowed = {
            "database",
            "prefix",
            "pattern",
            "paper",
            "homepage",
            "name",
            "uri_format",
            "database.label",
            "format.rdf",
            "database.homepage",
        }
        for prefix, resource in self.registry.items():
            if not resource.wikidata:
                continue
            with self.subTest(prefix=prefix):
                unexpected_keys = set(resource.wikidata) - allowed
                self.assertFalse(
                    unexpected_keys, msg=f"Unexpected keys in wikidata entry: {unexpected_keys}"
                )
                database = resource.wikidata.get("database")
                self.assertTrue(
                    database is None or database.startswith("Q"),
                    msg=f"Wikidata database for {prefix} is malformed: {database}",
                )

                wikidata_property = resource.wikidata.get("prefix")
                self.assertTrue(
                    wikidata_property is None or wikidata_property.startswith("P"),
                    msg=f"Wikidata property for {prefix} is malformed: {wikidata_property}",
                )

    def test_wikidata_wrong_place(self):
        """Test that wikidata annotations aren't accidentally placed in the wrong place."""
        registry_raw = json.loads(BIOREGISTRY_PATH.read_text(encoding="utf8"))
        metaprefixes = set(self.metaregistry)
        for prefix, resource in registry_raw.items():
            external_m = {
                metaprefix: resource[metaprefix]
                for metaprefix in metaprefixes
                if metaprefix in resource
            }
            if not external_m:
                continue
            with self.subTest(prefix=prefix):
                for metaprefix, external in external_m.items():
                    self.assertNotIn(
                        "wikidata",
                        external,
                        msg=f"""

    A "wikidata" key appeared in [{prefix}] inside external metadata for "{metaprefix}".
    Please move this key to its own top-level entry within the [{prefix}] record.
                        """,
                    )

    def test_mismatches(self):
        """Test mismatches all use canonical prefixes."""
        for prefix in bioregistry.read_mismatches():
            with self.subTest(prefix=prefix):
                self.assertTrue(
                    prefix in set(self.registry),
                    msg=f"mismatches.json has invalid prefix: {prefix}",
                )
