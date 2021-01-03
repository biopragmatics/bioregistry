from bioregistry.utils import updater


@updater
def update_prefixes(registry):
    for key, entry in registry.items():
        pattern = entry.get('pattern')
        if pattern is None:
            continue
        if pattern.startswith('^') and pattern.endswith('$'):
            continue
        entry['pattern'] = f'^{pattern}$'

    return registry


if __name__ == '__main__':
    update_prefixes()
