"""Test for checking the paper ranking model."""

import datetime
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from click.testing import CliRunner

from bioregistry.analysis.paper_ranking import main


class TestPaperRanking(unittest.TestCase):
    """Tests the paper ranking model."""

    def setUp(self):
        """Set up the test case with paths for the files."""
        root_dir = root_dir = Path(__file__).resolve().parent.parent
        self.bioregistry_file = root_dir / "src" / "bioregistry" / "data" / "bioregistry.json"
        self.output_directory = root_dir / "exports" / "analyses" / "paper_ranking"

        # Check if bioregistry file exists
        self.assertTrue(self.bioregistry_file.exists(), "Bioregistry file does not exist")

    @patch("bioregistry.analysis.paper_ranking.load_curated_papers")
    @patch("pandas.DataFrame.to_csv")
    def test_pipeline(self, mock_to_csv, mock_load_curated_papers):
        """Smoke test to ensure pipeline runs successfully without error."""
        # Mocking this data resolves the issue of the curated_papers.tsv file being missing from tox environment
        mock_data = {
            "pubmed": [39145441, 39163546, 39010878, 39074139, 39084442],
            "label": [0, 1, 0, 1, 0],
            "title": [
                "Clustering protein functional families at large scale with hierarchical approaches.",
                "GMMID: genetically modified mice information database.",
                "MotifbreakR v2: extended capability and database integration.",
                "FURNA: A database for functional annotations of RNA structures.",
                "HSADab: A comprehensive database for human serum albumin.",
            ],
            "abstract": [
                "Proteins, fundamental to cellular activities, reveal their function and evolution",
                "Genetically engineered mouse models (GEMMs) are vital for elucidating gene function",
                "MotifbreakR is a software tool that scans genetic variants against position weight",
                "Despite the increasing number of 3D RNA structures in the Protein Data Bank, the",
                "Human Serum Albumin (HSA), the most abundant protein in human body fluids, plays a",
            ],
        }
        mock_df = pd.DataFrame(mock_data)
        mock_load_curated_papers.return_value = mock_df

        start_date = datetime.date.today().isoformat()
        end_date = datetime.date.today().isoformat()

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

        # Check call count of to_csv is 3 for evaluation, importances and prediction file.
        self.assertEqual(
            mock_to_csv.call_count,
            3,
            f"Expected to_csv call count is 3. It was called {mock_to_csv.call_count} times",
        )


if __name__ == "__main__":
    unittest.main()
