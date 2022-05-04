import bioregistry


def main():
    registry = bioregistry.read_registry()
    for prefix, resource in registry.items():
        pattern = resource.get_pattern()
        if pattern:
            continue
        example = resource.get_example()
        if not example:
            continue
        #obo_prefix = resource.get_obo_preferred_prefix()
        #if not obo_prefix:
        #    continue
        if not example.startswith("00"):
            continue
        if len(example) > 10:
            continue
        pattern = f"^\\d{{{len(example)}}}$"
        print(prefix, example, pattern)
        resource.pattern = pattern
    bioregistry.write_registry(registry)


if __name__ == '__main__':
    main()
