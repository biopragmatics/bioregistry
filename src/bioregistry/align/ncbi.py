# -*- coding: utf-8 -*-

"""Align NCBI with the Bioregistry."""


from ..external.ncbi import get_ncbi
from ..utils import norm, secho, updater


@updater
def align_ncbi(registry):
    """Align NCBI references with Bioregistry."""
    ncbi_id_to_bioregistry_id = {
        entry["ncbi"]["prefix"]: key
        for key, entry in registry.items()
        if "ncbi" in entry
    }

    ncbi_registry = get_ncbi()

    ncbi_norm_prefix_to_prefix = {
        norm(ncbi_key): ncbi_key for ncbi_key in ncbi_registry
    }

    for bioregistry_id, entry in registry.items():
        if "ncbi" in entry:
            continue
        ncbi_id = ncbi_norm_prefix_to_prefix.get(norm(bioregistry_id))
        if ncbi_id is not None:
            entry["ncbi"] = {"prefix": ncbi_id}
            ncbi_id_to_bioregistry_id[ncbi_id] = bioregistry_id

    for ncbi_prefix, ncbi_entry in ncbi_registry.items():
        bioregistry_id = ncbi_id_to_bioregistry_id.get(ncbi_prefix)
        if bioregistry_id is None:
            bioregistry_id = ncbi_prefix
            registry[bioregistry_id] = {}
            secho(f"[{ncbi_prefix}] added: {ncbi_entry}", fg="green")

        registry[bioregistry_id]["ncbi"] = {"prefix": ncbi_prefix}

    return registry


if __name__ == "__main__":
    align_ncbi()
