import csv
import time
from itertools import zip_longest
from xml.etree import ElementTree as ET

import requests
from more_itertools import chunked

search_terms = ["database", "ontology", "resource", "vocabulary", "nomenclature"]

base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
summary_url = base_url + "esummary.fcgi"
search_url = base_url + "esearch.fcgi"


def get_publications(search_term, reldate=365):
    # Delay to avoid rate limit
    time.sleep(1)
    params = {
        "term": search_term + "[Title]",
        "reldate": reldate,
        "retmax": 100000,
        "retstart": 0,
        "db": "pubmed",
        "sort": "pub+date",
    }
    res = requests.get(search_url, params=params)
    if not res.content:
        return {}
    tree = ET.XML(res.content)
    id_terms = tree.findall("IdList/Id")
    if id_terms is None:
        return []
    ids = [idt.text for idt in id_terms]
    count = int(tree.find("Count").text)
    if count != len(ids):
        print(
            "Not all ids were retrieved for search %s;\n"
            "limited at %d." % (search_term, params["retmax"])
        )

    pubs = {}
    for batch in chunked(ids, 200):
        params = {
            "id": ",".join([pmid for pmid in batch if pmid]),
            "retmode": "json",
            "db": "pubmed",
        }
        res = requests.get(summary_url, params=params)
        entries = res.json()["result"]
        for pmid, data in entries.items():
            if pmid == "uids":
                continue
            title = data.get("title", "")
            pubs[pmid] = {"title": title, "terms": [search_term]}
    return pubs


def main():
    all_pubs = {}
    for term in search_terms:
        pubs = get_publications(term, reldate=365)
        for pmid, data in pubs.items():
            if pmid in all_pubs:
                data["terms"] += data["terms"]
            else:
                all_pubs[pmid] = data
    with open("relevant_pubs", "w") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerows(
            [(pmid, data["title"], ",".join(data["terms"])) for pmid, data in all_pubs.items()]
        )


if __name__ == "__main__":
    main()
