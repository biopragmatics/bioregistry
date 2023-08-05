"""Utilities."""

import itertools as itt
import logging
from collections import ChainMap, defaultdict
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

import click
import requests
from pystow.utils import get_hashes

from .constants import (
    BIOREGISTRY_PATH,
    COLLECTIONS_YAML_PATH,
    METAREGISTRY_YAML_PATH,
    REGISTRY_YAML_PATH,
)
from .version import get_version

logger = logging.getLogger(__name__)

#: Wikidata SPARQL endpoint. See https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service#Interfacing
WIKIDATA_ENDPOINT = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"


class OLSBroken(RuntimeError):
    """Raised when the OLS is having a problem."""


def secho(s, fg="cyan", bold=True, **kwargs):
    """Wrap :func:`click.secho`."""
    click.echo(
        f'[{datetime.now().strftime("%H:%M:%S")}] ' + click.style(s, fg=fg, bold=bold, **kwargs)
    )


def removeprefix(s: Optional[str], prefix: str) -> Optional[str]:
    """Remove the prefix from the string."""
    if s is None:
        return None
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


def removesuffix(s: Optional[str], suffix: str) -> Optional[str]:
    """Remove the prefix from the string."""
    if s is None:
        return None
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s


def query_wikidata(sparql: str) -> List[Mapping[str, Any]]:
    """Query Wikidata's sparql service.

    :param sparql: A SPARQL query string
    :return: A list of bindings
    """
    logger.debug("running query: %s", sparql)
    headers = {
        "User-Agent": f"bioregistry v{get_version()}",
    }
    res = requests.get(
        WIKIDATA_ENDPOINT, params={"query": sparql, "format": "json"}, headers=headers
    )
    res.raise_for_status()
    res_json = res.json()
    return res_json["results"]["bindings"]


class NormDict(dict):
    """A dictionary that supports lexical normalization of keys on setting and getting."""

    def __setitem__(self, key: str, value: str) -> None:
        """Set an item from the dictionary after lexically normalizing it."""
        norm_key = _norm(key)
        if value is None:
            raise ValueError(f"Tried to add empty value for {key}/{norm_key}")
        if norm_key in self and self[norm_key] != value:
            raise KeyError(
                f"Tried to add {norm_key}/{value} when already had {norm_key}/{self[norm_key]}"
            )
        super().__setitem__(norm_key, value)

    def __getitem__(self, item: str) -> str:
        """Get an item from the dictionary after lexically normalizing it."""
        return super().__getitem__(_norm(item))

    def __contains__(self, item) -> bool:
        """Check if an item is in the dictionary after lexically normalizing it."""
        return super().__contains__(_norm(item))

    def get(self, key: str, default=None) -> str:
        """Get an item from the dictionary after lexically normalizing it."""
        return super().get(_norm(key), default)


def _norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    rv = s.casefold().lower()
    for x in " -_./":
        rv = rv.replace(x, "")
    return rv


def norm(s: str) -> str:
    """Normalize a string for dictionary key usage."""
    rv = s.lower()
    for x in " .-":
        rv = rv.replace(x, "")
    return rv


def curie_to_str(prefix: str, identifier: str) -> str:
    """Combine a prefix and identifier into a CURIE string."""
    return f"{prefix}:{identifier}"


def get_hexdigests(alg: str = "sha256") -> Mapping[str, str]:
    """Get hex digests."""
    return {
        path.as_posix(): _get_hexdigest(path, alg=alg)
        for path in (
            BIOREGISTRY_PATH,
            REGISTRY_YAML_PATH,
            METAREGISTRY_YAML_PATH,
            COLLECTIONS_YAML_PATH,
        )
    }


def _get_hexdigest(path: Union[str, Path], alg: str = "sha256") -> str:
    hashes = get_hashes(path, [alg])
    return hashes[alg].hexdigest()


def get_ols_descendants(
    ontology: str, uri: str, *, force_download: bool = False, get_identifier=None, clean=None
) -> Mapping[str, Mapping[str, Any]]:
    """Get descendants in the OLS."""
    url = f"https://www.ebi.ac.uk/ols/api/ontologies/{ontology}/terms/{uri}/descendants?size=1000"
    res = requests.get(url)
    res.raise_for_status()
    res_json = res.json()
    try:
        terms = res_json["_embedded"]["terms"]
    except KeyError:
        raise OLSBroken from None
    return _process_ols(ontology=ontology, terms=terms, clean=clean, get_identifier=get_identifier)


def _process_ols(
    *, ontology, terms, clean=None, get_identifier=None
) -> Mapping[str, Mapping[str, Any]]:
    if clean is None:
        clean = _clean
    if get_identifier is None:
        get_identifier = _get_identifier
    rv = {}
    for term in terms:
        identifier = get_identifier(term, ontology)
        description = term.get("description")
        rv[identifier] = {
            "name": clean(term["label"]),
            "description": description and description[0],
            "obsolete": term.get("is_obsolete", False),
        }
    return rv


def _get_identifier(term, ontology: str) -> str:
    return term["obo_id"][len(ontology) + 1 :]


def _clean(s: str) -> str:
    s = cast(str, removesuffix(s, "identifier")).strip()
    s = cast(str, removesuffix(s, "ID")).strip()
    s = cast(str, removesuffix(s, "accession")).strip()
    return s


def backfill(records: Iterable[Dict[str, Any]], keys: Sequence[str]) -> Sequence[Dict[str, Any]]:
    """Backfill records that may have overlapping data."""
    _key_set = set(keys)
    index_dd: DefaultDict[str, DefaultDict[str, Dict[str, str]]] = defaultdict(
        lambda: defaultdict(dict)
    )

    # Make a copy
    records_copy = [record.copy() for record in records]

    # 1. index existing mappings
    for record in records_copy:
        pairs = ((key, value) for key, value in record.items() if key in _key_set)
        for (k1, v1), (k2, v2) in itt.combinations(pairs, 2):
            index_dd[k1][v1][k2] = v2
            index_dd[k2][v2][k1] = v1

    index = {k: dict(v) for k, v in index_dd.items()}

    for record in records_copy:
        missing_keys = {key for key in keys if key not in record}
        for _ in range(len(keys)):
            if not missing_keys:
                continue
            values = {key: record[key] for key in keys if key in record}
            for key, value in values.items():
                for xref_key, xref_value in index.get(key, {}).get(value, {}).items():
                    if xref_key in missing_keys:
                        record[xref_key] = xref_value
                        missing_keys.remove(xref_key)
    return records_copy


def deduplicate(records: Iterable[Dict[str, Any]], keys: Sequence[str]) -> Sequence[Dict[str, Any]]:
    """De-duplicate records that might have overlapping data."""
    dd: DefaultDict[Sequence[str], List[Dict[str, Any]]] = defaultdict(list)

    def _key(r: Dict[str, Any]):
        return tuple(r.get(key) or "" for key in keys)

    for record in backfill(records, keys):
        dd[_key(record)].append(record)

    rv = [dict(ChainMap(*v)) for v in dd.values()]

    return sorted(rv, key=_key, reverse=True)
