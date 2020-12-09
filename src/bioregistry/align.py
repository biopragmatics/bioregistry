# -*- coding: utf-8 -*-

"""This outputs a dataframe listing all of the stuff missing from the metaregistry.

1. Make sure all miriam entries are represented
2. Make sure all obo foundry entries are represented
3. Make sure all OLS entries are represented
4. WikiData?
"""

import click
import requests
import requests_ftp

from .external.miriam import get_miriam_registry
from .external.obofoundry import get_obofoundry
from .external.ols import get_ols
from .utils import clean_set, norm, secho, updater

requests_ftp.monkeypatch_session()
session = requests.Session()

MIRIAM_KEYS = {
    'id',
    'prefix',
    'pattern',
    'namespaceEmbeddedInLui',
    'name',
    'deprecated',
    'description',
}
OBO_KEYS = {
    'id',
    'prefix',
    'pattern',
    'namespaceEmbeddedInLui',
    'name',
    'deprecated',
    'description',
}


def _prepare_ols(ols_entry):
    ols_id = ols_entry['ontologyId']
    config = ols_entry['config']

    license_value = config['annotations'].get('license', [None])[0]
    if license_value in {'Unspecified', 'Unspecified'}:
        license_value = None

    rv = {
        'prefix': ols_id,
        'name': config['title'],
        'download': config['fileLocation'],
        'version': config['version'],
        'version.iri': config['versionIri'],
        'description': config['description'],
        'license': license_value,
    }

    rv = {k: v for k, v in rv.items() if v}
    return rv


def _prepare_obo(obofoundry_entry):
    prefix = obofoundry_entry['id']
    rv = {
        'prefix': prefix,
        'name': obofoundry_entry['title'],
        'deprecated': obofoundry_entry.get('is_obsolete', False),
    }

    license_dict = obofoundry_entry.get('license')
    if license_dict is not None:
        rv['license'] = license_dict['label']

    contact_dict = obofoundry_entry.get('contact')
    if contact_dict is not None and contact_dict.get('email'):
        rv.update({
            'contact': contact_dict['email'],
            'contact.label': contact_dict['label'],
        })

    build = obofoundry_entry.get('build')
    if build is not None:
        method = build.get('method')
        if method is None and 'checkout in build':
            method = 'vcs'
        if method is None:
            click.echo(f'[{prefix}] missing method: {build}')
            return rv

        if method == 'vcs':
            if build['system'] != 'git':
                click.echo(f'[{prefix}] Unrecognized build system: {build["system"]}')
                return rv
            checkout = build['checkout'].replace('  ', ' ')
            if not checkout.startswith('git clone https://github.com/'):
                click.echo(f'[{prefix}] unhandled build checkout: {checkout}')
                return rv

            owner, repo = checkout.removeprefix('git clone https://github.com/').removesuffix('.git').split('/')
            rv['repo'] = f'https://github.com/{owner}/{repo}.git'

            path = build.get('path', '.')
            if path == '.':
                obo_url = f'https://raw.githubusercontent.com/{owner}/{repo}/master/{prefix}.obo'
            else:  # disregard the path since most repos don't actually use it anyway
                # TODO maybe try recovering if this doesn't work
                obo_url = f'https://raw.githubusercontent.com/{owner}/{repo}/master/{prefix}.obo'

            res = session.get(obo_url)
            if res.status_code == 200:
                rv['download.obo'] = obo_url
            else:
                click.secho(f"[{prefix}] [http {res.status_code}] see {rv['repo']} [{path}]", bold=True, fg='red')

        elif method == 'owl2obo':
            source_url = build['source_url']

            # parse repo if possible
            for url_prefix in ('https://github.com/', 'http://github.com/', 'https://raw.githubusercontent.com/'):
                if source_url.startswith(url_prefix):
                    owner, repo, *_ = source_url.removeprefix(url_prefix).split('/')
                    rv['repo'] = f'https://github.com/{owner}/{repo}.git'
                    break

            if source_url.endswith('.obo'):
                rv['download.obo'] = source_url
            elif source_url.endswith('.owl'):
                obo_url = source_url.removesuffix('.owl') + '.obo'
                res = session.get(obo_url)
                if res.status_code == 200:
                    rv['download.obo'] = source_url
                else:
                    click.secho(f'[{prefix}] [http {res.status_code}] problem with {obo_url}', bold=True, fg='red')
            else:
                click.echo(f'[{prefix}] unhandled build.source_url: {source_url}')

        elif method == 'obo2owl':
            source_url = build['source_url']
            if source_url.endswith('.obo'):
                res = session.get(source_url)
                if res.status_code == 200:
                    rv['download.obo'] = source_url
                else:
                    click.secho(f'[{prefix}] [http {res.status_code}] problem with {source_url}', bold=True, fg='red')
            else:
                click.secho(f'[{prefix}] unhandled extension {source_url}', bold=True, fg='red')
        else:
            click.echo(f'[{prefix}] unhandled build method: {method}')

    return rv


