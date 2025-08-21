"""Survey ODK usage on GitHub and propose new Bioregistry prefixes.

This script does the following:

1. Search GitHub for ODK configurations in order to identify repositories containing ontologies
2. Filter out known false positives and low quality repositories
3. Map repositories back to the Bioregistry, when possible
4. Otherwise, make stub entries in the Bioregistry for new prefixes
"""

import enum
from itertools import islice
from pathlib import Path
from typing import Any, TypedDict

import click
import pandas as pd
import pystow
import requests
import yaml
from pystow.github import MAX_PER_PAGE, get_default_branch, search_code
from pystow.utils import safe_open_dict_reader
from tqdm import tqdm

import bioregistry
from bioregistry.license_standardizer import standardize_license
from bioregistry.schema.struct import CHARLIE_AUTHOR

HERE = Path(__file__).parent.resolve()
DATA = HERE.joinpath("data")
DATA.mkdir(exist_ok=True)
PATH = DATA.joinpath("00-odk.tsv")

MODULE = pystow.module("bioregistry", "odk-impact")


class Row(TypedDict):
    """A row in the ODK summary sheet."""

    repository: str
    name: str
    path: str
    version: str
    #: The Bioregistry prefix, mapped via the repository
    prefix: str | None


#: The column ordering for the ODK summary sheet
COLUMNS = ["repository", "name", "path", "version", "prefix"]


class SkipReason(enum.StrEnum):
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
    #
    "cmungall/lsfo": SkipReason.in_development,
    "StroemPhi/semunit": SkipReason.in_development,
    #
    "ASHS21/csonto": SkipReason.low_quality,
    "Mjvolk3/torchcell_ontology": SkipReason.low_quality,
    "JPReceveur/sudo_ontology": SkipReason.low_quality,
}

SKIP_PATHS = {
    "src/ontology/rto-odk.yamlZone.Identifier",
}

#: Users who have many test ODK files
#: or other reasons to not be considered
SKIP_USERS = [
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
]


@click.command()
@click.option("--per-page", type=int, default=MAX_PER_PAGE)
@click.option("--refresh", is_flag=True)
def main(per_page: int, refresh: bool) -> None:
    """Survey ODK usage and propose new Bioregistry prefixes."""
    data: dict[str, Row]
    if PATH.is_file() and not refresh:
        with safe_open_dict_reader(PATH) as reader:
            data = {record["repository"]: record for record in reader}  # type:ignore
    else:
        data = {}

    repository_to_bioregistry = get_repository_to_bioregistry()

    _get_rows(data=data, per_page=per_page, repository_to_bioregistry=repository_to_bioregistry)

    rows = sorted(data.values(), key=lambda row: row["repository"].casefold())
    df = pd.DataFrame(rows).sort_values(["prefix", "repository"])
    df = df[["prefix", "repository", "name", "version", "path"]]
    click.echo(f"Writing to {PATH}")
    df.to_csv(PATH, sep="\t", index=False)


def _get_rows(
    *,
    data: dict[str, Row],
    per_page: int | None = None,
    repository_to_bioregistry: dict[str, str],
) -> None:
    skip_user_part = " ".join(f"-user:{user}" for user in SKIP_USERS)
    skip_repo_part = " ".join(f"-repo:{repo}" for repo in SKIP_REPOS)
    query = f'filename:"-odk.yaml" {skip_user_part} {skip_repo_part} -is:fork'

    for item in search_code(query=query, per_page=per_page):
        name = item["name"]
        path = item["path"]
        if path in SKIP_PATHS:
            continue

        repository = item["repository"]["full_name"]
        if repository in SKIP_REPOS:
            continue

        branch = get_default_branch(
            item["repository"]["owner"]["login"], item["repository"]["name"]
        )

        bioregistry_prefix = repository_to_bioregistry.get(repository.casefold())

        odk_version = _odk_version(repository, branch) or "unknown"
        odk_config = _get_odk_configuration(repository, branch, path)

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
                    license=standardize_license(odk_config["license"])
                    if "license" in odk_config
                    else None,
                    repository=f"https://github.com/{repository}",
                    homepage=f"https://github.com/{repository}",
                    uri_format=f"{format_uri_base}/{odk_config['id'].upper()}_$1",
                    download_obo=download_url_base + "obo" if "obo" in export_formats else None,
                    download_owl=download_url_base + "owl" if "owl" in export_formats else None,
                    download_json=download_url_base + "json" if "json" in export_formats else None,
                    contributor=CHARLIE_AUTHOR,
                    example=" ",  # needs to be filled in,
                    description=" ",  # needs to be filled in,
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
        )


def _get_odk_configuration(repository: str, branch: str, path: str) -> dict[str, Any] | None:
    odk_config_url = f"https://raw.githubusercontent.com/{repository}/{branch}/{path}"
    try:
        with MODULE.ensure_open(url=odk_config_url) as file:
            odk_config = yaml.safe_load(file)
    except pystow.utils.DownloadError:
        return None
    else:
        return odk_config


def _odk_version(repository: str, branch: str) -> str | None:
    makefile_url = f"https://raw.githubusercontent.com/{repository}/{branch}/src/ontology/Makefile"
    try:
        line, *_ = islice(
            requests.get(makefile_url, stream=True, timeout=15).iter_lines(decode_unicode=True),
            3,
            4,
        )
        version = line.removeprefix("# ODK Version: v")
    except ValueError:
        tqdm.write(f"Could not get ODK version in https://github.com/{repository}")
        return None
    else:
        return version


def get_repository_to_bioregistry() -> dict[str, str]:
    """Get a dictionary from GitHub repository to Bioregistry prefix."""
    rv = {}
    for resource in bioregistry.resources():
        repository = resource.get_repository()
        if not repository or not repository.startswith("https://github.com/"):
            continue
        rv[repository.removeprefix("https://github.com/").casefold()] = resource.prefix
    return rv


if __name__ == "__main__":
    main()
