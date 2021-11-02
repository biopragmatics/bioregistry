# -*- coding: utf-8 -*-

"""Test for web."""

import unittest

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