@updater
def cleanup_synonyms(registry):
    """Remove redundant synonyms and empty synonym dictionaries."""
    for key, entry in registry.items():
        if 'synonyms' not in entry:
            continue

        skip_synonyms = clean_set([
            key,
            entry.get('miriam', {}).get('name'),
            entry.get('ols', {}).get('name'),
            entry.get('obofoundry', {}).get('name'),
        ])

        entry['synonyms'] = [synonym for synonym in entry['synonyms'] if synonym not in skip_synonyms]
        if 0 == len(entry['synonyms']):
            del entry['synonyms']


@updater
def align_obofoundry(registry):
    """Update OBOFoundry references."""
    obofoundry_id_to_bioregistry_id = {
        entry['obofoundry']['prefix']: key
        for key, entry in registry.items()
        if 'obofoundry' in entry
    }
    obofoundry_registry = get_obofoundry(mappify=True)

    obofoundry_norm_prefix_to_prefix = {
        norm(obo_key): obo_key
        for obo_key in obofoundry_registry
    }
    for bioregistry_id, entry in registry.items():
        if 'obofoundry' in entry:
            continue
        obofoundry_id = obofoundry_norm_prefix_to_prefix.get(norm(bioregistry_id))
        if obofoundry_id is not None:
            entry['obofoundry'] = {'prefix': obofoundry_id}
            obofoundry_id_to_bioregistry_id[obofoundry_id] = bioregistry_id

    for obofoundry_prefix, obofoundry_entry in obofoundry_registry.items():
        # Get key by checking the miriam.id key
        bioregistry_id = obofoundry_id_to_bioregistry_id.get(obofoundry_prefix)
        if bioregistry_id is None:
            continue
        # click.echo(f'bioregistry={bioregistry_id}, obo={obofoundry_prefix}')
        registry[bioregistry_id]['obofoundry'] = _prepare_obo(obofoundry_entry)


@updater
def align_miriam(registry):
    """Update MIRIAM references."""
    miriam_id_to_bioregistry_id = {
        entry['miriam']['id']: key
        for key, entry in registry.items()
        if 'miriam' in entry
    }

    miriam_registry = get_miriam_registry(mappify=True)

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
        miriam_id = miriam_entry['mirId'].removeprefix('MIR:')

        # Get key by checking the miriam.id key
        bioregistry_id = miriam_id_to_bioregistry_id.get(miriam_id)
        if bioregistry_id is None:
            continue

        miriam_entry = {k: v for k, v in miriam_entry.items() if k in MIRIAM_KEYS}
        miriam_entry['id'] = miriam_id

        if bioregistry_id is not None:
            registry[bioregistry_id]['miriam'] = miriam_entry
        else:
            prefix = miriam_entry['prefix']
            registry[prefix] = {
                'miriam': miriam_entry,
                'synonyms': [prefix],
            }
    return registry


@updater
def align_ols(registry):
    """Update OLS references."""
    ols_id_to_bioregistry_id = {
        entry['ols']['prefix']: key
        for key, entry in registry.items()
        if 'ols' in entry
    }

    ols_registry = get_ols(mappify=True)

    ols_norm_prefix_to_prefix = {
        norm(obo_key): obo_key
        for obo_key in ols_registry
    }
    for bioregistry_id, entry in registry.items():
        if 'ols' in entry:
            continue
        ols_id = ols_norm_prefix_to_prefix.get(norm(bioregistry_id))
        if ols_id is not None:
            entry['ols'] = {'prefix': ols_id}
            ols_id_to_bioregistry_id[ols_id] = bioregistry_id

    for ols_prefix, ols_entry in ols_registry.items():
        bioregistry_id = ols_id_to_bioregistry_id.get(ols_prefix)
        if bioregistry_id is None:
            continue
        registry[bioregistry_id]['ols'] = _prepare_ols(ols_entry)


@click.command()
def align():
    """Align all external registries."""
    secho('Aligning MIRIAM')
    align_miriam()

    secho('Aligning OBO Foundry')
    align_obofoundry()

    secho('Aligning OLS')
    align_ols()


if __name__ == '__main__':
    align()
