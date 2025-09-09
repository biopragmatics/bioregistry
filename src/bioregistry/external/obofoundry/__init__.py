"""Download registry information from the OBO Foundry."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

import requests
import yaml
from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY
from bioregistry.external.alignment_utils import Aligner, load_processed

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


def get_obofoundry(
    force_download: bool = False, force_process: bool = False
) -> dict[str, dict[str, Any]]:
    """Get the OBO Foundry registry."""
    if PROCESSED_PATH.exists() and not force_download and not force_process:
        return load_processed(PROCESSED_PATH)

    download(url=OBOFOUNDRY_URL, path=RAW_PATH, force=force_download)
    with RAW_PATH.open() as file:
        data = yaml.full_load(file)

    rv = {
        record["id"]: _process(record) for record in data["ontologies"] if record["id"] not in SKIP
    }
    for key, record in rv.items():
        for depends_on in record.get("depends_on", []):
            if depends_on not in rv:
                logger.warning("issue in %s: invalid dependency: %s", key, depends_on)
            else:
                rv[depends_on].setdefault("appears_in", []).append(key)
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True, ensure_ascii=False)

    return rv


def _process(record: dict[str, Any]) -> dict[str, Any]:
    for key in ("browsers", "usages", "build", "layout", "taxon"):
        record.pop(key, None)

    oid = record["id"].lower()

    # added to throw away placeholder contact
    contact_github = record.get("contact", {}).get("github")
    if contact_github == "ghost":
        del record["contact"]

    rv = {
        "name": record["title"],
        "description": record.get("description"),
        "deprecated": record["activity_status"] != "active",
        "homepage": record.get("homepage") or record.get("repository"),
        "preferredPrefix": record.get("preferredPrefix"),
        "license": record.get("license", {}).get("label"),
        "license.url": record.get("license", {}).get("url"),
        "contact": record.get("contact", {}).get("email"),
        "contact.label": record.get("contact", {}).get("label"),
        "contact.github": record.get("contact", {}).get("github"),
        "contact.orcid": record.get("contact", {}).get("orcid"),
        "repository": record.get("repository"),
        "domain": record.get("domain"),
    }

    for key in ("publications", "twitter"):
        value = record.get(key)
        if value:
            rv[key] = value

    dependencies = record.get("dependencies")
    if dependencies:
        rv["depends_on"] = sorted(
            dependency["id"]
            for dependency in record.get("dependencies", [])
            if dependency.get("type") not in {"BridgeOntology"}
        )

    for product in record.get("products", []):
        if product["id"] == f"{oid}.obo":
            rv["download.obo"] = product["ontology_purl"]
        elif product["id"] == f"{oid}.json":
            rv["download.json"] = product["ontology_purl"]
        elif product["id"] == f"{oid}.owl":
            rv["download.owl"] = product["ontology_purl"]

    logo = record.get("depicted_by")
    if logo:
        if logo.startswith("/images/"):
            logo = f"https://obofoundry.org{logo}"
        rv["logo"] = logo

    return {k: v for k, v in rv.items() if v is not None}


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
    normalize_invmap = True

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
