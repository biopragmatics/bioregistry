# -*- coding: utf-8 -*-

"""Align MIRIAM with the Bioregistry."""

from ..external.miriam import get_miriam
from ..utils import norm, secho, updater

MIRIAM_KEYS = {
    'id',
    'prefix',
    'pattern',
    'namespaceEmbeddedInLui',
    'name',
    'deprecated',
    'description',
    'sampleId',
}


@updater
def align_miriam(registry):
    """Update MIRIAM references."""
    miriam_id_to_bioregistry_id = {
        entry['miriam']['id']: key
        for key, entry in registry.items()
        if 'miriam' in entry
    }

    miriam_registry = get_miriam(mappify=True)

    miriam_prefix_to_miriam_id = {
        norm(miriam_entry['prefix']): miriam_entry['mirId'].removeprefix('MIR:')
        for miriam_entry in miriam_registry.values()
    }
    for key, entry in registry.items():
        if 'miriam' in entry:
            continue
        miriam_id = miriam_prefix_to_miriam_id.get(norm(key))
        if miriam_id is not None:
            entry['miriam'] = {'id': miriam_id}
            miriam_id_to_bioregistry_id[miriam_id] = key

    for miriam_entry in miriam_registry.values():
        miriam_entry['id'] = miriam_entry['mirId'].removeprefix('MIR:')

        # Get key by checking the miriam.id key
        bioregistry_id = miriam_id_to_bioregistry_id.get(miriam_entry['id'])
        if bioregistry_id is None:
            if miriam_entry.get('deprecated'):
                secho(f'[{miriam_entry["prefix"]}] skipping deprecated')
                continue
            bioregistry_id = miriam_entry['prefix']
            registry[bioregistry_id] = {}

        registry[bioregistry_id]['miriam'] = {
            k: v
            for k, v in miriam_entry.items()
            if k in MIRIAM_KEYS
        }

    return registry


if __name__ == '__main__':
    align_miriam()
