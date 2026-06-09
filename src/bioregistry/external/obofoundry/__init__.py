"""Download registry information from the OBO Foundry."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

import requests
import yaml
from curies import NamedReference

from bioregistry.alignment_model import (
    Artifact,
    ArtifactType,
    License,
    Person,
    Publication,
    Record,
    Status,
    make_record,
)
from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, build_getter

__all__ = [
    "OBOFoundryAligner",
    "get_obofoundry",
    "get_obofoundry_example",
]

logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "obofoundry.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"
OBOFOUNDRY_URL = "https://raw.githubusercontent.com/OBOFoundry/OBOFoundry.github.io/master/registry/ontologies.yml"
SKIP = {
    "obo_rel": "replaced",
}


def process_obofoundry(path: Path) -> dict[str, Record]:
    """Process the OBO Foundry."""
    with path.open() as file:
        data = yaml.full_load(file)
    rv: dict[str, Record] = {
        record["id"]: _process(record) for record in data["ontologies"] if record["id"] not in SKIP
    }
    for key, record in rv.items():
        for depends_on in record.depends_on or []:
            if depends_on not in rv:
                logger.warning("issue in %s: invalid dependency: %s", key, depends_on)
            elif rv[depends_on].appears_in is not None:
                rv[depends_on].appears_in.append(key)  # type:ignore[union-attr]
            else:
                rv[depends_on].appears_in = [key]
    return rv


get_obofoundry = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=OBOFOUNDRY_URL,
    func=process_obofoundry,
)


def _get_contact(record: dict[str, Any]) -> Person | None:
    contact = record.get("contact")
    if not contact:
        return None
    github = contact.get("github")
    if github == "ghost":
        return None
    return Person.model_validate(
        {
            "email": record.get("contact", {}).get("email"),
            "name": record.get("contact", {}).get("label"),
            "github": github,
            "orcid": record.get("contact", {}).get("orcid"),
        }
    )


def _get_license(record: dict[str, Any]) -> License | None:
    ll = record.get("license")
    if not ll:
        return None

    license_name = ll.get("label")
    license_url = ll.get("url")
    if not license_name and not license_url:
        return None
    # TODO standardize SPDX
    return License(name=license_name, url=license_url)


def _process_publication(p: dict[str, Any]) -> Publication:
    d = {"title": p["title"]}
    url = p["id"]
    if url.startswith("https://www.ncbi.nlm.nih.gov/pubmed/"):
        d["pubmed"] = url.removeprefix("https://www.ncbi.nlm.nih.gov/pubmed/")
    elif url.startswith("https://doi.org/"):
        d["doi"] = url.removeprefix("https://doi.org/").lower()
    elif url.startswith("https://www.medrxiv.org/content/"):
        d["doi"] = url.removeprefix("https://www.medrxiv.org/content/").lower()
        d["medrxiv"] = url.removeprefix("https://www.medrxiv.org/content/10.1101/").lower()
    elif url.startswith("https://zenodo.org/record/"):
        d["zenodo"] = url.removeprefix("https://zenodo.org/record/")
    else:
        # TODO explicitly handle "http://ceur-ws.org/"?
        d["url"] = url
    return Publication.model_validate(d)


def _process_product(prefix: str, product: dict[str, Any]) -> Artifact | None:
    if product["id"] == f"{prefix}.obo":
        return Artifact(url=product["ontology_purl"], type=ArtifactType.obo)
    elif product["id"] == f"{prefix}.json":
        return Artifact(url=product["ontology_purl"], type=ArtifactType.obograph_json)
    elif product["id"] == f"{prefix}.owl":
        return Artifact(url=product["ontology_purl"], type=ArtifactType.owl)
    return None


def _process(record: dict[str, Any]) -> Record:
    for key in ("browsers", "usages", "build", "layout"):
        record.pop(key, None)

    prefix = record["id"].lower()
    contact = _get_contact(record)
    if record["activity_status"] == "active":
        if contact is None:
            status = Status.orphaned
        else:
            status = Status.active
    elif record["activity_status"] == "orphaned":
        status = Status.orphaned
    elif record["activity_status"] == "inactive":
        status = Status.inactive
    else:
        raise NotImplementedError(f"unhandled obo foundry status: {record['activity_status']}")

    rv = {
        "prefix": prefix,
        "name": record["title"],
        "description": record.get("description"),
        "status": status,
        "homepage": record.get("homepage"),
        "preferred_prefix": record.get("preferredPrefix") or prefix.upper(),
        "contact": contact,
        "license": _get_license(record),
        "repository": record.get("repository"),
        "domain": record.get("domain"),
        "publications": [
            _process_publication(publication) for publication in record.get("publications", [])
        ],
        "artifacts": [
            artifact
            for product_dict in record.get("products", [])
            if (artifact := _process_product(prefix, product_dict))
        ],
    }

    if taxon := record.get("taxon"):
        if taxon["id"] in {"all", "NCBITaxon:1"}:
            rv["taxon"] = NamedReference.from_curie("NCBITaxon:1", name="root")
        else:
            rv["taxon"] = NamedReference.from_curie(taxon["id"], name=taxon["label"])

    if dependencies := record.get("dependencies", []):
        rv["depends_on"] = sorted(
            dependency["id"]
            for dependency in dependencies
            if dependency.get("type") not in {"BridgeOntology"}
        )

    logo = record.get("depicted_by")
    if logo:
        if logo.startswith("/images/"):
            logo = f"https://obofoundry.org{logo}"
        rv["logo"] = logo

    return make_record(rv)


def get_obofoundry_example(prefix: str) -> str | None:
    """Get an example identifier from the OBO Library PURL configuration."""
    url = f"https://raw.githubusercontent.com/OBOFoundry/purl.obolibrary.org/master/config/{prefix}.yml"
    data = yaml.safe_load(requests.get(url, timeout=15).content)
    examples: list[str] | None = data.get("example_terms")
    if not examples:
        return None
    return examples[0].rsplit("_")[-1]


class OBOFoundryAligner(Aligner):
    """Aligner for the OBO Foundry."""

    key = "obofoundry"
    getter = get_obofoundry
    curation_header: ClassVar[Sequence[str]] = ("deprecated", "name", "description")
    include_new = True

    def get_skip(self) -> Mapping[str, str]:
        """Get the prefixes in the OBO Foundry that should be skipped."""
        return SKIP

    def _align_action(
        self, bioregistry_id: str, external_id: str, external_entry: dict[str, Any]
    ) -> None:
        super()._align_action(bioregistry_id, external_id, external_entry)
        if (
            self.manager.get_example(bioregistry_id)
            or self.manager.has_no_terms(bioregistry_id)
            or self.manager.is_deprecated(bioregistry_id)
        ):
            return
        example = get_obofoundry_example(external_id)
        if example:
            self.internal_registry[bioregistry_id]["example"] = example


if __name__ == "__main__":
    OBOFoundryAligner.cli()
