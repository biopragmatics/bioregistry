# -*- coding: utf-8 -*-

"""Add examples from OLS."""

import random
from typing import Mapping

import requests
from tqdm import tqdm

import bioregistry


def _get_example(prefix: str, size: int = 1000):
    url = f"https://www.ebi.ac.uk/ols/api/ontologies/{prefix}/terms?page=1&size={size}"
    return _get_example_helper(prefix, url)


def _get_example_helper(prefix: str, url: str) -> str:
    if "page=50" in url:
        tqdm.write(f"[{prefix} too deep")
        raise KeyError
    tqdm.write(f"[{prefix}] getting {url}")
    res = requests.get(url).json()
    embedded = res.get("_embedded")
    if not embedded:
        tqdm.write(f"[{prefix} failure")
        tqdm.write(str(res))
        raise KeyError
    for term in embedded["terms"]:
        if term["short_form"].startswith(prefix.upper()):
            return term["short_form"]
    next_url = res["_links"]["next"]["href"]
    return _get_example_helper(prefix, next_url)


SKIP = {"afo", "dicom", "ensemblglossary", "co_321:root", "co_336", "co_359", "gexo", "hcao"}


def _get_missing_ols() -> Mapping[str, str]:
    """Get a map of prefixes to OLS prefixes that need checking."""
    return {
        prefix: bioregistry.get_ols_prefix(prefix)  # type: ignore
        for prefix, resource in bioregistry.read_registry().items()
        if (
            prefix not in SKIP
            and not bioregistry.has_no_terms(prefix)
            and resource.ols
            and not bioregistry.get_example(prefix)
        )
    }


def main():
    """Get OLS examples."""
    r = dict(bioregistry.read_registry())
    x = sorted(list(_get_missing_ols().items()))
    random.shuffle(x)
    for prefix, ols_prefix in tqdm(x[:30]):
        try:
            res = _get_example(ols_prefix, size=1000)
        except KeyError:
            continue
        if res is None:
            tqdm.write(f"no own terms in {prefix} (ols={ols_prefix})")
        else:
            tqdm.write(f"[{prefix}] got example {res}")
            if res.startswith(prefix.upper() + "_"):
                res = res[len(prefix) + 1 :]
            if res.startswith(prefix.upper() + ":"):
                res = res[len(prefix) + 1 :]
            r[prefix]["example"] = res
    bioregistry.write_registry(r)


if __name__ == "__main__":
    main()
