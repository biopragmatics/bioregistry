# -*- coding: utf-8 -*-

"""Tests for data integrity."""

import datetime
import logging
import unittest

import bioregistry
from bioregistry.export.rdf_export import resource_to_rdf_str
from bioregistry.resolve import EMAIL_RE, _get_prefix_key
from bioregistry.utils import is_mismatch

logger = logging.getLogger(__name__)


class TestRegistry(unittest.TestCase):
    """Tests for the registry."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.registry = bioregistry.read_registry()

    def test_keys(self):
        """Check the required metadata is there."""
        keys = {
            # Required
            'description',
            'homepage',
            'name',
            # Recommended
            'contact',
            'download',
            'example',
            'pattern',
            'type',
            'url',
            # Only there if true
            'no_own_terms',
            'not_available_as_obo',
            'namespaceEmbeddedInLui',
            # Only there if false
            # Lists
            'appears_in',
            # Other
            'deprecated',
            'banana',
            'mappings',
            'ols_version_date_format',
            'ols_version_prefix',
            'ols_version_suffix_split',
            'ols_version_type',
            'part_of',
            'provides',
            'references',
            'synonyms',
            'comment',
        }
        keys.update(bioregistry.read_metaregistry())
        for prefix, entry in self.registry.items():
            extra = {k for k in set(entry) - keys if not k.startswith('_')}
            if not extra:
                continue
            with self.subTest(prefix=prefix):
                self.fail(f'had extra keys: {extra}')

    def test_names(self):
        """Test that all entries have a name."""
        for prefix, entry in self.registry.items():
            with self.subTest(prefix=prefix):
                self.assertFalse(
                    'name' not in entry
                    and 'name' not in entry.get('miriam', {})
                    and 'name' not in entry.get('ols', {})
                    and 'name' not in entry.get('obofoundry', {}),
                    msg=f'{prefix} is missing a name',
                )

    def test_name_expansions(self):
        """Test that default names are not capital acronyms."""
        for prefix in bioregistry.read_registry():
            if bioregistry.is_deprecated(prefix):
                continue
            entry = bioregistry.get(prefix)
            if 'name' in entry:
                continue
            name = bioregistry.get_name(prefix)
            if prefix == name.lower() and name.upper() == name:
                with self.subTest(prefix=prefix):
                    self.fail(msg=f'{prefix} acronym ({name}) is not expanded')

            if '.' in prefix and prefix.split('.')[0] == name.lower():
                with self.subTest(prefix=prefix):
                    self.fail(msg=f'{prefix} acronym ({name}) is not expanded')

    def test_homepage_http(self):
        """Test that all homepages start with http."""
        for prefix in bioregistry.read_registry():
            homepage = bioregistry.get_homepage(prefix)
            if homepage is None or homepage.startswith('http'):
                continue
            with self.subTest(prefix=prefix):
                self.fail(msg=f'malformed homepage: {homepage}')

    def test_email(self):
        """Test that the email getter returns valid email addresses."""
        for prefix in bioregistry.read_registry():
            email = _get_prefix_key(prefix, 'contact', ('obofoundry', 'ols'))
            if email is None or EMAIL_RE.match(email):
                continue
            with self.subTest(prefix=prefix):
                self.fail(msg=f'bad email: {email}')

    def test_no_redundant_acronym(self):
        """Test that there is no redundant acronym in the name.

        For example, "Amazon Standard Identification Number (ASIN)" is a problematic
        name for prefix "asin".
        """
        for prefix in bioregistry.read_registry():
            if bioregistry.is_deprecated(prefix):
                continue
            entry = bioregistry.get(prefix)
            if 'name' in entry:
                continue
            name = bioregistry.get_name(prefix)

            try:
                _, rest = name.rstrip(')').rsplit('(', 1)
            except ValueError:
                continue
            if rest.lower() == prefix.lower():
                with self.subTest(prefix=prefix):
                    self.fail(msg=f'{prefix} has redundany acronym in name "{name}"')

    def test_format_urls(self):
        """Test that entries with a format URL are formatted right (yo dawg)."""
        for prefix, entry in self.registry.items():
            url = entry.get('url')
            if not url:
                continue
            with self.subTest(prefix=prefix):
                self.assertIn('$1', url, msg=f'{prefix} format does not have a $1')

    def test_patterns(self):
        """Test that all prefixes are norm-unique."""
        for prefix, entry in self.registry.items():
            pattern = entry.get('pattern')
            if pattern is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertTrue(pattern.startswith('^'), msg=f'{prefix} pattern {pattern} should start with ^')
                self.assertTrue(pattern.endswith('$'), msg=f'{prefix} pattern {pattern} should end with $')

                # Check that it's the same as external definitions
                for key in ('miriam', 'wikidata'):
                    external_pattern = entry.get('key', {}).get('pattern')
                    if external_pattern:
                        self.assertEqual(pattern, external_pattern, msg=f'{prefix}: {key} pattern not same')

    def test_examples(self):
        """Test that all entries have examples."""
        for prefix, entry in self.registry.items():
            if 'pattern' not in entry:  # TODO remove this later
                continue
            with self.subTest(prefix=prefix):
                msg = f'{prefix} is missing an example local identifier'
                if 'ols' in entry:
                    msg += f'\nSee: https://www.ebi.ac.uk/ols/ontologies/{entry["ols"]["prefix"]}/terms'
                self.assertIsNotNone(bioregistry.get_example(prefix), msg=msg)

    def test_examples_pass_patterns(self):
        """Test that all examples pass the patterns."""
        for prefix in self.registry:
            pattern = bioregistry.get_pattern_re(prefix)
            example = bioregistry.get_example(prefix)
            if pattern is None or example is None:
                continue
            if prefix == 'ark':
                continue  # FIXME
            if bioregistry.validate(prefix, example):
                continue
            with self.subTest(prefix=prefix):
                self.assertRegex(example, pattern)

    def test_ols_versions(self):
        """Test that all OLS entries have a version annotation on them."""
        for bioregistry_id, bioregistry_entry in self.registry.items():
            ols = bioregistry_entry.get('ols')
            if not ols:
                continue

            version = ols.get('version')
            if version is None:
                logger.warning('[%s] missing version', bioregistry_id)
                continue

            with self.subTest(prefix=bioregistry_id):
                if version != version.strip():
                    logger.warning('Extra whitespace in %s', bioregistry_id)
                    version = version.strip()

                version_prefix = bioregistry_entry.get('ols_version_prefix')
                if version_prefix:
                    self.assertTrue(version.startswith(version_prefix))
                    version = version[len(version_prefix):]

                if bioregistry_entry.get('ols_version_suffix_split'):
                    version = version.split()[0]

                version_suffix = bioregistry_entry.get('ols_version_suffix')
                if version_suffix:
                    self.assertTrue(version.endswith(version_suffix))
                    version = version[:-len(version_suffix)]

                version_type = bioregistry_entry.get('ols_version_type')
                version_date_fmt = bioregistry_entry.get('ols_version_date_format')
                self.assertTrue(
                    version_type is not None or version_date_fmt is not None,
                    msg=f'missing either a ``ols_version_type`` or ``ols_version_date_format`` for date: {version}',
                )

                if version_date_fmt:
                    if version_date_fmt in {"%Y-%d-%m"}:
                        logger.warning('Confusing date format for %s (%s)', bioregistry_id, version_date_fmt)
                    try:
                        version = datetime.datetime.strptime(version, version_date_fmt)
                    except ValueError:
                        logger.warning('Wrong format for %s (%s)', bioregistry_id, version)

    def test_is_mismatch(self):
        """Check for mismatches."""
        self.assertTrue(is_mismatch('geo', 'ols', 'geo'))
        self.assertFalse(is_mismatch('geo', 'miriam', 'geo'))

    def test_get_nope(self):
        """Test when functions don't return."""
        self.assertIsNone(bioregistry.get_banana('nope'))
        self.assertIsNone(bioregistry.get_description('nope'))
        self.assertIsNone(bioregistry.get_homepage('nope'))
        self.assertIsNone(bioregistry.get_format('gmelin'))  # no URL
        self.assertIsNone(bioregistry.get_format('nope'))
        self.assertIsNone(bioregistry.get_version('nope'))
        self.assertIsNone(bioregistry.get_name('nope'))
        self.assertIsNone(bioregistry.get_example('nope'))
        self.assertIsNone(bioregistry.get_email('nope'))
        self.assertIsNone(bioregistry.get_mappings('nope'))
        self.assertIsNone(bioregistry.get_fairsharing_prefix('nope'))
        self.assertIsNone(bioregistry.get_obofoundry_prefix('nope'))
        self.assertIsNone(bioregistry.get_obofoundry_format('nope'))
        self.assertIsNone(bioregistry.get_obo_download('nope'))
        self.assertIsNone(bioregistry.get_owl_download('nope'))
        self.assertIsNone(bioregistry.get_ols_link('nope', ...))
        self.assertIsNone(bioregistry.get_obofoundry_link('nope', ...))
        self.assertTrue(bioregistry.has_terms('nope'))
        self.assertFalse(bioregistry.is_deprecated('nope'))
        self.assertFalse(bioregistry.is_provider('nope'))
        self.assertIsNone(bioregistry.get_provides_for('nope'))
        self.assertIsNone(bioregistry.get_version('gmelin'))
        self.assertIsNone(bioregistry.validate('nope', ...))
        self.assertIsNone(bioregistry.get_default_url('nope', ...))
        self.assertIsNone(bioregistry.get_identifiers_org_url('nope', ...))
        self.assertIsNone(bioregistry.get_n2t_url('nope', ...))
        self.assertIsNone(bioregistry.get_bioportal_url('nope', ...))
        self.assertIsNone(bioregistry.get_bioportal_url('gmelin', ...))
        self.assertIsNone(bioregistry.get_identifiers_org_url('nope', ...))
        self.assertIsNone(bioregistry.get_identifiers_org_url('pid.pathway', ...))
        self.assertIsNone(bioregistry.get_identifiers_org_url('gmelin', ...))
        self.assertIsNone(bioregistry.get_link('gmelin', ...))

    def test_get(self):
        """Test getting resources."""
        self.assertIsInstance(bioregistry.get_description('chebi'), str)

        # No OBO Foundry format for dbSNP b/c not in OBO Foundry (and probably never will be)
        self.assertIsNone(bioregistry.get_obofoundry_format('dbsnp'))

        self.assertEqual('FAIRsharing.mya1ff', bioregistry.get_fairsharing_prefix('ega.dataset'))

    def test_get_rdf(self):
        """Test conversion to RDF."""
        s = resource_to_rdf_str('chebi')
        self.assertIsInstance(s, str)
