# -*- coding: utf-8 -*-

"""Tests for the bioregistry client."""

import unittest

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
