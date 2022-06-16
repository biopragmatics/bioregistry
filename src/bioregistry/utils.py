"""Utilities."""

import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Mapping, Optional, Union

import click
import requests
from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE
from pystow.utils import get_hashes

from .constants import (
    BIOREGISTRY_PATH,
    COLLECTIONS_YAML_PATH,
    METAREGISTRY_YAML_PATH,
    REGISTRY_YAML_PATH,
)

logger = logging.getLogger(__name__)

#: Wikidata SPARQL endpoint. See https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service#Interfacing
WIKIDATA_ENDPOINT = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"


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
    res = requests.get(WIKIDATA_ENDPOINT, params={"query": sparql, "format": "json"})
    res.raise_for_status()
    res_json = res.json()
    return res_json["results"]["bindings"]


def extended_encoder(obj: Any) -> Any:
    """Encode objects similarly to :func:`pydantic.json.pydantic_encoder`."""
    if isinstance(obj, BaseModel):
        return obj.dict(exclude_none=True)
    elif is_dataclass(obj):
        return asdict(obj)

    # Check the class type and its superclasses for a matching encoder
    for base in obj.__class__.__mro__[:-1]:
        try:
            encoder = ENCODERS_BY_TYPE[base]
        except KeyError:
            continue
        return encoder(obj)
    else:  # We have exited the for loop without finding a suitable encoder
        raise TypeError(f"Object of type '{obj.__class__.__name__}' is not JSON serializable")


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
