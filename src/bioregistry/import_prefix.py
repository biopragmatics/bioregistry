import bioregistry
from bioregistry import manager
from bioregistry.external import get_prefixcommons


def main():
    uniprot_pattern = bioregistry.get_resource("uniprot").get_pattern_re()
    pc = get_prefixcommons(force_download=True)
    prefixes = manager.get_registry_invmap("prefixcommons")
    c = 0
    for prefix, data in pc.items():
        if prefix in prefixes:
            continue

        if "_" in prefix:
            continue

        if not all(
            data.get(k)
            for k in ["name", "description", "homepage", "pattern", "example", "uri_format"]
        ):
            continue

        example = data["example"]
        if uniprot_pattern.match(example):
            continue
        uri_foramt = data['uri_format']
        if not uri_foramt.endswith("$1"):
            continue

        pubmeds = data.get("pubmed_ids")
        if not pubmeds:
            continue

        data["example_url"] = data["uri_format"].replace("$1", data["example"])

        print(data)
        c += 1
    print(c)


if __name__ == '__main__':
    main()
