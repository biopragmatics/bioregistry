# -*- coding: utf-8 -*-

"""Utilities for registry alignment."""

import csv
from typing import Any, Callable, ClassVar, Dict, Iterable, Mapping, Optional, Sequence

import click
from tabulate import tabulate

from ..constants import EXTERNAL
from ..resource_manager import Manager
from ..schema import Resource
from ..schema_utils import is_mismatch
from ..utils import norm

__all__ = [
    "Aligner",
]


class Aligner:
    """A class for aligning new registries."""

    #: The key for the external registry
    key: ClassVar[str]

    #: Header to put on the curation table, corresponding to ``get_curation_row()``
    curation_header: ClassVar[Sequence[str]]

    #: The function that gets the external registry as a dictionary from the string identifier to
    #: the entries (could be anything, but a dictionary is probably best)
    getter: ClassVar[Callable[..., Mapping[str, Any]]]

    #: Keyword arguments to pass to the getter function on call
    getter_kwargs: ClassVar[Optional[Mapping[str, Any]]] = None

    #: Should new entries be included automatically? Only set this true for aligners of
    #: very high confidence (e.g., OBO Foundry but not BioPortal)
    include_new: ClassVar[bool] = False

    #: Set this if there's another part of the data besides the ID that should be matched
    alt_key_match: ClassVar[Optional[str]] = None

    alt_keys_match: ClassVar[Optional[str]] = None

    #: Set to true if you don't want to align to deprecated resources
    skip_deprecated: ClassVar[bool] = False

    subkey: ClassVar[str] = "prefix"

    normalize_invmap: ClassVar[bool] = False

    def __init__(self, force_download: Optional[bool] = None):
        """Instantiate the aligner."""
        if not hasattr(self.__class__, "key"):
            raise TypeError
        if not hasattr(self.__class__, "curation_header"):
            raise TypeError

        self.manager = Manager()

        if self.key not in self.manager.metaregistry:
            raise TypeError(f"invalid metaprefix for aligner: {self.key}")

        kwargs = dict(self.getter_kwargs or {})
        kwargs.setdefault("force_download", True)
        if force_download is not None:
            kwargs["force_download"] = force_download
        self.external_registry = self.__class__.getter(**kwargs)
        self.skip_external = self.get_skip()

        # Get all of the pre-curated mappings from the Bioregistry
        self.external_id_to_bioregistry_id = self.manager.get_registry_invmap(
            self.key,
            normalize=self.normalize_invmap,
        )

        # Run lexical alignment
        self._align()

    @property
    def internal_registry(self) -> Dict[str, Resource]:
        """Get the internal registry."""
        return self.manager.registry

    def get_skip(self) -> Mapping[str, str]:
        """Get the mapping prefixes that should be skipped to their reasons (strings)."""
        return {}

    def _align(self):
        """Align the external registry."""
        for external_id, external_entry in sorted(self.external_registry.items()):
            if external_id in self.skip_external:
                continue

            bioregistry_id = self.external_id_to_bioregistry_id.get(external_id)
            # There's already a mapping for this external ID to a bioregistry
            # entry. Just add all of the latest metadata and move on
            if bioregistry_id is not None:
                self._align_action(bioregistry_id, external_id, external_entry)
                continue

            # try to lookup with lexical match
            if not self.alt_key_match:
                bioregistry_id = self.manager.normalize_prefix(external_id)
            else:
                alt_match = external_entry.get(self.alt_key_match)
                if alt_match:
                    bioregistry_id = self.manager.normalize_prefix(alt_match)

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
                if is_mismatch(bioregistry_id, self.key, external_id):
                    continue
                self.internal_registry[bioregistry_id] = Resource(prefix=bioregistry_id)
                self._align_action(bioregistry_id, external_id, external_entry)
                continue

    def _align_action(
        self, bioregistry_id: str, external_id: str, external_entry: Dict[str, Any]
    ) -> None:
        if self.internal_registry[bioregistry_id].mappings is None:
            self.internal_registry[bioregistry_id].mappings = {}
        self.internal_registry[bioregistry_id].mappings[self.key] = external_id  # type:ignore

        _entry = self.prepare_external(external_id, external_entry)
        _entry[self.subkey] = external_id
        self.internal_registry[bioregistry_id][self.key] = _entry
        self.external_id_to_bioregistry_id[external_id] = bioregistry_id

    def prepare_external(self, external_id: str, external_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a dictionary to be added to the bioregistry for each external registry entry.

        The default implementation returns `external_entry` unchanged.
        If you need more than that, override this method.

        :param external_id: The external registry identifier
        :param external_entry: The external registry data
        :return: The dictionary to be added to the bioregistry for the aligned entry
        """
        return external_entry

    def write_registry(self) -> None:
        """Write the internal registry."""
        self.manager.write_registry()

    @classmethod
    def align(
        cls,
        dry: bool = False,
        show: bool = False,
        force_download: Optional[bool] = None,
    ):
        """Align and output the curation sheet."""
        instance = cls(force_download=force_download)
        if not dry:
            instance.write_registry()
        if show:
            instance.print_curation_table()
        instance.write_curation_table()

    @classmethod
    def cli(cls):
        """Construct a CLI for the aligner."""

        @click.command()
        @click.option("--dry", is_flag=True)
        @click.option("--show", is_flag=True)
        @click.option("--no-force", is_flag=True)
        def _main(dry: bool, show: bool, no_force: bool):
            cls.align(dry=dry, show=show, force_download=not no_force)

        _main()

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Get a sequence of items that will be ech row in the curation table.

        :param external_id: The external registry identifier
        :param external_entry: The external registry data
        :return: A sequence of cells to add to the curation table.
        :raises TypeError: If an invalid value is encountered

        The default implementation of this function iterates over all of the keys
        in the class variable :data:`curation_header` and looks inside each record
        for those in order.

        .. note:: You don't need to pass the external ID. this will automatically be the first element.
        """  # noqa:DAR202
        rv = []
        for k in self.curation_header:
            value = external_entry.get(k)
            if value is None:
                rv.append("")
            elif isinstance(value, str):
                rv.append(value.strip())
            elif isinstance(value, (list, tuple, set)):
                rv.append("|".join(sorted(v.strip() for v in value)))
            else:
                raise TypeError
        return rv

    def _iter_curation_rows(self) -> Iterable[Sequence[str]]:
        for external_id, external_entry in sorted(
            self.external_registry.items(), key=lambda s: s[0].casefold()
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
        path = EXTERNAL.joinpath(self.key, "curation.tsv")
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

    def get_curation_table(self, **kwargs) -> Optional[str]:
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

    def print_curation_table(self, **kwargs) -> None:
        """Print the curation table."""
        s = self.get_curation_table(**kwargs)
        if s:
            print(s)  # noqa:T201
