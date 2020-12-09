import itertools as itt
import json
from collections import defaultdict

from bioregistry.constants import BIOREGISTRY_PATH

keys = ['obofoundry', 'miriam', 'ols', 'wikidata']


def main():
    with open(BIOREGISTRY_PATH) as file:
        registry = json.load(file)

    dd = defaultdict(set)
    for bioregistry_id, entry in registry.items():
        for external in ('obofoundry', 'miriam', 'ols'):
            if external in entry:
                dd[external].add(bioregistry_id)
        if 'wikidata_property' in entry:
            dd['wikidata'].add(bioregistry_id)

    remaining = set(registry)
    rs = defaultdict(set)
    for i in range(len(keys), 0, -1):
        for subkeys in sorted({tuple(sorted(subkeys)) for subkeys in itt.permutations(keys, i)}):
            for r in list(remaining):
                if all(r in dd[key] for key in subkeys):
                    rs[subkeys].add(r)
    rs = dict(rs)
    rs_counts = {k: len(v) for k, v in rs.items()}
    from pprint import pprint
    pprint(rs_counts)

    print('appearing in all')
    pprint(rs['miriam', 'obofoundry', 'wikidata'])

    print('\n\n just in wikidata')
    pprint(rs[('wikidata',)])




if __name__ == '__main__':
    main()
