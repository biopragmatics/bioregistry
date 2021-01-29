# -*- coding: utf-8 -*-

"""Tests for data integrity."""

import datetime
import logging
import unittest

import bioregistry

logger = logging.getLogger(__name__)


class TestDuplicates(unittest.TestCase):
    """Tests for duplicates."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.registry = bioregistry.read_bioregistry()

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
        for prefix, entry in self.registry.items():
            pattern = bioregistry.get_pattern_re(prefix)
            example = bioregistry.get_example(prefix)
            if pattern is None or example is None:
                continue

            if 'namespace.rewrite' in entry:
                embedded_prefix = entry['namespace.rewrite']
                example = f'{embedded_prefix}:{example}'
            elif bioregistry.namespace_in_lui(prefix):
                embedded_prefix = entry['miriam']['prefix']  # FIXME not always available via miriam
                if entry.get('namespace.capitalized') or 'obofoundry' in entry:
                    embedded_prefix = embedded_prefix.upper()
                example = f'{embedded_prefix}:{example}'
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
                    msg='missing either a version type or date format string',
                )

                if version_date_fmt:
                    if version_date_fmt in {"%Y-%d-%m"}:
                        logger.warning('Confusing date format for %s (%s)', bioregistry_id, version_date_fmt)
                    try:
                        version = datetime.datetime.strptime(version, version_date_fmt)
                    except ValueError:
                        logger.warning('Wrong format for %s (%s)', bioregistry_id, version)
