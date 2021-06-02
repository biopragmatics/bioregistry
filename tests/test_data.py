# -*- coding: utf-8 -*-

"""Tests for data integrity."""

import datetime
import logging
import unittest
from collections import Counter

import bioregistry
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


class TestCollections(unittest.TestCase):
    """Tests for collections."""

    def test_minimum_metadata(self):
        """Check collections have minimal metadata and correct prefixes."""
        registry = bioregistry.read_registry()

        for key, collection in sorted(bioregistry.read_collections().items()):
            with self.subTest(key=key):
                self.assertRegex(key, '^\\d{7}$')
                self.assertIn('name', collection)
                self.assertIn('authors', collection)
                self.assertIsInstance(collection['authors'], list)
                for author in collection['authors']:
                    self.assertIn('name', author)
                    self.assertIn('orcid', author)
                    self.assertRegex(author['orcid'], bioregistry.get_pattern('orcid'))
                self.assertIn('description', collection)
                incorrect = {
                    prefix
                    for prefix in collection['resources']
                    if prefix not in registry
                }
                self.assertEqual(set(), incorrect)
                duplicates = {
                    prefix
                    for prefix, count in Counter(collection['resources']).items()
                    if 1 < count
                }
                self.assertEqual(set(), duplicates, msg='Duplicates found')


class TestMetaregistry(unittest.TestCase):
    """Tests for the metaregistry."""

    def test_minimum_metadata(self):
        """Test the metaregistry entries have a minimum amount of data."""
        for metaprefix, data in bioregistry.read_metaregistry().items():
            with self.subTest(metaprefix=metaprefix):
                self.assertIn('name', data)
                self.assertIn('homepage', data)
                self.assertIn('example', data)
                self.assertIn('description', data)
                self.assertIn('registry', data)

                # When a registry is a provider, it means it
                # provides for its entries
                self.assertIn('provider', data)
                if data['provider']:
                    self.assertIn('formatter', data)
                    self.assertIn('$1', data['formatter'])

                # When a registry is a resolver, it means it
                # can resolve entries (prefixes) + identifiers
                self.assertIn('resolver', data)
                if data['resolver']:
                    self.assertIn('resolver_url', data)
                    self.assertIn('$1', data['resolver_url'])
                    self.assertIn('$2', data['resolver_url'])

                invalid_keys = set(data).difference({
                    'prefix', 'name', 'homepage', 'download', 'registry',
                    'provider', 'resolver', 'description', 'formatter',
                    'example', 'resolver_url',
                })
                self.assertEqual(set(), invalid_keys, msg='invalid metadata')
