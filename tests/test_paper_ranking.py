"""Test for checking the paper ranking model."""

import datetime
import json
import unittest
import unittest.mock
from pathlib import Path

from bioregistry.analysis.paper_ranking import runner
from bioregistry.constants import BIOREGISTRY_PATH, EXPORT_ANALYSES

HERE = Path(__file__).parent.resolve()
RESOURCES = HERE.joinpath("resources")
MOCK_DATA_PATH = RESOURCES.joinpath("mock_pubmed_data.json")
MOCK_SEARCH_PATH = RESOURCES.joinpath("mock_search.json")


class TestPaperRanking(unittest.TestCase):
    """Tests the paper ranking model."""

    def setUp(self):
        """Set up the test case with paths for the files."""
        self.output_directory = EXPORT_ANALYSES / "paper_ranking"

    @unittest.mock.patch("bioregistry.analysis.paper_ranking._get_metadata_for_ids")
    @unittest.mock.patch("bioregistry.analysis.paper_ranking._get_ids")
    def test_pipeline(self, mock_get_metadata_for_ids, mock_get_ids):
        """Smoke test to ensure pipeline runs successfully without error."""
        start_date = datetime.date.today().isoformat()
        end_date = datetime.date.today().isoformat()

        mock_get_metadata_for_ids.return_value = json.loads(MOCK_DATA_PATH.read_text())
        mock_get_ids.return_value = {}

        runner(BIOREGISTRY_PATH, start_date, end_date, include_remote=False)

        # TODO ideally the tests check the actual functionality and not the I/O

        # Check if the evaluation file was created
        evaluation_file = self.output_directory.joinpath("evaluation.tsv")
        self.assertTrue(evaluation_file.exists(), f"{evaluation_file} was not created")

        # Check if the importances file was created
        importances_file = self.output_directory.joinpath("importances.tsv")
        self.assertTrue(importances_file.exists(), f"{importances_file} was not created")


if __name__ == "__main__":
    unittest.main()
