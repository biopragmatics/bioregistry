# -*- coding: utf-8 -*-

"""Align the Biolink with the Bioregistry."""

from typing import Any, Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.biolink import get_biolink

__all__ = [
    'BiolinkAligner',
]


class BiolinkAligner(Aligner):
    """Aligner for Biolink."""

    key = 'biolink'
    getter = get_biolink
    curation_header = ['formatter', 'identifiers', 'purl']

    def prepare_external(self, external_id, external_entry) -> Mapping[str, Any]:
        """Prepare Biolink data to be added to the Biolink for each BioPortal registry entry."""
        formatter = external_entry['formatter'].strip()
        return {
            'formatter': formatter,
            'is_identifiers': formatter.startswith('http://identifiers.org'),
            'is_obo': formatter.startswith('http://purl.obolibrary.org'),
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Biolink registry entries."""
        formatter = external_entry['formatter'].strip()
        return [
            formatter,
            formatter.startswith('http://identifiers.org'),
            formatter.startswith('http://purl.obolibrary.org'),
        ]


if __name__ == '__main__':
    BiolinkAligner.align()
