# -*- coding: utf-8 -*-

"""Tests for the bioregistry client."""

import unittest

import requests

import bioregistry


class TestResolve(unittest.TestCase):
    """Tests for getting Bioregistry content."""

    def test_resolve(self):
        """Test prefixes can be resolved properly."""
        for expected, query in [
            ('ncbitaxon', 'ncbitaxon'),
            ('ncbitaxon', 'NCBITaxon'),
            ('ncbitaxon', 'taxonomy'),
            ('bel', 'SCOMP'),
            ('bel', 'SFAM'),
            ('eccode', 'ec-code'),
            ('eccode', 'EC_CODE'),
            ('chembl.compound', 'chembl.compound'),
            ('chembl.compound', 'chemblcompound'),
            ('chembl.compound', 'chembl'),
        ]:
            with self.subTest(query=query):
                self.assertEqual(expected, bioregistry.normalize_prefix(query))

    def test_get(self):
        """Test getting content from the bioregistry."""
        ncbitaxon_entry = bioregistry.get('ncbitaxon')
        self.assertIn('synonyms', ncbitaxon_entry)
        self.assertIn('NCBI_Taxon_ID', ncbitaxon_entry['synonyms'])
        self.assertIn('miriam', ncbitaxon_entry)
        self.assertIn('obofoundry', ncbitaxon_entry)
        self.assertIn('ols', ncbitaxon_entry)
        self.assertIn('wikidata', ncbitaxon_entry)

    def test_validate_none(self):
        """Test validation of identifiers for a prefix that does not exist."""
        self.assertIsNone(bioregistry.validate('lol', 'lol:nope'))

    def test_validate_true(self):
        """Test that validation returns true."""
        for prefix, identifier in [
            ('eccode', '1'),
            ('eccode', '1.1'),
            ('eccode', '1.1.1'),
            ('eccode', '1.1.1.1'),
            ('eccode', '1.1.123.1'),
            ('eccode', '1.1.1.123'),
            ('chebi', '24867'),
            ('chebi', 'CHEBI:1234'),
        ]:
            with self.subTest(prefix=prefix, identifier=identifier):
                self.assertTrue(bioregistry.validate(prefix, identifier))

    def test_validate_false(self):
        """Test that validation returns false."""
        for prefix, identifier in [
            ('chebi', 'A1234'),
            ('chebi', 'chebi:1234'),
        ]:
            with self.subTest(prefix=prefix, identifier=identifier):
                self.assertFalse(bioregistry.validate(prefix, identifier))

    def test_lui(self):
        """Test the LUI makes sense (spoilers, they don't).

        Discussion is ongoing at:

        - https://github.com/identifiers-org/identifiers-org.github.io/issues/151
        """
        for prefix in bioregistry.read_bioregistry():
            if not bioregistry.namespace_in_lui(prefix):
                continue
            if bioregistry.get_banana(prefix):
                continue  # rewrite rules are applied to prefixes with bananas
            if prefix in {'ark', 'obi'}:
                continue  # these patterns on identifiers.org are garb
            with self.subTest(prefix=prefix):
                re_pattern = bioregistry.get_pattern(prefix)
                miriam_prefix = bioregistry.get_identifiers_org_prefix(prefix)
                self.assertTrue(
                    re_pattern.startswith(f'^{miriam_prefix.upper()}') or re_pattern.startswith(miriam_prefix.upper()),
                    msg=f'{prefix} pattern: {re_pattern}',
                )

    def test_banana(self):
        """Test that entries curated with a new banana are resolved properly."""
        for prefix, entry in bioregistry.read_bioregistry().items():
            banana = entry.get('banana')
            if banana is None:
                continue
            if prefix in {'gramene.growthstage', 'oma.hog'}:
                continue  # identifiers.org is broken for these prefixes
            with self.subTest(
                prefix=prefix,
                banana=banana,
                pattern=bioregistry.get_pattern(prefix),
            ):
                identifier = bioregistry.get_example(prefix)
                self.assertIsNotNone(identifier)
                url = bioregistry.resolve_identifier.get_identifiers_org_url(prefix, identifier)
                res = requests.get(url)
                self.assertEqual(200, res.status_code, msg=f'failed with URL: {url}')
