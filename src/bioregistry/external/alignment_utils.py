"""Utilities for registry alignment."""

import csv
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, ParamSpec, TypeAlias

import click
from curies.w3c import NCNAME_RE
from pystow.utils import download
from tabulate import tabulate

from ..alignment_model import Record, dump_records
from ..alignment_model import load_processed as load_records
from ..constants import METADATA_CURATION_DIRECTORY
from ..resource_manager import Manager
from ..schema import Resource
from ..schema_utils import is_mismatch
from ..utils import norm

__all__ = [
    "Aligner",
    "Getter",
    "adapter",
    "build_getter",
    "build_no_raw_getter",
    "load_processed",
]

GetterRt: TypeAlias = Mapping[str, Any]

Getter: TypeAlias = Callable[..., GetterRt]


class Aligner:
    """A class for aligning new registries."""

    #: The key for the external registry
    key: ClassVar[str]

    #: Header to put on the curation table, corresponding to ``get_curation_row()``
    curation_header: ClassVar[Sequence[str]] = (
        "name",
        "homepage",
        "description",
        "uri_format",
        "examples",
    )

    #: The function that gets the external registry as a dictionary from the string identifier to
    #: the entries (could be anything, but a dictionary is probably best)
    getter: ClassVar[Getter]

    #: Keyword arguments to pass to the getter function on call
    getter_kwargs: ClassVar[Mapping[str, Any] | None] = None

    #: Should new entries be included automatically? Only set this true for aligners of
    #: very high confidence (e.g., OBO Foundry but not BioPortal)
    include_new: ClassVar[bool] = False

    #: Set this if there's another part of the data besides the ID that should be matched
    alt_key_match: ClassVar[str | None] = None

    alt_keys_match: ClassVar[str | None] = None

    #: Set to true if you don't want to align to deprecated resources
    skip_deprecated: ClassVar[bool] = False

    subkey: ClassVar[str] = "prefix"

    def __init__(
        self,
        *,
        force_download: bool | None = None,
        force_process: bool | None = None,
        manager: Manager | None = None,
    ) -> None:
        """Instantiate the aligner."""
        if not hasattr(self.__class__, "key"):
            raise TypeError
        if not hasattr(self.__class__, "curation_header"):
            raise TypeError

        self.manager = Manager() if manager is None else manager

        if self.key not in self.manager.metaregistry:
            raise TypeError(f"invalid metaprefix for aligner: {self.key}")

        kwargs = dict(self.getter_kwargs or {})
        kwargs.setdefault("force_download", True)
        if force_download is not None:
            kwargs["force_download"] = force_download
        if force_process is not None:
            kwargs["force_process"] = force_process
        self.external_registry = self.__class__.getter(**kwargs)
        self.skip_external = self.get_skip()

        self.provided_by_to_bioregistry = {
            external_prefix: internal_prefix
            for internal_prefix, xx in self.manager.provided_by_mappings.items()
            for external_prefix in xx.get(self.key, [])
        }

        # Get the pre-curated mappings from the Bioregistry
        self.external_id_to_bioregistry_id = self.manager.get_registry_invmap(self.key)

        # Run lexical alignment
        self._align()

    @property
    def internal_registry(self) -> dict[str, Resource]:
        """Get the internal registry."""
        return self.manager.registry

    def get_skip(self) -> Mapping[str, str]:
        """Get the mapping prefixes that should be skipped to their reasons (strings)."""
        return {}

    def _align(self) -> None:
        """Align the external registry."""
        for external_id, external_entry in sorted(self.external_registry.items()):
            if external_id in self.skip_external:
                continue

            if external_id in self.provided_by_to_bioregistry:
                continue  # TODO implement alignment logic!

            bioregistry_id = self.external_id_to_bioregistry_id.get(external_id)
            # There's already a mapping for this external ID to a bioregistry
            # entry. Just add all the latest metadata and move on
            if bioregistry_id is not None:
                self._align_action(bioregistry_id, external_id, external_entry)
                continue

            # try to lookup with lexical match
            if not self.alt_key_match:
                bioregistry_id = self.manager.normalize_prefix(external_id)
            else:
                alt_match = external_entry.get(self.alt_key_match)
                if alt_match is None:
                    pass
                elif isinstance(alt_match, str):
                    bioregistry_id = self.manager.normalize_prefix(alt_match)
                elif isinstance(alt_match, list):
                    bioregistry_id = None
                    for mm in alt_match:
                        bioregistry_id = self.manager.normalize_prefix(mm)
                        if bioregistry_id is not None:
                            break
                else:
                    raise TypeError(
                        f"alt_match {self.alt_key_match} has unsupported type {type(alt_match)}"
                    )

            if bioregistry_id is None and self.alt_keys_match:
                for alt_match in external_entry.get(self.alt_keys_match, []):
                    bioregistry_id = self.manager.normalize_prefix(alt_match)
                    if bioregistry_id:
                        break

            # A lexical match was possible
            if bioregistry_id is not None:
                # check this external ID for curated mismatches, and move
                # on if one has already been curated
                if is_mismatch(bioregistry_id, self.key, external_id):
                    continue
                if self.skip_deprecated and self.manager.is_deprecated(bioregistry_id):
                    continue
                self._align_action(bioregistry_id, external_id, external_entry)
                continue

            # add the identifier from an external resource if it's been marked as high quality
            elif self.include_new:
                bioregistry_id = norm(external_id)
                if not NCNAME_RE.match(bioregistry_id):
                    if NCNAME_RE.match("_" + bioregistry_id):
                        # The prefix is non-conformant to W3C, but if we prepend
                        # an underscore, it is. This happens for prefixes that start
                        # with numbers.
                        bioregistry_id = "_" + bioregistry_id
                    else:
                        # The prefix is non-conformant to W3C, therefore we can't
                        # add it safely without manual intervention
                        continue
                if is_mismatch(bioregistry_id, self.key, external_id):
                    continue
                self.internal_registry[bioregistry_id] = Resource(prefix=bioregistry_id)
                self._align_action(bioregistry_id, external_id, external_entry)
                continue

    def _align_action(
        self, bioregistry_id: str, external_id: str, external_entry: dict[str, Any]
    ) -> None:
        if self.internal_registry[bioregistry_id].mappings is None:
            self.internal_registry[bioregistry_id].mappings = {}
        self.internal_registry[bioregistry_id].mappings[self.key] = external_id  # type:ignore

        external_entry[self.subkey] = external_id
        self.internal_registry[bioregistry_id][self.key] = external_entry
        self.external_id_to_bioregistry_id[external_id] = bioregistry_id

    def write_registry(self) -> None:
        """Write the internal registry."""
        self.manager.write_registry()

    @classmethod
    def align(
        cls,
        dry: bool = False,
        show: bool = False,
        force_download: bool | None = None,
        force_process: bool | None = None,
    ) -> None:
        """Align and output the curation sheet.

        :param dry: If true, don't write changes to the registry
        :param show: If true, print a curation table
        :param force_download: Force re-download of the data
        """
        instance = cls(force_download=force_download, force_process=force_process)
        if not dry:
            instance.write_registry()
        if show:
            instance.print_curation_table()
        instance.write_curation_table()

    @classmethod
    def cli(cls, *args: Any, **kwargs: Any) -> None:
        """Construct a CLI for the aligner."""

        @click.command(help=f"Align {cls.key}")
        @click.option("--dry", is_flag=True, help="if set, don't write changes to the registry")
        @click.option("--show", is_flag=True, help="if set, print a curation table")
        @click.option(
            "--no-force", is_flag=True, help="if set, do not force re-downloading the data"
        )
        def _main(dry: bool, show: bool, no_force: bool) -> None:
            cls.align(dry=dry, show=show, force_download=not no_force)

        _main(*args, **kwargs)

    def get_curation_row(self, external_id: str, external_entry: dict[str, Any]) -> Sequence[str]:
        """Get a sequence of items that will be ech row in the curation table.

        :param external_id: The external registry identifier
        :param external_entry: The external registry data

        :returns: A sequence of cells to add to the curation table.

        :raises TypeError: If an invalid value is encountered

        The default implementation of this function iterates over all of the keys in the
        class variable :data:`curation_header` and looks inside each record for those in
        order.

        .. note::

            You don't need to pass the external ID. this will automatically be the first
            element.
        """
        rv = []
        for k in self.curation_header:
            value = external_entry.get(k)
            if value is None:
                rv.append("")
            elif isinstance(value, str):
                rv.append(value.strip().replace("\n", " ").replace("  ", " "))
            elif isinstance(value, bool):
                rv.append("true" if value else "false")
            elif isinstance(value, list | tuple | set):
                rv.append("|".join(sorted(v.strip() for v in value)))
            else:
                raise TypeError(f"unexpected type in curation header: {value}")
        return rv

    def _iter_curation_rows(self) -> Iterable[Sequence[str]]:
        for external_id, external_entry in sorted(
            self.external_registry.items(), key=lambda s: (s[0].casefold(), s[0])
        ):
            if external_id in self.skip_external:
                continue

            bioregistry_id = self.external_id_to_bioregistry_id.get(external_id)
            if bioregistry_id is None:
                yield (
                    external_id,
                    *self.get_curation_row(external_id, external_entry),
                )

    def write_curation_table(self) -> None:
        """Write the curation table to a TSV."""
        path = METADATA_CURATION_DIRECTORY.joinpath(self.key).with_suffix(".tsv")
        rows = list(self._iter_curation_rows())
        if not rows:
            if path.is_file():
                path.unlink()
            return

        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as file:
            writer = csv.writer(file, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            writer.writerow((self.subkey, *self.curation_header))
            writer.writerows(rows)

    def get_curation_table(self, **kwargs: Any) -> str | None:
        """Get the curation table as a string, built by :mod:`tabulate`."""
        kwargs.setdefault("tablefmt", "rst")
        headers = (self.subkey, *self.curation_header)
        rows = list(self._iter_curation_rows())
        if not rows:
            return None
        return tabulate(
            rows,
            headers=headers,
            **kwargs,
        )

    def print_curation_table(self, **kwargs: Any) -> None:
        """Print the curation table."""
        s = self.get_curation_table(**kwargs)
        if s:
            print(s)  # noqa:T201


def load_processed(path: Path) -> dict[str, dict[str, Any]]:
    """Load a processed."""
    with path.open() as file:
        return json.load(file)  # type:ignore


P = ParamSpec("P")


def adapter(f: Callable[P, dict[str, Record]]) -> Getter:
    """Adapt a new-style getter."""

    def _getter(*args: P.args, **kwargs: P.kwargs) -> GetterRt:
        r = f(*args, **kwargs)
        return {
            prefix: model.model_dump(exclude_unset=True, exclude_none=True, exclude_defaults=True)
            for prefix, model in r.items()
        }

    _getter.__new_style_bioregistry = True  # type:ignore[attr-defined]
    return _getter


def cleanup_json(path: Path) -> None:
    """Clean up a processed JSON file."""
    with path.open() as file:
        data = json.load(file)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def build_getter(
    *,
    processed_path: Path,
    raw_path: Path,
    url: str | Callable[[], str],
    func: Callable[[Path], dict[str, Record]],
    cleanup: Callable[[Path], None] | None = None,
) -> Getter:
    """Construct a getter function."""

    @adapter
    def getter(*, force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
        """Get the registry."""
        if processed_path.exists() and not force_download and not force_process:
            return load_records(processed_path)
        download(
            url=url if isinstance(url, str) else url(),
            path=raw_path,
            force=force_download,
        )
        if cleanup is not None:
            cleanup(raw_path)
        rv = func(raw_path)
        dump_records(rv, processed_path)
        return rv

    return getter


def build_no_raw_getter(
    *,
    processed_path: Path,
    func: Callable[[], dict[str, Record]],
) -> Getter:
    """Construct a getter function."""

    @adapter
    def getter(*, force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
        """Get the registry."""
        if processed_path.exists() and not force_download and not force_process:
            return load_records(processed_path)
        rv = func()
        dump_records(rv, processed_path)
        return rv

    return getter
