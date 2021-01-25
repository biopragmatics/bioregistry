import datetime
import logging
from functools import lru_cache
from typing import Mapping, Optional

from bioregistry import normalize_prefix, read_bioregistry

__all__ = [
    'get_version',
    'get_versions',
]

logger = logging.getLogger(__name__)
r = read_bioregistry()


def get_version(prefix: str) -> Optional[str]:
    return get_versions().get(normalize_prefix(prefix))


@lru_cache(maxsize=1)
def get_versions() -> Mapping[str, str]:
    """Get a map of prefixes to versions"""
    rv = {}
    for bioregistry_id, bioregistry_entry in r.items():
        if 'ols' not in bioregistry_entry:
            continue
        version = bioregistry_entry['ols'].get('version')
        if version is None:
            continue

        if version != version.strip():
            logger.warning('Extra whitespace in %s', bioregistry_id)
            version = version.strip()

        version_prefix = bioregistry_entry.get('ols_version_prefix')
        if version_prefix:
            if not version.startswith(version_prefix):
                raise
            version = version[len(version_prefix):]

        if bioregistry_entry.get('ols_version_suffix_split'):
            version = version.split()[0]

        version_suffix = bioregistry_entry.get('ols_version_suffix')
        if version_suffix:
            if not version.endswith(version_suffix):
                raise
            version = version[:-len(version_suffix)]

        version_type = bioregistry_entry.get('ols_version_type')
        version_date_fmt = bioregistry_entry.get('ols_version_date_format')

        if version_date_fmt:
            if version_date_fmt in {"%Y-%d-%m"}:
                logger.warning('Confusing date format for %s (%s)', bioregistry_id, version_date_fmt)
            try:
                version = datetime.datetime.strptime(version, version_date_fmt)
            except ValueError:
                logger.warning('Wrong format for %s (%s)', bioregistry_id, version)
        elif not version_type:
            logger.warning('No type for %s (%s)', bioregistry_id, version)

        rv[bioregistry_id] = version
    return rv


if __name__ == '__main__':
    i = 0
    for k, v in get_versions().items():
        if "ols_version_date_format" not in r[k] and "ols_version_type" not in r[k]:
            i += 1
            print(k, v)
