"""Add titles and missing xrefs for publications.

Run this script with python -m bioregistry.curation.clean_publications.
"""

from functools import lru_cache
from typing import Optional

from manubot.cite.doi import get_pubmed_ids_for_doi
from manubot.cite.pubmed import get_pubmed_csl_item
from tqdm import tqdm

from bioregistry import Resource, manager
from bioregistry.schema.struct import Publication, deduplicate_publications
from bioregistry.utils import removeprefix


@lru_cache(None)
def _get_pubmed_csl_item(pmid):
    return get_pubmed_csl_item(pmid)


@lru_cache(None)
def _get_pubmed_from_doi(doi: str) -> Optional[str]:
    doi = removeprefix(doi, "https://doi.org/")
    try:
        dict = get_pubmed_ids_for_doi(doi)
    except AssertionError:
        tqdm.write(f"Expected DOI to start with 10., but got {doi}")
        return None
    if dict:
        print(dict)
        raise
    return dict.get("pmid")


def _main():
    c = 0

    dois = set()
    resources = []
    it = tqdm(manager.registry.values(), unit="resource", unit_scale=True, desc="caching PMIDs")
    for resource in it:
        resource: Resource
        it.set_postfix(prefix=resource.prefix)
        resource_publications = resource.get_publications()
        pubmed_ids = set()
        for publication in resource_publications:
            if publication.pubmed:
                pubmed_ids.add(publication.pubmed)
            elif publication.doi:
                dois.add(publication.doi)
                tqdm.write("getting pubmed from DOI")
                pmid = _get_pubmed_from_doi(publication.doi)
                if pmid:
                    pubmed_ids.add(pmid)
        if pubmed_ids:
            resources.append((resource, pubmed_ids))
        elif resource.publications:
            resource.publications = deduplicate_publications(resource.publications)

    tqdm.write(f"looked up {len(dois):,} DOIs")

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
