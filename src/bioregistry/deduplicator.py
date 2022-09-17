import itertools as itt
import unittest
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence


def deduplicate(
    records: Sequence[Dict[str, Any]], keys: Sequence[str]
) -> List[Mapping[str, Any]]:
    _key_set = set(keys)
    index = defaultdict(lambda: defaultdict(dict))

    # 1. index existing mappings
    for record in records:
        pairs = ((key, value) for key, value in record.items() if key in _key_set)
        for (k1, v1), (k2, v2) in itt.combinations(pairs, 2):
            index[k1][v1][k2] = v2
            index[k2][v2][k1] = v1

    # 2. expand index in len(keys) steps
    for _ in range(len(keys)):

    # 3. apply index
    for _ in range(len(keys)):
        for record in records:
            missing_keys = {key for key in keys if key not in record}
            values = {key: index[key][record[key]] for key in keys if key in record}




    rv = []

    return rv


class TestDeduplicate(unittest.TestCase):
    def test_deduplicate(self):
        records = [
            {"arxiv": "arxiv_1", "doi": "doi_1"},
            {"doi": "doi_1", "pubmed": "pmid_1", "title": "yup"},
            {"pubmed": "pmid_1", "pmc": "pmc_1"},
        ]
        res = deduplicate(records, keys=["pubmed", "doi", "pmc", "arxiv"])
        self.assertEqual(
            [
                {
                    "arxiv": "arxiv_1",
                    "doi": "doi_1",
                    "pubmed": "pmid_1",
                    "title": "yup",
                    "pmc": "pmc_1",
                },
            ],
            res,
        )
