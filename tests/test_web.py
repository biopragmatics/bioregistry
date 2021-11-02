# -*- coding: utf-8 -*-

"""Test for web."""

import sys
import unittest

import bioregistry
from bioregistry.app.wsgi import app


class TestWeb(unittest.TestCase):
    """Tests for the web application."""

    def test_download_registry_json(self):
        """Test downloading the full registry as JSON."""
        with app.test_client() as client:
            res = client.get("/api/registry")
            self.assertEqual(200, res.status_code)
            res = client.get("/api/registry?format=json")
            self.assertEqual(200, res.status_code)

    def test_download_registry(self):
        """Test downloading the full registry as YAML."""
        with app.test_client() as client:
            res = client.get("/api/registry?format=yaml")
            self.assertEqual(200, res.status_code)

    def test_download_resource(self):
        """Test downloading a resource as YAML."""
        fmts = ["json", "yaml", "turtle"]
        if sys.version_info[1] >= 7:
            fmts.append("jsonld")
        with app.test_client() as client:
            for fmt in fmts:
                with self.subTest(fmt=fmt):
                    res = client.get(f"/api/registry/3dmet?format={fmt}")
                    self.assertEqual(200, res.status_code)

    def test_view_resource(self):
        """Test viewing resources."""
        with app.test_client() as client:
            for prefix in list(bioregistry.read_registry())[:5]:
                with self.subTest(prefix=prefix):
                    res = client.get(f"/registry/{prefix}")
                    self.assertEqual(200, res.status_code, msg=res)

    def test_view_metaresource(self):
        """Test viewing metaresources."""
        with app.test_client() as client:
            for metaprefix in bioregistry.read_metaregistry():
                with self.subTest(metaprefix=metaprefix):
                    res = client.get(f"/metaregistry/{metaprefix}")
                    self.assertEqual(200, res.status_code, msg=res)
