import tabulate

import bioregistry
import re

def main():
    registry = bioregistry.read_registry()
    rows = []
    for prefix, resource in registry.items():
        pattern = resource.get_pattern()
        if pattern:
            continue
        example = resource.get_example()
        if not example:
            continue
        if len(example) > 10:
            continue  # skip long examples
        if example.startswith("0"):
            pattern = f"^\\d{{{len(example)}}}$"
            if not re.match(pattern, example):
                print("Check", prefix)
                continue
            resource.pattern = pattern
            rows.append((prefix, example, resource.pattern))
        elif example.isnumeric():
            pattern = "^\\d+$"
            if not re.match(pattern, example):
                print("Check", prefix)
                continue
            resource.pattern = pattern
            rows.append((prefix, example, resource.pattern))

    print(tabulate.tabulate(rows, headers=["prefix", "example","pattern"]))
    bioregistry.write_registry(registry)


if __name__ == '__main__':
    main()
