"""Add titles and missing xrefs for publications.

Run this script with python -m bioregistry.curation.clean_publications.
"""

from manubot.cite.pubmed import get_pubmed_csl_item
from tqdm import tqdm

from bioregistry import manager
from bioregistry.schema.struct import Publication, deduplicate_publications


def _main():
    c = 0

    resources = []
    for resource in manager.registry.values():
        if not resource.prefixcommons:
            continue
        pubmed_ids = set(resource.prefixcommons.get("pubmed_ids", []))
        if not pubmed_ids:
            continue
        pubmed_ids.difference_update(
            p.pubmed for p in resource.get_publications() if p.pubmed and p.title
        )
        if pubmed_ids:
            resources.append((resource, pubmed_ids))

    for resource, pubmed_ids in tqdm(resources):
        new_publications = []
        for pubmed in pubmed_ids:
            csl_item = get_pubmed_csl_item(pubmed)
            title = csl_item.get("title", "").strip() or None
            doi = csl_item.get("DOI") or None
            pmc = csl_item.get("PMCID") or None
            if not title:
                tqdm.write(f"No title available for pubmed:{pubmed} / doi:{doi} / pmc:{pmc}")
                continue
            new_publications.append(
                Publication(
                    pubmed=pubmed,
                    title=title,
                    doi=doi,
                    pmc=pmc,
                )
            )

        if resource.publications:
            resource.publications = deduplicate_publications(
                [
                    *new_publications,
                    *resource.publications,
                ]
            )
        else:
            resource.publications = deduplicate_publications(new_publications)

        c += 1
        if c > 5:
            # output every so often in case of failure
            manager.write_registry()
            c = 0


if __name__ == "__main__":
    _main()
