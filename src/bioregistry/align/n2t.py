# -*- coding: utf-8 -*-

"""Align N2T with the Bioregistry."""

from ..external import get_n2t
from ..utils import norm, updater


@updater
def align_n2t(registry):
    """Update N2T references."""
    n2t_id_to_bioregistry_id = {
        entry['n2t']['prefix']: key
        for key, entry in registry.items()
        if 'n2t' in entry
    }
    n2t = get_n2t()
    n2t_norm_prefix_to_prefix = {
        norm(n2t_key): n2t_key
        for n2t_key in n2t
    }
    for bioregistry_id, entry in registry.items():
        if 'n2t' in entry:
            continue
        n2t_id = n2t_norm_prefix_to_prefix.get(norm(bioregistry_id))
        if n2t_id is not None:
            entry['n2t'] = {'prefix': n2t_id}
            n2t_id_to_bioregistry_id[n2t_id] = bioregistry_id

    for n2t_prefix, _n2t_entry in n2t.items():
        bioregistry_id = n2t_id_to_bioregistry_id.get(n2t_prefix)
        if bioregistry_id is None:
            continue
        registry[bioregistry_id]['n2t'] = {
            'prefix': n2t_prefix,
            # TODO add providers? they're not so informative though
            # 'providers': n2t_entry,
        }
        if len(_n2t_entry) == 1:
            registry[bioregistry_id]['n2t']['homepage'] = _n2t_entry[0]['homepage']
            registry[bioregistry_id]['n2t']['name'] = _n2t_entry[0]['title']

    return registry


if __name__ == '__main__':
    align_n2t()
