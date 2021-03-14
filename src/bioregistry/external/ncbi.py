# -*- coding: utf-8 -*-

"""Download registry information from NCBI."""

import re
from typing import Dict
from urllib.parse import urlsplit, urlunsplit

import click
from bs4 import BeautifulSoup

from ..constants import BIOREGISTRY_MODULE

URL = 'https://www.ncbi.nlm.nih.gov/genbank/collab/db_xref/'
NCBI_URL_PARTS = urlsplit(URL)
DATA_TABLE_CAPTION_RE = re.compile(r'db_xref List')


def get_ncbi() -> Dict[str, Dict[str, str]]:
    """Get the NCBI data."""
    path = BIOREGISTRY_MODULE.ensure(url=URL, name='ncbi.html')
    with open(path) as f:
        soup = BeautifulSoup(f, 'html.parser')
    # find the data table based on its caption element
    data_table = soup.find('caption', string=DATA_TABLE_CAPTION_RE).parent

    rv = {}
    for row in data_table.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue

        prefix = cells[0].text.strip()
        name = cells[2].text.strip()
        if not (prefix and name):
            continue

        item = {'name': name}

        link = cells[0].find('a')
        if link and 'href' in link.attrs:
            link_href = link.attrs['href'].strip()
            if link_href:
                url_parts = urlsplit(link_href)
                if not url_parts.netloc:  # handle relative links
                    if url_parts.path.startswith('/'):  # relative to site root
                        url_parts = (
                            NCBI_URL_PARTS.scheme,
                            NCBI_URL_PARTS.netloc,
                            url_parts.path,
                            url_parts.query,
                            url_parts.fragment,
                        )
                    else:  # relative to the page we got it from
                        url_parts = (
                            NCBI_URL_PARTS.scheme,
                            NCBI_URL_PARTS.netloc,
                            NCBI_URL_PARTS.path + url_parts.path,
                            url_parts.query,
                            url_parts.fragment,
                        )
                    item['generic_urls'] = [urlunsplit(url_parts)]
                else:
                    item['generic_urls'] = [link_href]

        examples = cells[4].text.strip()
        # only bother with the first line of examples
        example = examples.split()[0]
        if example:
            # example text is like `/db_xref="FOO BAR"`
            item['example'] = example.split('=', 1)[1].strip('"')

        rv[prefix] = item

    return rv


@click.command()
def main():
    """Reload NCBI data."""
    get_ncbi()


if __name__ == '__main__':
    main()
