"""Test for checking the paper ranking model."""

import datetime
import importlib.util
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import pandas as pd

from bioregistry.analysis.paper_ranking import load_curated_papers, train
from bioregistry.schema import Publication, Resource
from bioregistry.schema_utils import write_registry


@unittest.skipUnless(
    importlib.util.find_spec("pubmed_downloader"), reason="test needs pubmed-downloader"
)
class TestPaperRanking(unittest.TestCase):
    """Tests the paper ranking model."""

    @unittest.mock.patch("bioregistry.analysis.paper_ranking._get_articles_dict")
    @unittest.mock.patch("bioregistry.analysis.paper_ranking._search")
    def test_pipeline(self, mock_search, mock_get_articles_dict):
        """Smoke test to ensure pipeline runs successfully without error."""
        import pubmed_downloader
        from pubmed_downloader import Article
        from pubmed_downloader.api import JournalIssue

        abstract = [pubmed_downloader.AbstractText(text="sample text")]
        journal = pubmed_downloader.Journal(nlm_catalog_id="abcdef")
        journal_issue = JournalIssue(published=datetime.date.today())

        n = 30
        positive_group_1 = [
            Article(
                pubmed=i,
                title=f"test positive {i}",
                abstract=abstract,
                journal=journal,
                journal_issue=journal_issue,
            )
            for i in range(1, n)
        ]
        uncurated_group = [
            Article(
                pubmed=i,
                title=f"test {i}",
                abstract=abstract,
                journal=journal,
                journal_issue=journal_issue,
            )
            for i in range(n, 2 * n)
        ]
        negative_group = [
            Article(
                pubmed=i,
                title=f"test negative {i}",
                abstract=abstract,
                journal=journal,
                journal_issue=journal_issue,
            )
            for i in range(2 * n, 3 * n)
        ]

        registry = {
            "test": Resource(
                prefix="test",
                name="Test",
                publications=[
                    Publication(
                        pubmed=str(positive_group_1[0].pubmed), title=positive_group_1[0].title
                    )
                ],
            )
        }

        articles = [
            *positive_group_1,
            *uncurated_group,
            *negative_group,
        ]

        curated_paper_rows = [
            *((str(article.pubmed), 1) for article in positive_group_1),
            *((str(article.pubmed), 0) for article in negative_group),
            *((str(article.pubmed), None) for article in uncurated_group),
        ]
        curated_papers_df = pd.DataFrame(curated_paper_rows, columns=["pubmed", "relevant"])

        # set the mocks
        mock_get_articles_dict.return_value = {str(article.pubmed): article for article in articles}
        mock_search.return_value = {str(i): ["database"] for i in range(1, 3 * n)}

        # these are dummy values, since we will mock
        # the functions that use them
        datetime.date.today().isoformat()
        datetime.date.today().isoformat()

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)

            curated_papers_path = directory.joinpath("curated-papers.tsv")
            curated_papers_df.to_csv(curated_papers_path, sep="\t", index=False)

            # check that adding in the mock content works
            df = load_curated_papers(curated_papers_path, loud=False)
            self.assertEqual(
                {str(i) for i in range(1, 3 * n)},
                set(df.pubmed),
            )

            registry_path = directory.joinpath("registry.json")
            write_registry(registry, path=registry_path)

            train(
                bioregistry_file=registry_path,
                curated_papers_path=curated_papers_path,
                include_remote=False,
                output_path=directory,
                strict=True,
            )

            # Check if the evaluation file was created
            evaluation_file = directory.joinpath("evaluation.tsv")
            self.assertTrue(evaluation_file.exists(), f"{evaluation_file} was not created")

            # Check if the importances file was created
            importances_file = directory.joinpath("importances.tsv")
            self.assertTrue(importances_file.exists(), f"{importances_file} was not created")
