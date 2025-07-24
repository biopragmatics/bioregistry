"""Download registry information from Identifiers.org/MIRIAMs."""

import json
from collections.abc import Sequence
from operator import itemgetter
from pathlib import Path
from typing import Any, ClassVar

from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, load_processed

__all__ = [
    "MiriamAligner",
    "get_miriam",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "miriam.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
MIRIAM_URL = "https://registry.api.identifiers.org/resolutionApi/getResolverDataset"
SKIP = {
    "merops",
    "hgnc.family",
    # Appear to be unreleased records
    "f82a1a",
    "4503",
    "6vts",
    # Appears to be a duplicate of modeldb causing URI prefix clash
    "modeldb.concept",
}
SKIP_URI_FORMATS = {
    "http://arabidopsis.org/servlets/TairObject?accession=$1",
}


def get_miriam(
    force_download: bool = False, force_process: bool = False
) -> dict[str, dict[str, Any]]:
    """Get the MIRIAM registry."""
    if PROCESSED_PATH.exists() and not force_download and not force_process:
        return load_processed(PROCESSED_PATH)

    download(url=MIRIAM_URL, path=RAW_PATH, force=force_download)
    with open(RAW_PATH) as file:
        data = json.load(file)

    data["payload"]["namespaces"] = sorted(data["payload"]["namespaces"], key=itemgetter("prefix"))
    if force_download:
        with open(RAW_PATH, "w") as file:
            json.dump(data, file, indent=2, sort_keys=True, ensure_ascii=False)

    rv = {
        record["prefix"]: _process(record)
        for record in data["payload"]["namespaces"]
        # records whose prefixes start with `dg.` appear to be unreleased
        if not record["prefix"].startswith("dg.") and record["prefix"] not in SKIP
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


#: Pairs of MIRIAM prefix and provider codes (or name, since some providers don't have codes)
PROVIDER_BLACKLIST = {
    ("ega.study", "omicsdi"),
    # see discussion at https://github.com/biopragmatics/bioregistry/pull/944
    ("bioproject", "ebi"),
    ("pmc", "ncbi"),
    ("inchi", "InChI through Chemspider"),
}


def _process(record: dict[str, Any]) -> dict[str, Any]:
    prefix = record["prefix"]
    rv = {
        "prefix": prefix,
        "id": record["mirId"][len("MIR:") :],
        "name": record["name"],
        "deprecated": record["deprecated"],
        "namespaceEmbeddedInLui": record["namespaceEmbeddedInLui"],
        "sampleId": record["sampleId"],
        "description": record["description"],
        "pattern": record["pattern"],
    }
    resources = [
        _preprocess_resource(resource)
        for resource in record.get("resources", [])
        if not resource.get("deprecated")
    ]
    if not resources:
        return rv

    has_official = any(resource["official"] for resource in resources)
    if has_official:
        primary = next(resource for resource in resources if resource["official"])
        rest = [resource for resource in resources if not resource["official"]]
    else:
        primary, *rest = resources
    rv["homepage"] = primary["homepage"]
    if URI_FORMAT_KEY in primary:
        rv[URI_FORMAT_KEY] = primary[URI_FORMAT_KEY]

    extras = []
    for provider in rest:
        code = provider["code"]
        if (
            code in SKIP_PROVIDERS
            or (prefix, code) in PROVIDER_BLACKLIST
            or (prefix, provider["name"]) in PROVIDER_BLACKLIST
        ):
            continue
        del provider["official"]
        extras.append(provider)
    if extras:
        rv["providers"] = extras
    return rv


SKIP_PROVIDERS = {
    "ols",  # handled by the Bioregistry's metaregistry
    "bptl",  # handled by the Bioregistry's metaregistry
    "bioentitylink",
}


def _preprocess_resource(resource: dict[str, Any]) -> dict[str, Any]:
    rv = {
        "official": resource["official"],
        "homepage": resource["resourceHomeUrl"],
        "code": resource["providerCode"],
        "name": resource["name"],
        "description": resource["description"],
    }
    uri_format = resource["urlPattern"].replace("{$id}", "$1")
    if uri_format not in SKIP_URI_FORMATS:
        rv[URI_FORMAT_KEY] = uri_format
    return rv


class MiriamAligner(Aligner):
    """Aligner for the MIRIAM registry."""

    key = "miriam"
    getter = get_miriam
    curation_header: ClassVar[Sequence[str]] = ("deprecated", "name", "description")
    include_new = True


if __name__ == "__main__":
    MiriamAligner.cli()
