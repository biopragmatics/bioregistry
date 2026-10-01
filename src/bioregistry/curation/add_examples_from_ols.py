"""Add examples from OLS."""

from __future__ import annotations

from typing import cast

import requests
from tqdm import tqdm

import bioregistry
from bioregistry.external.ols import EBI_OLS_BASE_URL
from bioregistry.external.ols.tib import TIB_OLS_BASE_URL


def _get_example(prefix: str, *, size: int = 1000, base_url: str) -> str | None:
    url = f"{base_url}/ontologies/{prefix}/terms?page=0&size={size}"
    return _get_example_helper(prefix, url)


def _get_example_helper(prefix: str, url: str) -> str | None:
    if "page=50" in url:
        tqdm.write(f"[{prefix} too deep")
        raise KeyError
    tqdm.write(f"[{prefix}] getting {url}")
    res = requests.get(url, timeout=15).json()

    ppp = prefix.casefold() + "_"

    embedded = res.get("_embedded")
    if embedded:
        for term in embedded["terms"]:
            iri = term["iri"]
            bioregistry.parse_iri(iri)

            short_form = term["short_form"]
            if short_form.casefold().startswith(ppp):
                return cast(str, short_form[len(ppp) :])
            # else:
            #    tqdm.write(f"[{prefix}] unable to use {short_form}\n\t{term}")
        next_url = res["_links"]["next"]["href"]
        return _get_example_helper(prefix, next_url)

    page = res.get("page")
    if not page:
        raise KeyError

    if page["totalElements"] == 0:
        tqdm.write(f"no terms for {prefix}")
        return None
    raise KeyError


SKIP = {"afo", "dicom", "ensemblglossary", "co_321:root", "co_336", "co_359", "gexo", "hcao"}


def _get_missing_ols(metaprefix: str) -> dict[str, str]:
    """Get a map of prefixes to OLS prefixes that need checking."""
    return {
        prefix: external
        for prefix, external in bioregistry.get_registry_map(metaprefix).items()
        if (
            prefix not in SKIP
            and not bioregistry.has_no_terms(prefix)
            and not bioregistry.get_example(prefix)
        )
    }


def _main_helper(metaprefix: str, base_url: str) -> None:
    """Get OLS examples."""
    r = dict(bioregistry.read_registry())
    for prefix, ols_prefix in sorted(_get_missing_ols(metaprefix).items()):
        try:
            example = _get_example(ols_prefix, size=1000, base_url=base_url)
        except KeyError:
            continue
        if example is None:
            tqdm.write(f"no own terms in {prefix} (ols={ols_prefix})")
        else:
            tqdm.write(f"[{prefix}] got example {example}")
            if example.startswith(prefix.upper() + "_"):
                example = example[len(prefix) + 1 :]
            if example.startswith(prefix.upper() + ":"):
                example = example[len(prefix) + 1 :]
            r[prefix]["example"] = example
            bioregistry.write_registry(r)


def main() -> None:
    """Add examples from OLS instances."""
    _main_helper("ols", EBI_OLS_BASE_URL)
    _main_helper("tib", TIB_OLS_BASE_URL)


if __name__ == "__main__":
    main()
