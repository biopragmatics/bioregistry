from bioregistry import manager
from tqdm import tqdm
from bioregistry.constants import URI_PATH

from typing import Iterable, Tuple


def iter_uris() -> Iterable[Tuple[str, str, str, str]]:
    for prefix, resource in tqdm(manager.registry.items(), desc='Generating test URIs', unit="prefix"):
        example = resource.get_example()
        if not example:
            continue
        for metaprefix, url in manager.get_providers_list(prefix, example):
            if url.endswith(example):  # skip funny formats
                yield prefix, example, metaprefix, url
        for extra_example in resource.example_extras or []:
            for metaprefix, url in manager.get_providers_list(prefix, extra_example):
                if url.endswith(extra_example):
                    yield prefix, extra_example, metaprefix, url


def get_uris(rebuild: bool = True):
    if URI_PATH.is_file() and not rebuild:
        return [line.strip() for line in URI_PATH.read_text().splitlines()]
    uris = sorted(set(iter_uris()))
    URI_PATH.write_text("\n".join("\t".join(line) for line in uris))
    return uris


def main(rebuild: bool = True):
    uris = get_uris(rebuild=rebuild)
    print(f"using {len(uris):,} test URIs")
    print(URI_PATH)


if __name__ == '__main__':
    main()
