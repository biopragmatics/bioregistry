from tabulate import tabulate

import bioregistry

if __name__ == "__main__":
    rows = []
    for resource in bioregistry.resources():
        if resource.is_deprecated():
            continue
        if resource.get_contact():
            continue
        publications = resource.get_publications()
        if not publications:
            continue
        url = publications[0].get_url()
        rows.append((resource.prefix, resource.get_name(), url))

    print(tabulate(rows, headers=["prefix", "name", "url"]))