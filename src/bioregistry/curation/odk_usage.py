"""Survey ODK usage on GitHub and propose new Bioregistry prefixes.

This script does the following:

1. Search GitHub for ODK configurations in order to identify repositories containing
   ontologies
2. Filter out known false positives and low quality repositories
3. Map repositories back to the Bioregistry, when possible
4. Otherwise, make stub entries in the Bioregistry for new prefixes
"""

from __future__ import annotations

import enum
from itertools import islice
from typing import Any, TypedDict, cast

import click
import pandas as pd
import pystow
import yaml
from pystow.github import MAXIMUM_SEARCH_PAGE_SIZE, get_default_branch, search_code
from pystow.utils import safe_open_dict_reader
from tqdm import tqdm

import bioregistry
from bioregistry import Author
from bioregistry.license_standardizer import standardize_license

MODULE = pystow.module("bioregistry", "odk-impact")
PATH = MODULE.join(name="results.tsv")


class Row(TypedDict):
    """A row in the ODK summary sheet."""

    repository: str
    name: str
    path: str
    version: str
    branch: str
    #: The Bioregistry prefix, mapped via the repository
    prefix: str | None
    license: str | None
    description: str | None
    contact: str | None


#: The column ordering for the ODK summary sheet
COLUMNS = [
    "prefix",
    "repository",
    "version",
    "name",
    "branch",
    "path",
    "license",
    "description",
    "contact",
]


class SkipReason(enum.Enum):
    """The reason a repository is skipped."""

    false_positive = enum.auto()
    hard_fork = enum.auto()
    training = enum.auto()
    playtime = enum.auto()
    application = enum.auto()
    in_development = enum.auto()
    low_quality = enum.auto()


#: Manually curated as irrelevant
SKIP_REPOS: dict[str, SkipReason] = {
    "fjelltopp/fjelltopp-ansible": SkipReason.false_positive,
    "commondataio/dataportals-registry": SkipReason.false_positive,
    "buildsi/error-analysis": SkipReason.false_positive,
    "joaquinpereyra98/legendary-classes-pf1e": SkipReason.false_positive,
    "Krusz-Beton/przemienniki-mapy73pl": SkipReason.false_positive,
    "denniszielke/container_demos": SkipReason.false_positive,
    "jembi/trace-odk-to-dhis2": SkipReason.false_positive,
    "NhanAZ/FunnyBlock": SkipReason.false_positive,
    "NhanAZ/SLBSER": SkipReason.false_positive,
    "gootools/token-list": SkipReason.false_positive,
    "InSilicoVida-Research-Lab/pbpko": SkipReason.false_positive,
    #
    "yasuhide0802/Eye2": SkipReason.hard_fork,  # of HP
    "vyasakhilesh/digitrubber": SkipReason.hard_fork,
    #
    "EBISPOT/ontology_editor_training": SkipReason.training,
    "pfabry/ODKDocs": SkipReason.training,
    "pfabry/ODKDocsV2": SkipReason.training,
    #
    "anitacaron/cato": SkipReason.playtime,  # test "cat" ontology
    "AgriculturalSemantics/seont_test": SkipReason.playtime,
    # see real one at https://github.com/AgriculturalSemantics/SEOnt
    #
    "cmungall/chemessence": SkipReason.application,
    "monarch-initiative/mondo-ingest": SkipReason.application,
    "monarch-initiative/phenio": SkipReason.application,
    "EBISPOT/scatlas_ontology": SkipReason.application,
    "futres/uberonfovt": SkipReason.application,
    "rsc3/biocoreterms": SkipReason.application,
    #
    "cmungall/lsfo": SkipReason.in_development,
    "StroemPhi/semunit": SkipReason.in_development,
    #
    "ASHS21/csonto": SkipReason.low_quality,
    "Mjvolk3/torchcell_ontology": SkipReason.low_quality,
    "JPReceveur/sudo_ontology": SkipReason.low_quality,
}
SKIP_REPOS_CASEFOLDED: set[str] = {k.casefold() for k in SKIP_REPOS}

SKIP_PATHS = {
    "src/ontology/rto-odk.yamlZone.Identifier",
}

#: Users who have many test ODK files
#: or other reasons to not be considered
SKIP_USERS = {
    "INCATools",
    "matentzn",
    "one-acre-fund",
    "agustincharry",  # kafka stuff
    "hboutemy",  # hboutemy/mcmm-yaml is not related
    "kirana-ks",  # kirana-ks/aether-infrastructure-provisioning is not related to ODK
    "ferjavrec",  # projects in odk-central are not related to our ODK
    "acevesp",
    "cthoyt",  # self reference
    "OBOAcademy",  # teaching material
}


