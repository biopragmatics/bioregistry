# -*- coding: utf-8 -*-

"""Utilities for registry alignment."""

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, Iterable, Mapping, Optional, Sequence

import click
from tabulate import tabulate

from ..constants import EXTERNAL
from ..resource_manager import Manager
from ..schema import Resource
from ..schema_utils import is_mismatch, read_metaregistry
from ..utils import norm

__all__ = [
    "Aligner",
]


class Aligner(ABC):
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

    #: Set to true if you don't want to align to deprecated resources
    skip_deprecated: ClassVar[bool] = False

    subkey: ClassVar[str] = "prefix"

    def __init__(self):
        """Instantiate the aligner."""
        if self.key not in read_metaregistry():
            raise TypeError(f"invalid metaprefix for aligner: {self.key}")

        self.manager = Manager()

        kwargs = self.getter_kwargs or {}
        kwargs.setdefault("force_download", True)
        self.external_registry = self.__class__.getter(**kwargs)
        self.skip_external = self.get_skip()

        # Get all of the pre-curated mappings from the Bioregistry
        self.external_id_to_bioregistry_id = self.manager.get_registry_invmap(self.key)

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
        for external_id, external_entry in self.external_registry.items():
            if external_id in self.skip_external:
                continue

            bioregistry_id = self.external_id_to_bioregistry_id.get(external_id)

            # try to lookup with lexical match
            if bioregistry_id is None:
                if not self.alt_key_match:
                    bioregistry_id = self.manager.normalize_prefix(external_id)
                else:
                    alt_match = external_entry.get(self.alt_key_match)
                    if alt_match:
                        bioregistry_id = self.manager.normalize_prefix(alt_match)

            # add the identifier from an external resource if it's been marked as high quality
            if bioregistry_id is None and self.include_new:
                bioregistry_id = norm(external_id)
                self.internal_registry[bioregistry_id] = Resource(prefix=bioregistry_id)

            if self._do_align_action(bioregistry_id):
                self._align_action(bioregistry_id, external_id, external_entry)

    def _do_align_action(self, prefix: Optional[str]) -> bool:
        # a match was found if the prefix is not None
        return prefix is not None and (
            not self.skip_deprecated or not self.manager.is_deprecated(prefix)
        )

    def _align_action(self, bioregistry_id, external_id, external_entry):
        # skip mismatches
        if is_mismatch(bioregistry_id, self.key, external_id):
            return

        # Add mapping
        if self.internal_registry[bioregistry_id].mappings is None:
            self.internal_registry[bioregistry_id].mappings = {}
        self.internal_registry[bioregistry_id].mappings[self.key] = external_id

        _entry = self.prepare_external(external_id, external_entry)
        _entry[self.subkey] = external_id
        self.internal_registry[bioregistry_id][self.key] = _entry
        self.external_id_to_bioregistry_id[external_id] = bioregistry_id

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
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
    def align(cls, dry: bool = False, show: bool = False):
        """Align and output the curation sheet."""
        instance = cls()
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
        def _main(dry: bool, show: bool):
            cls.align(dry=dry, show=show)

        _main()

    @abstractmethod
    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Get a sequence of items that will be ech row in the curation table.

        :param external_id: The external registry identifier
        :param external_entry: The external registry data
        :return: A sequence of cells to add to the curation table.

        .. note:: You don't need to pass the external ID. this will automatically be the first element.
        """  # noqa:DAR202

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
        rows = list(self._iter_curation_rows())
        if not rows:
            return

        directory = EXTERNAL / self.key
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "curation.tsv").open("w") as file:
            print(self.subkey, *self.curation_header, sep="\t", file=file)  # noqa:T201
            for row in rows:
                print(*row, sep="\t", file=file)  # noqa:T201

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
