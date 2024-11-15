"""Test for checking the paper ranking model."""

import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from bioregistry.analysis.paper_ranking import load_curated_papers


class TestLoadCuratedPapers(unittest.TestCase):
    """Tests for Load Curated Papers."""

    @patch("bioregistry.analysis.paper_ranking.pubmed_client.get_metadata_for_ids")
    @patch("bioregistry.analysis.paper_ranking.pd.read_csv")
    def test_load_curated_papers(self, mock_read_csv, mock_get_metadata):
        """Tests load curated papers function."""
        # Test data
        test_data = pd.DataFrame({"pmid": [11111, 22222, 33333], "relevant": [1, 0, 1]})
        mock_read_csv.return_value = test_data

        # Mock fetching metadata
        mock_get_metadata.return_value = {
            11111: {"title": "Paper 1", "abstract": "Abstract 1"},
            22222: {"title": "Paper 2", "abstract": "Abstract 2"},
            33333: {"title": "Paper 3", "abstract": "Abstract 3"},
        }

        # Expected DataFrame
        expected_df = pd.DataFrame(
            {
                "pubmed": [11111, 22222, 33333],
                "label": [1, 0, 1],
                "title": ["Paper 1", "Paper 2", "Paper 3"],
                "abstract": ["Abstract 1", "Abstract 2", "Abstract 3"],
            }
        )

        actual_df = load_curated_papers(file_path=Path("dummy/path/curated_papers.tsv"))

        # Check for equality
        pd.testing.assert_frame_equal(actual_df, expected_df)


if __name__ == "__main__":
    unittest.main()