@click.command()
@click.option("--per-page", type=int, default=MAXIMUM_SEARCH_PAGE_SIZE)
@click.option("--refresh", is_flag=True)
def main(per_page: int, refresh: bool) -> None:
    """Survey ODK usage and propose new Bioregistry prefixes."""
    data: dict[str, Row]
    if PATH.is_file() and not refresh:
        with safe_open_dict_reader(PATH) as reader:
            data = {record["repository"]: record for record in reader}  # type:ignore
    else:
        data = {}

    _get_rows(data=data, per_page=per_page)

    rows = sorted(data.values(), key=lambda row: row["repository"].casefold())
    df = pd.DataFrame(rows).sort_values(["prefix", "repository"])
    df = df[COLUMNS]
    click.echo(f"Writing to {PATH}")
    df.to_csv(PATH, sep="\t", index=False)


def _get_rows(*, data: dict[str, Row], per_page: int | None = None) -> None:
    repository_to_prefix = bioregistry.get_repository_to_prefix()

    skip_user_part = " ".join(f"-user:{user}" for user in SKIP_USERS)
    query = f'filename:"-odk.yaml" {skip_user_part} -is:fork'

    for item in search_code(query=query, page_size=per_page):
        name = item["name"]
        path = item["path"]
        if path in SKIP_PATHS:
            continue

        repository = item["repository"]["full_name"]
        if repository.casefold() in SKIP_REPOS_CASEFOLDED:
            continue

        branch = get_default_branch(
            item["repository"]["owner"]["login"], item["repository"]["name"]
        )

        bioregistry_prefix = repository_to_prefix.get(repository.casefold())

        odk_version = _odk_version(repository, branch) or "unknown"
        odk_config = _get_odk_configuration(repository, branch, path) or {}

        license_ = standardize_license(odk_config.get("license"))
        description = odk_config.get("description")
        if contact := odk_config.get("contact"):
            contact = contact.strip().replace(" ", "").replace("[at]", "@").replace("[.]", ".")

        if odk_config and not bioregistry_prefix:
            export_formats = odk_config.get("export_formats", [])
            internal_prefix = odk_config["id"]

            download_url_base = (
                f"https://github.com/{repository}/raw/refs/heads/{branch}/{internal_prefix}."
            )
            format_uri_base = odk_config.get("uribase", "http://purl.obolibrary.org/obo")

            try:
                rr = bioregistry.Resource(
                    prefix=internal_prefix.lower(),
                    name=odk_config["title"],
                    license=license_,
                    repository=f"https://github.com/{repository}",
                    homepage=f"https://github.com/{repository}",
                    uri_format=f"{format_uri_base}/{odk_config['id'].upper()}_$1",
                    download_obo=download_url_base + "obo" if "obo" in export_formats else None,
                    download_owl=download_url_base + "owl" if "owl" in export_formats else None,
                    download_json=download_url_base + "json" if "json" in export_formats else None,
                    contributor=Author.get_charlie(),
                    example=" ",  # needs to be filled in,
                    description=description or " ",  # needs to be filled in
                    pattern="^\\d{7}$",
                )
                bioregistry.add_resource(rr)
                bioregistry.manager.write_registry()
            except KeyError as ke:
                tqdm.write(f"Unable to add {internal_prefix} - {ke}")

        data[repository] = Row(
            repository=repository,
            name=name,
            version=odk_version,
            path=path,
            prefix=bioregistry_prefix,
            branch=branch,
            license=license_,
            description=description,
            contact=contact,
        )


def _get_odk_configuration(repository: str, branch: str, path: str) -> dict[str, Any] | None:
    odk_config_url = f"https://raw.githubusercontent.com/{repository}/{branch}/{path}"
    try:
        with MODULE.ensure_open("configuration", url=odk_config_url) as file:  # type:ignore
            odk_config = yaml.safe_load(file)
    except pystow.utils.DownloadError:
        return None
    else:
        return cast(dict[str, Any], odk_config)


def _odk_version(repository: str, branch: str) -> str | None:
    makefile_url = f"https://raw.githubusercontent.com/{repository}/{branch}/src/ontology/Makefile"
    name = repository.replace("/", "_").casefold() + ".makefile.txt"
    try:
        with MODULE.ensure_open("makefile", url=makefile_url, name=name) as file:  # type:ignore
            version_line, *_ = islice(file, 3, 4)
        version = version_line.removeprefix("# ODK Version: v").strip()
    except ValueError:
        tqdm.write(f"Could not get ODK version in https://github.com/{repository}")
        return None
    except pystow.utils.DownloadError:
        tqdm.write(f"Could not download {makefile_url}")
        return None
    else:
        return cast(str, version)


if __name__ == "__main__":
    main()
