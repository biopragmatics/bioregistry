# -*- coding: utf-8 -*-

"""Test the resolution API."""

import sys
from functools import partial

import click
import requests
from tqdm import tqdm

from bioregistry import curie_to_str, manager

SLASH_URL_ENCODED = "%2F"


@click.command()
@click.option("-u", "--url", default="https://bioregistry.io", show_default=True)
@click.option("-l", "--local", is_flag=True)
def main(url: str, local: bool):
    """Test the API."""
    url = url.rstrip("/")
    if local:
        url = "http://localhost:5000"
    click.echo(f"Testing resolution API on {url}")
    failure = False
    it = tqdm(manager.registry.items())

    for prefix, resource in it:
        identifier = resource.get_example()
        if identifier is None:
            continue
        it.set_postfix({"prefix": prefix})
        req_url = f"{url}/{curie_to_str(prefix, identifier)}"
        res = requests.get(req_url, allow_redirects=False)
        log = partial(_log, req_url=req_url)
        if res.status_code == 302:  # redirect
            continue
        elif res.status_code != 404:
            text = res.text.splitlines()[3][len("<p>") : -len("</p>")]
            log(f"HTTP {res.status_code}: {res.reason} {text}", fg="red")
        elif not manager.get_providers(prefix, identifier):
            continue
        elif "/" in identifier or SLASH_URL_ENCODED in identifier:
            log("contains slash 🎩 🎸", fg="red")
        elif not manager.is_standardizable_identifier(prefix, identifier):
            pattern = resource.get_pattern()
            if resource.get_banana():
                log(f"banana {pattern} 🍌", fg="red")
            else:
                log(f"invalid example does not match pattern {pattern}", fg="red")
        else:
            log("404 unknown issue", fg="red")

        failure = True

    return sys.exit(1 if failure else 0)


def _log(s: str, req_url: str, **kwargs) -> None:
    with tqdm.external_write_mode(file=sys.stdout):
        click.secho(f"[{req_url}] {s}", **kwargs)


if __name__ == "__main__":
    main()
