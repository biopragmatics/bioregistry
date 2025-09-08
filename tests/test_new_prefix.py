"""Tests for new prefix pipeline."""

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from bioregistry.gh.new_prefix import MAPPING, main, process_new_prefix_issue
from bioregistry.schema import Author, Resource

HERE = Path(__file__).parent.resolve()
RESOURCES = HERE.joinpath("resources")
NCBIORTHOLOG_TEST = json.load(RESOURCES.joinpath("ncbiortholog_test.json").open())
VIBSO_TEST = json.load(RESOURCES.joinpath("vibso_test.json").open())


class TestNewPrefix(unittest.TestCase):
    """Tests for new prefix pipeline."""

    @patch("bioregistry.gh.new_prefix.bioregistry.get_resource")
    def test_process_new_prefix_issue(self, mock_get_resource):
        """Tests if Resource object returned is as expected using data from an old issue."""
        mock_get_resource.return_value = None

        issue_id = 1181
        resource_data = copy.deepcopy(NCBIORTHOLOG_TEST)

        expected_resource = Resource(
            prefix="ncbiortholog.test",
            name="National Center for Biotechnology Information",
            description=(
                "Database of one-to-one ortholog information provided by the NCBI as a subset "
                "of their Gene resource. Used for users to access ortholog information for "
                "over 1000 species of vertebrates and arthropods."
            ),
            pattern="^\\d+$",
            uri_format="https://www.ncbi.nlm.nih.gov/gene/$1/ortholog/",
            uri_format_resolvable=None,
            rdf_uri_format=None,
            providers=None,
            homepage="https://www.ncbi.nlm.nih.gov/gene/",
            repository="n/a",
            contact=Author(
                name="Terence Murphy",
                orcid="0000-0001-9311-9745",
                email="murphyte@ncbi.nlm.nih.gov",
                github="murphyte",
            ),
            owners=None,
            example="2",
            example_extras=None,
            example_decoys=None,
            license="US gov't public domain",
            version=None,
            part_of=None,
            provides=None,
            download_owl=None,
            download_obo=None,
            download_json=None,
            download_rdf=None,
            banana=None,
            banana_peel=None,
            deprecated=None,
            mappings=None,
            synonyms=None,
            keywords=None,
            references=None,
            publications=[],
            appears_in=None,
            depends_on=None,
            namespace_in_lui=None,
            no_own_terms=None,
            comment=(
                "We do not currently have the source code for our ortholog resource available publicly, "
                "although we are looking at how to split it off and make it available in the next year. "
                "We are now in the process of adding this tag to the INSDC list for use in annotations, "
                "so I'd like to mirror that tag in bioregistry."
            ),
            contributor=Author(
                name="Terence Murphy",
                orcid="0000-0001-9311-9745",
                email="murphyte@ncbi.nlm.nih.gov",
                github="murphyte",
            ),
            contributor_extras=None,
            reviewer=None,
            proprietary=None,
            has_canonical=None,
            preferred_prefix=None,
            twitter=None,
            mastodon=None,
            github_request_issue=issue_id,
            logo=None,
            miriam=None,
            n2t=None,
            prefixcommons=None,
            wikidata=None,
            go=None,
            obofoundry=None,
            bioportal=None,
            ecoportal=None,
            agroportal=None,
            cropoct=None,
            ols=None,
            aberowl=None,
            ncbi=None,
            uniprot=None,
            biolink=None,
            cellosaurus=None,
            ontobee=None,
            cheminf=None,
            fairsharing=None,
            biocontext=None,
            edam=None,
            re3data=None,
            hl7=None,
            bartoc=None,
            rrid=None,
            lov=None,
            zazuko=None,
            togoid=None,
            integbio=None,
            pathguide=None,
        )

        actual = process_new_prefix_issue(issue_id, resource_data)

        self.assertIsNotNone(actual, "Resource should not be None")
        self.assertEqual(
            actual, expected_resource, "Resource object does not match the expected output"
        )

    @patch("bioregistry.gh.new_prefix.github_client")
    @patch("bioregistry.gh.new_prefix.add_resource")
    def test_specific_issue(self, mock_add_resource, mock_github_client):
        """Test the workflow in a dry run for a specific issue."""
        mock_github_client.get_form_data_for_issue.return_value = copy.deepcopy(NCBIORTHOLOG_TEST)

        runner = CliRunner()
        result = runner.invoke(main, ["--dry", "--issue", "1181"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Processing specific issue 1181", result.output)

        self.assertIn("🚀 Adding resource ncbiortholog.test (#1181)", result.output)
        mock_add_resource.assert_called_once()

        mock_github_client.get_form_data_for_issue.assert_called_once_with(
            "biopragmatics", "bioregistry", 1181, remapping=MAPPING
        )

    @patch("bioregistry.gh.new_prefix.github_client")
    @patch("bioregistry.gh.new_prefix.add_resource")
    def test_all_relevant_issues(self, mock_add_resource, mock_github_client):
        """Test the workflow in a dry run for a all relevant issues."""
        mock_github_client.get_bioregistry_form_data.return_value = {
            1181: copy.deepcopy(NCBIORTHOLOG_TEST),
            1278: copy.deepcopy(VIBSO_TEST),
        }

        runner = CliRunner()
        result = runner.invoke(main, ["--dry"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Running workflow for all relevant issues", result.output)

        self.assertIn(
            "No specific issue provided. Searching for all relevant issues", result.output
        )
        self.assertIn("Adding 2 issues after filter", result.output)

        self.assertIn("🚀 Adding resource ncbiortholog.test (#1181)", result.output)
        self.assertIn("🚀 Adding resource vibso.test (#1278)", result.output)
        self.assertEqual(mock_add_resource.call_count, 2)


if __name__ == "__main__":
    unittest.main()
