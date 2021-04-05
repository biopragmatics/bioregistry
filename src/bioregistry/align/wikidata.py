# -*- coding: utf-8 -*-

"""Align Wikidata with the Bioregistry."""

from bioregistry.utils import query_wikidata, updater


@updater
def align_wikidata(registry):
    """Update Wikidata references."""
    properties = {}
    for bioregistry_id, v in registry.items():
        wikidata_property = v.get('wikidata', {}).get('property')
        if wikidata_property is not None:
            properties[wikidata_property] = bioregistry_id

    query = f'''
    SELECT
      ?prop ?propLabel ?format ?pattern ?homepage ?database ?databaseLabel
    WHERE
    {{
        OPTIONAL {{ ?prop wdt:P1921 ?format }}
        OPTIONAL {{ ?prop wdt:P1793 ?pattern }}
        OPTIONAL {{ ?prop wdt:P1896 ?homepage }}
        OPTIONAL {{ ?prop wdt:P1629 ?database }}
        VALUES ?prop {{{' '.join(set(f'wd:{p}' for p in properties))}}}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    '''

    for entry in query_wikidata(query):
        entry = {k: v['value'] for k, v in entry.items()}
        if 'database' in entry:
            entry['database'] = entry.pop('database').removeprefix('http://www.wikidata.org/entity/')
        if 'databaseLabel' in entry:
            entry['database.label'] = entry.pop('databaseLabel')
        entry['property.label'] = entry.pop('propLabel')
        bioregistry_id = properties[entry.pop('prop').removeprefix('http://www.wikidata.org/entity/')]
        registry[bioregistry_id]['wikidata'].update(entry)

    return registry


if __name__ == '__main__':
    align_wikidata()
