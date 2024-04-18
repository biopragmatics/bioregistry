# -*- coding: utf-8 -*-

"""Align Prefix Commons with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.prefixcommons import get_prefixcommons

__all__ = [
    "PrefixCommonsAligner",
]

SKIP = {
    "redidb": "Website is dead",
    "trnadbce": "Website is password protected",
    "pogs_plantrbp": "Website is dead",
    "smr": "no evidence of it existing",
}
PROVIDERS = {
    "homeodomain_resource": "hdr",
    "interpare": "pdb",
    "consurfdb": "pdb",
    "homstrad": "pdb",
    "jail": "pdb",
    "hotsprint": "pdb",
    "lpfc": "pdb",
    "pdbreprdb": "pdb",
    "pdtd": "pdb",
    "supersite": "pdb",
    "pairsdb": "pdb",
    "icbs": "pdb",
    "pdbbind": "pdb",
    "pdb.tm": "pdb",
    "ligasite": "pdb",
    "firedb": "pdb",
    "dali": "pdb",
    "pisite": "pdb",
    "procognate": "pdb",
    "binding_moad": "pdb",
    "bhfucl": "uniprot",
    "pdzbase": "uniprot",
    "unisave": "uniprot",
    "2dbaseecoli": "uniprot",
    "swiss2dpage": "uniprot",
    "siena2dpage": "uniprot",
    "phci2dpage": "uniprot",
    "reproduction2dpage": "uniprot",
    "agbase": "uniprot",
    "iproclass": "uniprot",
    "asap_ii": "unigene",
    "snp2nmd": "dbsnp",
    "cangem": "ensembl",
    "cisred": "ensembl",
    "interferome": "ensembl",
    "spliceinfo": "ensembl",
    "piggis": "ensembl",
    "corg": "ensembl",
    "greglist": "ensembl",
    "gxa": "ensembl",
    "cyclebase": "ensembl",
    "droid": "flybase",
    "enzyme": "eccode",
    "orenza": "eccode",
    "explorenz": "eccode",
    "fcp": "eccode",
    "mousecyc": "mgi",
    "imgt.3dstructuredb": "pdb",
    "mapu": "ipi",
    "sysbodyfluid": "ipi",
    "uniprot.taxonomy": "ncbitaxon",
    "domine": "pfam",
    "dima": "pfam",
    "interdom": "pfam",
    "sdr": "pfam",
    "ipfam": "pfam",
    "hupi": "hgnc.symbol",
    "chimerdb": "hgnc.symbol",
    "po.psds": "po",
    "cutdb": "pmap.cutdb",
    "hubmed": "pubmed",
}


class PrefixCommonsAligner(Aligner):
    """Aligner for Prefix Commons."""

    key = "prefixcommons"
    getter = get_prefixcommons
    curation_header = (
        "name",
        "synonyms",
        "description",
        "example",
        "pattern",
        "uri_format",
    )
    alt_keys_match = "synonyms"
    # TODO consider updating
    include_new = False

    def get_skip(self) -> Mapping[str, str]:
        """Get skip prefixes."""
        return {**SKIP, **PROVIDERS}

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Prefix Commons registry entries."""
        return [
            external_entry["name"],
            ", ".join(external_entry.get("synonyms", [])),
            external_entry.get("description", "").replace('"', ""),
            external_entry.get("example", ""),
            external_entry.get("pattern", ""),
            external_entry.get("uri_format", ""),
        ]


if __name__ == "__main__":
    PrefixCommonsAligner.cli()
