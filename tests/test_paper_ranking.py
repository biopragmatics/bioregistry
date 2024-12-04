"""Test for checking the paper ranking model."""

import json
import datetime
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from bioregistry.analysis.paper_ranking import main


class TestPaperRanking(unittest.TestCase):
    """Tests the paper ranking model."""

    def setUp(self):
        """Set up the test case with paths for the files."""
        root_dir = root_dir = Path(__file__).resolve().parent.parent
        self.bioregistry_file = root_dir / "src" / "bioregistry" / "data" / "bioregistry.json"
        self.output_directory = root_dir / "exports" / "analyses" / "paper_ranking"
        self.mock_data_path = root_dir / "tests" / "mock_pubmed_data.json"

        # Check if bioregistry and mock data files exists
        self.assertTrue(self.mock_data_path.exists(), "Mock data file does not exist")
        self.assertTrue(self.bioregistry_file.exists(), "Bioregistry file does not exist")

    @patch("bioregistry.analysis.paper_ranking.pubmed_client.get_metadata_for_ids")
    def test_pipeline(self, mock_get_metadata_for_ids):
        """Smoke test to ensure pipeline runs successfully without error."""
        start_date = datetime.date.today().isoformat()
        end_date = datetime.date.today().isoformat()

        # Mock return value for get_metadata_for_ids
        with open(self.mock_data_path, "r", encoding="utf-8") as file:
            mock_data = json.load(file)

        mock_get_metadata_for_ids.return_value = mock_data

        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "--bioregistry-file",
                str(self.bioregistry_file),
                "--start-date",
                start_date,
                "--end-date",
                end_date,
            ],
        )

        # Check if the pipeline ran successfully
        self.assertEqual(result.exit_code, 0, f"Pipeline failed with: {result.exit_code}")

        # Check if the output directory exists
        self.assertTrue(self.output_directory.exists(), f"{self.output_directory} does not exist")

        # Check if the evaluation file was created
        evaluation_file = self.output_directory.joinpath("evaluation.tsv")
        self.assertTrue(evaluation_file.exists(), f"{evaluation_file} was not created")

        # Check if the importances file was created
        importances_file = self.output_directory.joinpath("importances.tsv")
        self.assertTrue(importances_file.exists(), f"{importances_file} was not created")


if __name__ == "__main__":
    unittest.main()
