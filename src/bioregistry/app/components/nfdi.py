"""NFDI dashboard."""

from __future__ import annotations

from collections import Counter, defaultdict

from flask import render_template

from .base import ui_blueprint
from ..proxies import manager
from ...constants import NFDI_ROR
from ...schema.struct import Collection
from ...schema_utils import get_collection_mappings

__all__ = ["show_nfdi"]


@ui_blueprint.route("/nfdi")
@ui_blueprint.route("/nfdi/")
def show_nfdi() -> str:
    """Render the NFDI dashboard page."""
    nfdi_collections = {
        c.identifier: c
        for c in manager.collections.values()
        if c.has_organization_with_ror(NFDI_ROR)
    }

    def _filter(d: dict[str, str]) -> dict[str, str]:
        return {k: v for k, v in d.items() if k in nfdi_collections}

    tib_collection_mappings = _filter(get_collection_mappings("tib.collection"))
    bartoc_collection_mappings = _filter(get_collection_mappings("bartoc"))
    collection_to_tib_opportunities = defaultdict(list)
    collection_to_license_needs_curation = defaultdict(list)
    collection_to_domain_needs_curation = defaultdict(list)
    collection_to_download_need_curation = defaultdict(list)
    tib_opportunities = set()
    for collection_ in nfdi_collections.values():
        for prefix in collection_.get_prefixes():
            if prefix == "bioregistry":
                continue
            resource_ = manager.get_resource(prefix, strict=True)
            if not resource_.get_mapped_prefix("tib") and resource_.has_download():
                collection_to_tib_opportunities[collection_.identifier].append(prefix)
                tib_opportunities.add(prefix)
            if not resource_.get_license():
                collection_to_license_needs_curation[collection_.identifier].append(resource_)
            if not resource_.domain:
                collection_to_domain_needs_curation[collection_.identifier].append(resource_)
            if not resource_.has_download():
                collection_to_download_need_curation[collection_.identifier].append(resource_)

    # who is used more than once?
    counter = Counter(prefix for c in nfdi_collections.values() for prefix in c.get_prefixes())

    # first party
    first_party = defaultdict(list)
    for collection_ in nfdi_collections.values():
        for prefix, call in manager.get_collection_first_party(
            collection_, skip_org_rors={NFDI_ROR}
        ).items():
            if call:
                first_party[prefix].append(collection_)
    first_party_list = [
        (manager.registry[prefix], consortia) for prefix, consortia in sorted(first_party.items())
    ]

    return render_template(
        "nfdi.html",
        collections=nfdi_collections,
        tib_collection_mappings=tib_collection_mappings,
        bartoc_collection_mappings=bartoc_collection_mappings,
        collection_to_tib_opportunities=collection_to_tib_opportunities,
        tib_opportunities=tib_opportunities,
        prefix_counter=counter,
        collection_to_license_needs_curation=collection_to_license_needs_curation,
        collection_to_domain_needs_curation=collection_to_domain_needs_curation,
        collection_to_download_need_curation=collection_to_download_need_curation,
        first_party=first_party_list,
        sort_collections=_sort_collections,
    )


def _sort_collections(c: list[Collection]) -> list[Collection]:
    return sorted(c, key=_collections_key, reverse=True)


def _collections_key(c: Collection) -> tuple[int, int]:
    rv = len(c.maintainers or [])
    rv += sum(
        r.startswith("https://discord") or r.startswith("https://go.rocket")
        for r in c.references or []
    )
    return rv, len(c.resources)
