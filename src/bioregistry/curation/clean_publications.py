"""Add titles and missing xrefs for publications.

Run this script with python -m bioregistry.curation.clean_publications.
"""

from functools import lru_cache

from manubot.cite.pubmed import get_pubmed_csl_item
from tqdm import tqdm

from bioregistry import manager
from bioregistry.schema.struct import Publication, deduplicate_publications


@lru_cache(None)
def _get_pubmed_csl_item(pmid):
    return get_pubmed_csl_item(pmid)


def _main():
    c = 0

    resources = []
    for resource in manager.registry.values():
        resource_publications = resource.get_publications()
        pubmed_ids = {p.pubmed for p in resource_publications if p.pubmed}
        if pubmed_ids:
            resources.append((resource, pubmed_ids))
        elif resource.publications:
            resource.publications = deduplicate_publications(resource.publications)

    for resource, pubmed_ids in tqdm(
        resources, desc="resources with pubmeds to update", unit="resource"
    ):
        new_publications = []
        for pubmed in pubmed_ids:
            csl_item = _get_pubmed_csl_item(pubmed)
            title = csl_item.get("title", "").strip() or None
            doi = csl_item.get("DOI") or None
            pmc = csl_item.get("PMCID") or None
            year = csl_item.get("issued", {}).get("date-parts", [[None]])[0][0]
            if not title:
                tqdm.write(f"No title available for pubmed:{pubmed} / doi:{doi} / pmc:{pmc}")
                continue
            new_publications.append(
                Publication(
                    pubmed=pubmed,
                    title=title,
                    doi=doi and doi.lower(),
                    pmc=pmc,
                    year=year,
                )
            )

        if not resource.publications and not new_publications:
            raise ValueError(f"error on {resource.prefix}")
        _pubs = [
            *(new_publications or []),
            *(resource.publications or []),
        ]
        if len(_pubs) == 1:
            resource.publications = _pubs
        else:
            resource.publications = deduplicate_publications(_pubs)

        c += 1
        if c > 7:
            # output every so often in case of failure
            manager.write_registry()
            c = 0


if __name__ == "__main__":
    _main()
