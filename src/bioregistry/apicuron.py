# -*- coding: utf-8 -*-

"""Upload curation statistics to APICURON.

Run this with:

.. code-block:: sh

    $ pip install -e .[apicuron]
    $ pip install apicuron-client
    $ python -m bioregistry.apicuron
"""

from functools import lru_cache
from typing import Iterable

import bioregistry

DESCRIPTION_PAYLOAD = {
    "resource_id": "bioregistry",
    "resource_uri": "bioregistry",
    "resource_name": "Bioregistry",
    "resource_url": "https://bioregistry.io",
    "resource_long_name": "Bioregistry",
    "resource_description": "The Bioregistry is an open source, community curated registry, meta-registry, and compact identifier resolver.",
    "terms_def": [
        {
            "activity_term": "prefix_submission",
            "activity_name": "Submitted a Prefix",
            "activity_category": "generation",
            "score": 20,
            "description": "Curated a novel prefix and a minimal amount of its associated metadata",
        },
        {
            "activity_term": "prefix_contribution",
            "activity_name": "Contributed to a Prefix",
            "activity_category": "generation",
            "score": 10,
            "description": "Affirmed the correctness of a predicted mapping",
        },
    ],
    "achievements_def": [
        {
            "category": "1",
            "name": "Newbie curator",
            "count_threshold": 10,
            "type": "badge",
            "list_terms": ["prefix_submission", "prefix_contribution"],
            "color_code": "#055701",
        }
    ],
}


@lru_cache(1)
def _get_description():
    from apicuron_client import Description
    return Description(**DESCRIPTION_PAYLOAD)


def get_curation_payload() -> "Submission":
    """Get curation payload dictionary for upload to APICURON."""
    from apicuron_client import Submission

    description = _get_description()
    return Submission(
        resource_uri=description.resource_uri,
        reports=list(iter_reports()),
    )


def iter_reports() -> Iterable["Report"]:
    """Generate reports from the Bioregistry for APICURON."""
    from apicuron_client import Report

    description = _get_description()
    for prefix, resource in bioregistry.read_registry().items():
        submitter = resource.contributor
        if submitter is not None and submitter.orcid is not None:
            yield Report(
                curator_orcid=submitter.orcid,
                activity_term="prefix_submission",
                resource_uri=description.resource_uri,
                entity_uri=f"https://bioregistry.io/{prefix}",
            )
        for contributor in resource.contributor_extras or []:
            if contributor.orcid is not None:
                yield Report(
                    curator_orcid=contributor.orcid,
                    activity_term="prefix_contribution",
                    resource_uri=description.resource_uri,
                    entity_uri=f"https://bioregistry.io/{prefix}",
                )


def main():
    """Submit the payload."""
    from apicuron_client import resubmit_curations, submit_description

    x = submit_description(_get_description())
    print(x)

    sub = get_curation_payload()
    res = resubmit_curations(sub)
    print(res.text)


if __name__ == "__main__":
    main()
