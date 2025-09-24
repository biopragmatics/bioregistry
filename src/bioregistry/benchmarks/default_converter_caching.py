"""Benchmark the benefit of caching the default converter."""

import timeit

NUMBER = 1

def main():
    print("Time to get default converter")
    print(
        timeit.timeit(
            "manager.get_converter()",
            setup="from bioregistry import manager",
            number=NUMBER,
        ),
    )

    print("Time to get cached converter")
    print(
        timeit.timeit(
            "_get_default_converter_helper(False)",
            setup="from bioregistry.parse_iri import _get_default_converter_helper; _get_default_converter_helper(True)",
            number=NUMBER,
        ),
    )

    print("Time to get cached converter (from LRU cache)")
    print(
        timeit.timeit(
            "get_default_converter()",
            setup="from bioregistry import get_default_converter; get_default_converter()",
            number=NUMBER,
        ),
    )


if __name__ == '__main__':
    main()
