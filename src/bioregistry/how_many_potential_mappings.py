"""Calculate the number of possible mappings between bioregistry entries."""

from itertools import combinations
from collections import defaultdict
import bioregistry
from bioregistry.external.getters import GETTERS
from bioregistry.version import VERSION
from humanize import intword
from bioregistry import manager

def main():
    registry = bioregistry.read_registry()

    metaprefix_to_len = {
        metaprefix: len(getter())
        for metaprefix, _, getter in GETTERS
    }
    bioregistry_len = len(registry)

    bioregistry_to_metaprefix = defaultdict(set)
    metaprefix_to_bioregistry = defaultdict(set)
    for prefix, resource in registry.items():
        for metaprefix in resource.get_mappings():
            bioregistry_to_metaprefix[prefix].add(metaprefix)
            metaprefix_to_bioregistry[metaprefix].add(bioregistry)
    bioregistry_to_metaprefix = {k:len(v) for k,v in bioregistry_to_metaprefix.items()}
    metaprefix_to_bioregistry = {k:len(v) for k,v in metaprefix_to_bioregistry.items()}

    total_cross = sum(
        x * y
        for x, y in combinations(metaprefix_to_len.values(), 2)
    )
    print(f"There are {intword(total_cross)} possible mappings "
          f"between external registries (Bioregistry v{VERSION}).")

    total_cross = sum(
        min(x) ** 2
        for x in combinations(metaprefix_to_len.values(), 2)
    )
    print(f"There are {intword(total_cross)} possible one-to-one mappings "
          f"between external registries (Bioregistry v{VERSION}).")


    total_bioregistry = sum(
        min(bioregistry_len, x) ** 2
        for x in metaprefix_to_len.values()
    )
    print(f"There are {intword(total_bioregistry)} possible "
          f"mappings to the Bioregistry (v{VERSION}).")

    # TODO calculate remaining unmapped entries

    actual_total = sum(
        (count - len(manager.get_registry_invmap(metaprefix))) * (bioregistry_len - len(manager.get_registry_map(metaprefix)))
        for metaprefix, count in metaprefix_to_len.items()
    )
    print(f"There are {intword(actual_total)} realistic uncurated "
          f"mappings to the Bioregistry (v{VERSION}).")

    """
    Tweet:
    
    Worst case scenario: there are ~9M mappings between prefixes in different registries. 

    Luckily, this is a _very_ liberal estimate and the actual number is several orders of magnitude less 😄 

    Here’s how the @bioregistry calculates this number: https://gist.github.com/cthoyt/52f1af29f600075b83a19638d2fbb26c
    """




if __name__ == '__main__':
    main()
