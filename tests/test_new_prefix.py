"""Tests for new prefix pipeline."""

import unittest
from unittest.mock import patch

from bioregistry.gh.new_prefix import process_new_prefix_issue
from bioregistry.schema import Author, Resource


class TestNewPrefix(unittest.TestCase):
    """Tests for new prefix pipeline."""

    @patch("bioregistry.gh.new_prefix.bioregistry.get_resource")
    def test_process_new_prefix_issue(self, mock_get_resource):
        """Tests if Resource object returned is as expected using data from an old issue."""
        mock_get_resource.return_value = None

        issue_id = 1181
        resource_data = {
            "prefix": "ncbiortholog",
            "name": "National Center for Biotechnology Information",
            "homepage": "https://www.ncbi.nlm.nih.gov/gene/",
            "repository": "n/a",
            "description": (
                "Database of one-to-one ortholog information provided by the NCBI "
                "as a subset of their Gene resource. Used for users to access ortholog "
                "information for over 1000 species of vertebrates and arthropods."
            ),
            "license": "US gov't public domain",
            "example": "2",
            "pattern": "^\\d+$",
            "uri_format": "https://www.ncbi.nlm.nih.gov/gene/$1/ortholog/",
            "contributor_name": "Terence Murphy",
            "contributor_github": "murphyte",
            "contributor_orcid": "0000-0001-9311-9745",
            "contributor_email": "murphyte@ncbi.nlm.nih.gov",
            "contact_name": "Terence Murphy",
            "contact_orcid": "0000-0001-9311-9745",
            "contact_github": "murphyte",
            "contact_email": "murphyte@ncbi.nlm.nih.gov",
            "comment": (
                "We do not currently have the source code for our ortholog resource available publicly, "
                "although we are looking at how to split it off and make it available in the next year. "
                "We are now in the process of adding this tag to the INSDC list for use in annotations, "
                "so I'd like to mirror that tag in bioregistry."
            ),
        }

        expected_resource = Resource(
            prefix="ncbiortholog",
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


if __name__ == "__main__":
    unittest.main()
