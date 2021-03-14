# -*- coding: utf-8 -*-

"""Align NCBI with the Bioregistry."""

from typing import Any, Dict, List

from bioregistry.align.utils import Aligner
from bioregistry.external.ncbi import get_ncbi

__all__ = ['NcbiAligner']


class NcbiAligner(Aligner):
    """Aligner for NCBI xref registry."""

    key = 'ncbi'
    getter = get_ncbi
    curation_header = ('name', 'homepage', 'example')

    def prepare_external(
        self,
        external_id: str,
        external_entry: Dict[str, str],
    ) -> Dict[str, Any]:
        """Stub for preparing NCBI xref data to be added to the bioregistry.

        The NCBI getter does all the necessary processing, so this method is effectively an identity.

        :param external_id: the key of the entry in the incoming data
        :param external_entry: the actual entry data from the incoming data

        :returns: the processed entry data (in this case, no actual processing is done)
        """
        return external_entry

    def get_curation_row(self, external_id, external_entry) -> List[str]:
        """Return the relevant fields from an NCBI entry for pretty-printing."""
        return [
            external_entry['name'],
            external_entry.get('homepage'),
            external_entry.get('example'),
        ]


if __name__ == '__main__':
    NcbiAligner.align()
