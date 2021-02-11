# -*- coding: utf-8 -*-

"""Download Biolink."""

import requests
import yaml

__all__ = [
    'get_biolink',
]

URL = 'https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml'


def get_biolink():
    """Get Biolink."""
    res = requests.get(URL)
    data = yaml.safe_load(res.content)
    return {
        prefix: {'formatter': f'{url}$1'}
        for prefix, url in data['prefixes'].items()
    }


if __name__ == '__main__':
    print(get_biolink())
