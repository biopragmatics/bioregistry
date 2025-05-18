"""Add titles and missing xrefs for publications.

Run this script with python -m bioregistry.curation.clean_publications.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from manubot.cite.doi import get_doi_csl_item
from manubot.cite.pubmed import get_pmid_for_doi, get_pubmed_csl_item
from tqdm import tqdm

from bioregistry import manager
from bioregistry.schema.struct import Publication, deduplicate_publications
from bioregistry.utils import removeprefix


@lru_cache(None)
def _get_pubmed_csl_item(pubmed_id: str) -> dict[str, Any] | None:
    try:
        return get_pubmed_csl_item(pubmed_id)  # type:ignore
    except Exception:
        return None


@lru_cache(None)
def _get_doi_csl_item(pubmed_id: str) -> dict[str, Any] | None:
    return get_doi_csl_item(pubmed_id)  # type:ignore


@lru_cache(None)
def _get_pubmed_from_doi(doi: str) -> str | None:
    tqdm.write(f"getting pubmed from DOI:{doi}")
    doi = removeprefix(doi, "https://doi.org/")
    return get_pmid_for_doi(doi)  # type:ignore


def _clean_doi(doi: str) -> str:
    doi = doi.lower()
    doi = removeprefix(doi, "https://doi.org/")
    doi = removeprefix(doi, "http://doi.org/")
    doi = removeprefix(doi, "doi:")
    return doi


def _main() -> None:
    c = 0

    resource_dois = []
    resources = []
    it = tqdm(manager.registry.values(), unit="resource", unit_scale=True, desc="caching PMIDs")
    for resource in it:
        it.set_postfix(prefix=resource.prefix)
        resource_publications = resource.get_publications()
        pubmed_ids: set[str] = set()
        dois: set[str] = set()
        for publication in resource_publications:
            if publication.pubmed:
                pubmed_ids.add(publication.pubmed)
            elif publication.doi:
                _publication_doi = _clean_doi(publication.doi)
                pubmed = _get_pubmed_from_doi(_publication_doi)
                if pubmed:
                    pubmed_ids.add(pubmed)
                else:
                    dois.add(_publication_doi)
        if pubmed_ids:
            resources.append((resource, pubmed_ids))
        if dois:
            resource_dois.append((resource, dois))
        if not pubmed_ids and not dois and resource.publications:
            resource.publications = deduplicate_publications(resource.publications)

    tqdm.write(f"looked up {len(resource_dois):,} DOIs")

    for resource, dois in tqdm(resource_dois):
        new_publications = []
        for doi in dois:
            csl_item = _get_doi_csl_item(doi)
            if not csl_item:
                continue
            title = csl_item.get("title", "").strip().rstrip(".") or None
            pubmed = csl_item.get("PMID") or None
            pmc = csl_item.get("PMCID") or None
            year = csl_item.get("issued", {}).get("date-parts", [[None]])[0][0]
            if not title:
                tqdm.write(f"No title available for pubmed:{pubmed} / doi:{doi} / pmc:{pmc}")
                continue
            new_publications.append(
                Publication(
                    pubmed=pubmed,
                    title=title,
                    doi=doi,
                    pmc=pmc,
                    year=year,
                )
            )
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

    for resource, pubmed_ids in tqdm(
        resources, desc="resources with pubmeds to update", unit="resource"
    ):
        new_publications = []
        for pubmed in pubmed_ids:
            csl_item = _get_pubmed_csl_item(pubmed)
            if not csl_item:
                continue
            title = csl_item.get("title", "").strip().rstrip(".") or None
            doi = csl_item.get("DOI") or None  # type:ignore
            if doi is not None:
                doi = _clean_doi(doi)
            pmc = csl_item.get("PMCID") or None
            year = csl_item.get("issued", {}).get("date-parts", [[None]])[0][0]
            if not title:
                tqdm.write(f"No title available for pubmed:{pubmed} / doi:{doi} / pmc:{pmc}")
                continue
            new_publications.append(
                Publication(
                    pubmed=pubmed,
                    title=title,
                    doi=doi,
                    pmc=pmc,
                    year=year,
                )
            )

        if not resource.publications and not new_publications:
            tqdm.write(f"error on {resource.prefix}")
            continue
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
