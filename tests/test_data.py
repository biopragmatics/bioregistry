# -*- coding: utf-8 -*-

"""Tests for data integrity."""

import json
import logging
import unittest
from collections import defaultdict
from textwrap import dedent
from typing import Mapping

import curies

import bioregistry
from bioregistry import Resource, manager
from bioregistry.constants import BIOREGISTRY_PATH, EMAIL_RE
from bioregistry.export.rdf_export import resource_to_rdf_str
from bioregistry.license_standardizer import REVERSE_LICENSES, standardize_license
from bioregistry.resolve import get_obo_context_prefix_map
from bioregistry.schema.struct import SCHEMA_PATH, get_json_schema
from bioregistry.schema_utils import is_mismatch
from bioregistry.utils import _norm, extended_encoder

logger = logging.getLogger(__name__)


class TestRegistry(unittest.TestCase):
    """Tests for the registry."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.registry = bioregistry.read_registry()
        self.metaregistry = bioregistry.read_metaregistry()

    def test_schema(self):
        """Test the schema is up-to-date."""
        actual = SCHEMA_PATH.read_text()
        expected = json.dumps(get_json_schema(), indent=2)
        self.assertEqual(expected, actual)

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
                self.assertNotIn(":", prefix)

    def test_valid_integration_annotations(self):
        """Test that the integration keys are valid."""
        valid = {"required", "optional", "suggested", "required_for_new"}
        for name, field in Resource.__fields__.items():
            with self.subTest(name=name):
                status = field.field_info.extra.get("integration_status", None)
                if field.required:
                    self.assertEqual(
                        "required",
                        status,
                        msg=f"required field {name} is not marked with integration_status",
                    )
                elif status:
                    self.assertIn(status, valid, msg=f"invalid integration status for field {name}")

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
                desc = bioregistry.get_description(prefix)
                self.assertIsNotNone(desc)

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
                self.assertTrue(
                    any(
                        uri_format.startswith(protocol + "://")
                        for protocol in ["http", "https", "ftp", "s3"]
                    ),
                    msg=f"{prefix} URI format dos not start with a valid protocol",
                )
                self.assertIn("$1", uri_format, msg=f"{prefix} URI format does not have a $1")

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
            for use_preferred in (True, False):
                curie_example = entry.get_example_curie(use_preferred=use_preferred)
                curie_pattern = bioregistry.get_curie_pattern(prefix, use_preferred=use_preferred)
                if curie_pattern is None or curie_example is None:
                    continue
                with self.subTest(prefix=prefix, use_preferred=use_preferred):
                    self.assertRegex(
                        curie_example,
                        curie_pattern,
                        msg=dedent(
                            f"""
                    prefix: {prefix}
                    preferred prefix: {entry.get_preferred_prefix()}
                    example CURIE: {curie_example}
                    pattern for LUI: {bioregistry.get_pattern(prefix)}
                    pattern for CURIE: {curie_pattern}
                    """
                        ),
                    )

    def test_pattern_with_banana(self):
        """Test getting patterns with bananas."""
        resource = self.registry["chebi"]
        self.assertEqual(
            "^CHEBI:\\d+$",
            resource.get_pattern_with_banana(),
        )
        self.assertEqual("^(CHEBI:)?\\d+$", resource.get_pattern_with_banana(strict=False))

        resource = self.registry["agrovoc"]
        self.assertEqual(
            "^c_[a-z0-9]+$",
            resource.get_pattern_with_banana(),
        )
        self.assertEqual("^(c_)?[a-z0-9]+$", resource.get_pattern_with_banana(strict=False))

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
                    self.assert_is_valid_identifier(prefix, example)

    def assert_is_valid_identifier(self, prefix: str, example: str) -> None:
        """Assert the identifier is canonical."""
        entry = self.registry[prefix]
        canonical = entry.is_valid_identifier(example)
        self.assertTrue(canonical is None or canonical, msg=f"[{prefix}] invalid LUID: {example}")

    def test_extra_examples(self):
        """Test extra examples."""
        for prefix, entry in self.registry.items():
            if not entry.example_extras:
                continue
            primary_example = entry.get_example()
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(
                    primary_example, msg="entry has extra examples but not primary example"
                )

            for example in entry.example_extras:
                with self.subTest(prefix=prefix, identifier=example):
                    self.assertEqual(entry.standardize_identifier(example), example)
                    self.assertNotEqual(
                        primary_example, example, msg="extra example matches primary example"
                    )
                    self.assert_is_valid_identifier(prefix, example)

            self.assertEqual(
                len(entry.example_extras),
                len(set(entry.example_extras)),
                msg="duplicate extra examples",
            )

    def test_example_decoys(self):
        """Test example decoys."""
        for prefix, entry in self.registry.items():
            if not entry.example_decoys:
                continue
            with self.subTest(prefix=prefix):
                pattern = entry.get_pattern()
                self.assertIsNotNone(pattern)
                for example in entry.example_decoys:
                    self.assertNotRegex(example, pattern)

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
        self.assertFalse(bioregistry.is_standardizable_identifier("nope", ...))
        self.assertIsNone(bioregistry.get_default_iri("nope", ...))
        self.assertIsNone(bioregistry.get_identifiers_org_iri("nope", ...))
        self.assertIsNone(bioregistry.get_n2t_iri("nope", ...))
        self.assertIsNone(bioregistry.get_bioportal_iri("nope", ...))
        self.assertIsNone(bioregistry.get_bioportal_iri("gmelin", ...))
        self.assertIsNone(bioregistry.get_identifiers_org_iri("nope", ...))
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
        s = resource_to_rdf_str("chebi", manager=manager)
        self.assertIsInstance(s, str)

    def test_parts(self):
        """Make sure all part of relations point to valid prefixes."""
        for prefix, resource in self.registry.items():
            if bioregistry.is_deprecated(prefix) or bioregistry.get_provides_for(prefix):
                continue
            if resource.part_of is None or resource.part_of == "pubchem":
                continue

            with self.subTest(prefix=prefix):
                norm_part_of = bioregistry.normalize_prefix(resource.part_of)
                if norm_part_of is not None:
                    self.assertEqual(
                        norm_part_of, resource.part_of, msg="part_of is not standardized"
                    )
                # Some are not prefixes, e.g., datanator_gene, datanator_metabolite, ctd.
                # self.assertIn(
                #     resource.part_of, self.registry, msg="super-resource is not a valid prefix"
                # )

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

    def test_records(self):
        """Test generating records."""
        records: Mapping[str, curies.Record] = {
            record.prefix: record
            for record in bioregistry.manager.get_curies_records(include_prefixes=True)
        }

        # This is a "provides" situation
        self.assertNotIn("ctd.gene", set(records))
        self.assertIn("ncbigene", set(records))
        ncbigene_record = records["ncbigene"]
        self.assertIsInstance(ncbigene_record, curies.Record)
        self.assertEqual("ncbigene", ncbigene_record.prefix)
        self.assertEqual("https://www.ncbi.nlm.nih.gov/gene/", ncbigene_record.uri_prefix)
        self.assertIn("EGID", ncbigene_record.prefix_synonyms)
        self.assertIn("entrez", ncbigene_record.prefix_synonyms)
        self.assertIn("https://bioregistry.io/ncbigene:", ncbigene_record.uri_prefix_synonyms)
        self.assertIn("http://identifiers.org/ncbigene:", ncbigene_record.uri_prefix_synonyms)
        self.assertIn(
            "https://scholia.toolforge.org/ncbi-gene/", ncbigene_record.uri_prefix_synonyms
        )

        # Test that all of the CTD gene stuff is rolled into NCBIGene because CTD gene provides for NCBI gene
        self.assertIn("ctd.gene", ncbigene_record.prefix_synonyms)
        self.assertIn("ctd.gene:", ncbigene_record.uri_prefix_synonyms)
        self.assertIn("http://identifiers.org/ctd.gene:", ncbigene_record.uri_prefix_synonyms)
        self.assertIn("https://bioregistry.io/ctd.gene:", ncbigene_record.uri_prefix_synonyms)
        self.assertIn(
            "https://ctdbase.org/detail.go?type=gene&acc=", ncbigene_record.uri_prefix_synonyms
        )

        # This is a "canonical" situation
        self.assertIn("ena.embl", set(records))
        record = records["ena.embl"]
        self.assertIsInstance(record, curies.Record)
        self.assertEqual("ena.embl", record.prefix)
        self.assertEqual("ena.embl", record.prefix)
        self.assertIn("bioproject", record.prefix_synonyms)
        self.assertIn("ena.embl:", record.uri_prefix_synonyms)
        self.assertIn("bioproject:", record.uri_prefix_synonyms)

        # part of but different stuff
        self.assertNotIn("biogrid.interaction", records["biogrid"].prefix_synonyms)

        self.assertIn("biogrid.interaction", set(records))
        record = records["biogrid.interaction"]
        self.assertIsInstance(record, curies.Record)
        self.assertEqual("biogrid.interaction", record.prefix)
        self.assertEqual("https://thebiogrid.org/interaction/", record.uri_prefix)

        # part of but same URIs
        self.assertIn("kegg", set(records))
        record = records["kegg"]
        self.assertIsInstance(record, curies.Record)
        self.assertEqual("kegg", record.prefix)
        self.assertIn("kegg.module", record.prefix_synonyms)
        self.assertEqual("http://www.kegg.jp/entry/", record.uri_prefix)
        self.assertIn("kegg:", record.uri_prefix_synonyms)
        self.assertIn("kegg.module:", record.uri_prefix_synonyms)

        # Make sure sure primary URI prefix gets upgraded properly from vz -> canonical for -> viralzone
        self.assertIn("http://viralzone.expasy.org/", records["viralzone"].uri_prefix_synonyms)

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

    def test_default_prefix_map_no_miriam(self):
        """Test no identifiers.org URI prefixes get put in the prefix map."""
        self.assert_no_idot(bioregistry.get_prefix_map())
        # self.assert_no_idot(bioregistry.get_prefix_map(include_synonyms=True))

    def test_obo_prefix_map(self):
        """Test the integrity of the OBO prefix map."""
        obofoundry_prefix_map = get_obo_context_prefix_map()
        self.assert_no_idot(obofoundry_prefix_map)
        self.assertIn("FlyBase", set(obofoundry_prefix_map))

        self.assert_no_idot(get_obo_context_prefix_map(include_synonyms=True))

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
        self.assertEqual("GO", self.registry["go"].get_preferred_prefix())
        self.assertEqual("AAO", self.registry["aao"].get_preferred_prefix())
        self.assertEqual("NCBITaxon", self.registry["ncbitaxon"].get_preferred_prefix())
        self.assertEqual("MGI", self.registry["mgi"].get_preferred_prefix())

        for prefix, resource in self.registry.items():
            if bioregistry.is_deprecated(prefix):
                continue
            pp = resource.get_preferred_prefix()
            if pp is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertEqual(prefix.replace(".", "").replace("_", ""), _norm(pp))
                # TODO consider later if preferred prefix should
                #  explicitly not be mentioned in synonyms
                # self.assertNotIn(pp, resource.get_synonyms())

    def test_priority_prefix(self):
        """Test getting priority prefixes."""
        resource = self.registry["go"]
        self.assertEqual("go", resource.get_priority_prefix())
        self.assertEqual("go", resource.get_priority_prefix("default"))
        self.assertEqual("go", resource.get_priority_prefix("bioregistry"))
        self.assertEqual("go", resource.get_priority_prefix("obofoundry"))
        self.assertEqual("GO", resource.get_priority_prefix("preferred"))

        resource = self.registry["biomodels.kisao"]
        self.assertEqual("biomodels.kisao", resource.get_priority_prefix())
        self.assertEqual("biomodels.kisao", resource.get_priority_prefix("default"))
        self.assertEqual("biomodels.kisao", resource.get_priority_prefix("bioregistry"))
        self.assertEqual("kisao", resource.get_priority_prefix("obofoundry"))
        self.assertEqual("KISAO", resource.get_priority_prefix("obofoundry.preferred"))
        self.assertEqual("biomodels.kisao", resource.get_priority_prefix("preferred"))

    def test_mappings(self):
        """Make sure all mapping keys are valid metaprefixes."""
        for prefix, resource in self.registry.items():
            with self.subTest(prefix=prefix):
                for metaprefix in resource.mappings or {}:
                    self.assertIn(metaprefix, self.metaregistry)
                for metaprefix in self.metaregistry:
                    d = getattr(resource, metaprefix, None)
                    if not d:
                        continue
                    prefix = d.get("prefix")
                    if prefix is None:
                        if metaprefix == "wikidata":
                            # FIXME make separate field for these
                            self.assertTrue("paper" in d or "database" in d)
                        else:
                            self.fail()
                    else:
                        self.assertIsNotNone(
                            resource.mappings,
                            msg=f"did not find {metaprefix} mapping in {prefix} in {d}",
                        )
                        self.assertIn(metaprefix, set(resource.mappings))

    def test_provider_codes(self):
        """Make sure provider codes are unique."""
        for prefix, resource in self.registry.items():
            if not resource.providers:
                continue
            with self.subTest(prefix=prefix):
                for provider in resource.providers:
                    self.assertNotEqual(provider.code, prefix)
                    self.assertNotIn(provider.code, self.metaregistry)
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

        for prefix, resource in self.registry.items():
            if resource.license is None:
                continue
            with self.subTest(prefix=prefix):
                standard_license = standardize_license(resource.license)
                self.assertEqual(
                    standard_license,
                    resource.license,
                    msg=f"manually curated license in {prefix} should be standardized"
                    f" to SPDX identifier {standard_license}",
                )

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

    def test_no_contributor_duplicates(self):
        """Test that the contributor doesn't show up in the contributor extras."""
        for prefix, resource in self.registry.items():
            with self.subTest(prefix=prefix):
                if not resource.contributor or not resource.contributor_extras:
                    continue
                for contributor in resource.contributor_extras:
                    self.assertNotEqual(
                        resource.contributor.orcid, contributor.orcid, msg="Duplicated contributor"
                    )

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

    def test_request_issue(self):
        """Check all prefixes with a request issue have a reviewer."""
        for prefix, resource in self.registry.items():
            if resource.github_request_issue is None:
                continue
            with self.subTest(prefix=prefix):
                if resource.contributor.github != "cthoyt":
                    # needed to bootstrap records before there was more governance in place
                    self.assertIsNotNone(resource.reviewer)
                self.assertNotIn(
                    f"https://github.com/biopragmatics/bioregistry/issues/{resource.github_request_issue}",
                    resource.references or [],
                    msg="Reference to GitHub request issue should be in its dedicated field.",
                )

    def test_publications(self):
        """Test references and publications are sorted right."""
        for prefix, resource in self.registry.items():
            with self.subTest(prefix=prefix):
                if resource.references:
                    for reference in resource.references:
                        self.assertNotIn("doi", reference)
                        self.assertNotIn("pubmed", reference)
                        self.assertNotIn("pmc", reference)
                        self.assertNotIn("arxiv", reference)
                if resource.publications:
                    for publication in resource.publications:
                        self.assertIsNotNone(
                            publication.title,
                            msg=f"Manually curated publication {publication} is missing a title. Please run the "
                            "publication clean-up script `python -m bioregistry.curation.enrich_publications` "
                            "to automatically retrieve the title or `python -m bioregistry.curation.clean_publications`"
                            " to prune it.",
                        )
                        self.assertLessEqual(
                            1,
                            sum(
                                (
                                    publication.doi is not None,
                                    publication.pubmed is not None,
                                    publication.pmc is not None,
                                )
                            ),
                        )
                        if publication.doi:
                            # DOIs are case insensitive, so standardize to lowercase in bioregistry
                            self.assertEqual(publication.doi.lower(), publication.doi)

                    # Test no duplicates
                    index = defaultdict(lambda: defaultdict(list))
                    for publication in resource.publications:
                        for key, value in publication.dict().items():
                            if key in {"title", "year"} or value is None:
                                continue
                            index[key][value].append(publication)
                    for citation_prefix, citation_identifier_dict in index.items():
                        for citation_identifier, values in citation_identifier_dict.items():
                            self.assertEqual(
                                1,
                                len(values),
                                msg=f"[{prefix}] duplication on {citation_prefix}:{citation_identifier}",
                            )

    def test_mapping_patterns(self):
        """Test mappings correspond to valid identifiers."""
        k = {}
        for metaprefix, registry in self.metaregistry.items():
            if registry.bioregistry_prefix:
                resource = self.registry[registry.bioregistry_prefix]
            elif registry.prefix in self.registry:
                resource = self.registry[registry.prefix]
            else:
                continue
            pattern = resource.get_pattern_re()
            if pattern is None:
                continue
            k[metaprefix] = pattern

        for prefix, resource in self.registry.items():
            for metaprefix, metaidentifier in resource.get_mappings().items():
                pattern = k.get(metaprefix)
                if pattern is None:
                    continue
                with self.subTest(prefix=prefix, metaprefix=metaprefix):
                    self.assertRegex(metaidentifier, pattern)

    def test_standardize_identifier(self):
        """Standardize the identifier."""
        examples = [
            ("agrovoc", "1234", "1234"),
            ("agrovoc", "c_1234", "1234"),
        ]
        for prefix, identifier, norm_identifier in examples:
            with self.subTest(prefix=prefix, identifier=identifier):
                self.assertEqual(
                    norm_identifier, bioregistry.standardize_identifier(prefix, identifier)
                )
