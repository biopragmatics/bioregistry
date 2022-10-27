# -*- coding: utf-8 -*-

"""Code for standardizing permissive licenses.

Could be extended later for non-permissive information as well as using
vocabularies like SPDX for storing synonyms.
"""

from typing import List, Mapping, Optional

__all__ = [
    "standardize_license",
    "REVERSE_LICENSES",
    "LICENSES",
]


def standardize_license(license_str: Optional[str]) -> Optional[str]:
    """Standardize a license string."""
    if license_str is None or not license_str.strip():
        return None
    license_str = license_str.strip().rstrip("/")
    if not license_str:
        return None
    return LICENSES.get(license_str, license_str)


#: https://creativecommons.org/licenses/by/3.0/
CC_BY_4 = "CC BY 4.0"
#: https://creativecommons.org/licenses/by-sa/4.0/
CC_BY_SA_4 = "CC BY-SA 4.0"
#: https://creativecommons.org/licenses/by-nd/4.0/
CC_BY_ND_4 = "CC BY-ND 4.0"
#: https://creativecommons.org/licenses/by-nc-sa/4.0/
CC_BY_NC_SA_4 = "CC BY-NC-SA 4.0"
#: http://creativecommons.org/licenses/by-nc/4.0
CC_BY_NC_4 = "CC BY-NC 4.0"

CC_BY_UNSPECIFIED = "CC-BY"
CC_BY_SA_UNSPECIFIED = "CC BY-SA"

##########################
# PUBLIC DOMAIN LICENSES #
##########################

#: https://creativecommons.org/publicdomain/zero/1.0/
CC_0 = "CC0 1.0"

#: https://creativecommons.org/publicdomain/mark/1.0/
CC_MARK = "CC_MARK"

###################
# LEGACY LICENSES #
###################

#: https://creativecommons.org/licenses/by/3.0/
CC_BY_3 = "CC BY 3.0"
#: http://creativecommons.org/licenses/by-nd/3.0
CC_BY_ND_3 = "CC BY-ND 3.0"
#: http://creativecommons.org/licenses/by-nc-sa/3.0
CC_BY_NC_SA_3 = "CC BY-NC-SA 3.0"
#: http://creativecommons.org/licenses/by-nc-nd/3.0
CC_BY_NC_ND_3 = "CC BY-NC-ND 3.0"
#: http://creativecommons.org/licenses/by-sa/3.0
CC_BY_SA_3 = "CC BY-SA 3.0"
#: http://creativecommons.org/licenses/by-nc/3.0
CC_BY_NC_3 = "CC BY-NC 3.0"

#: https://creativecommons.org/licenses/by/2.0/
CC_BY_2 = "CC BY 2.0"
#: https://creativecommons.org/licenses/by-nc-sa/2.0/
CC_BY_NC_SA_2 = "CC BY-NC-SA 2.0"

#: https://creativecommons.org/licenses/by-sa/2.0/
CC_BY_SA_2 = "CC BY-SA 2.0"

#: https://creativecommons.org/licenses/by/1.0/
CC_BY_1 = "CC BY 1.0"

#: https://opensource.org/licenses/W3C
W3C = "W3C"

CC_BY_3_IGO = "CC-BY-3.0-IGO"

#: https://creativecommons.org/licenses/by/2.5/
CC_BY_25 = "CC BY 2.5"

REVERSE_LICENSES: Mapping[Optional[str], List[str]] = {
    None: ["None", "license", "unspecified"],
    CC_BY_25: [
        "https://creativecommons.org/licenses/by/2.5/",
        "https://creativecommons.org/licenses/by/2.5/dk",
    ],
    CC_BY_3_IGO: [
        CC_BY_3_IGO,
        "https://spdx.org/licenses/CC-BY-3.0-IGO.html",
        "https://creativecommons.org/licenses/by/3.0/igo/legalcode",
        "https://creativecommons.org/licenses/by/3.0/igo",
    ],
    W3C: [
        W3C,
        "http://www.opensource.org/licenses/W3C",
    ],
    CC_BY_4: [
        "CC-BY-4.0",
        "CC-BY 4.0",
        "CC BY 4.0",  # correct
        "https://creativecommons.org/licenses/by/4.0",
        "http://creativecommons.org/licenses/by/4.0",
        "https://creativecommons.org/licenses/by/4.0/",
        "http://creativecommons.org/licenses/by/4.0/",
        "http://creativecommons.org/licenses/by/4.0/legalcode",
        "url: http://creativecommons.org/licenses/by/4.0",
        "SWO is provided under a Creative Commons Attribution 4.0 International"
        " (CC BY 4.0) license (https://creativecommons.org/licenses/by/4.0/).",
    ],
    CC_BY_3: [
        "CC-BY-3.0",
        "CC-BY 3.0",
        "CC BY 3.0",  # correct
        "http://creativecommons.org/licenses/by/3.0",
        "https://creativecommons.org/licenses/by/3.0",
        "http://creativecommons.org/licenses/by/3.0/",
        "https://creativecommons.org/licenses/by/3.0/",
        "CC-BY 3.0 https://creativecommons.org/licenses/by/3.0",
        "CC-BY version 3.0",
    ],
    CC_BY_ND_3: [
        "CC BY-ND 3.0",
        "http://creativecommons.org/licenses/by-nd/3.0",
        "https://creativecommons.org/licenses/by-nd/3.0",
    ],
    CC_BY_2: [
        "CC-BY-2.0",
        "CC-BY 2.0",
        "CC BY 2.0",  # correct
        "http://creativecommons.org/licenses/by/2.0",
        "https://creativecommons.org/licenses/by/2.0",
        "http://creativecommons.org/licenses/by/2.0/",
        "https://creativecommons.org/licenses/by/2.0/",
    ],
    CC_BY_UNSPECIFIED: [
        "CC-BY",
        "creative-commons-attribution-license",
    ],
    CC_0: [
        "CC-0",  # correct
        "CC 0",
        "CC0",
        "CC-0 1.0 Universal",
        "CC0 1.0 Universal",
        "CC0 1.0",
        "CC-0 1.0",
        "http://creativecommons.org/publicdomain/zero/1.0",
        "https://creativecommons.org/publicdomain/zero/1.0",
        "http://creativecommons.org/publicdomain/zero/1.0/",
        "https://creativecommons.org/publicdomain/zero/1.0/",
    ],
    CC_MARK: [
        "http://creativecommons.org/publicdomain/mark/1.0",
        "https://creativecommons.org/publicdomain/mark/1.0",
    ],
    CC_BY_SA_4: [
        "http://creativecommons.org/licenses/by-sa/4.0",
        "https://creativecommons.org/licenses/by-sa/4.0",
    ],
    CC_BY_SA_UNSPECIFIED: [
        "CC-BY-SA",
        "CC BY-SA",  # correct
        "CC-BY SA",
        "CC BY SA",
    ],
    CC_BY_NC_SA_2: [
        "CC-BY-NC-SA 2.0",
        "CC BY-NC-SA 2.0",  # corect
        "CC BY NC SA 2.0",
        "https://creativecommons.org/licenses/by-nc-sa/2.0",
        "http://creativecommons.org/licenses/by-nc-sa/2.0",
    ],
    CC_BY_SA_2: [
        "https://creativecommons.org/licenses/by-sa/2.0/",
    ],
    "Artistic License 2.0": [
        "Artistic License 2.0",
        "http://opensource.org/licenses/Artistic-2.0",
        "https://opensource.org/licenses/Artistic-2.0",
        "http://opensource.org/licenses/Artistic-2.0/",
        "https://opensource.org/licenses/Artistic-2.0/",
    ],
    "hpo": [
        "HPO",
        "hpo",
        "https://hpo.jax.org/app/license",
    ],
    "Apache 2.0 License": [
        "Apache 2.0 License",
        "LICENSE-2.0",
        "www.apache.org/licenses/LICENSE-2.0",
        "http://www.apache.org/licenses/LICENSE-2.0",
        "https://www.apache.org/licenses/LICENSE-2.0",
        "http://www.apache.org/licenses/LICENSE-2.0/",
        "https://www.apache.org/licenses/LICENSE-2.0/",
    ],
    "GPL-3.0": [
        "GPL-3.0",
        "GPL 3.0",
        "GNU GPL 3.0",
        "https://www.gnu.org/licenses/gpl-3.0.en.html",
        "https://www.gnu.org/licenses/gpl-3.0.en",
        "https://www.gnu.org/licenses/gpl-3.0",
    ],
    "ODBL": [
        "http://opendatacommons.org/licenses/odbl/1.0",
        "https://opendatacommons.org/licenses/odbl/1.0",
    ],
    CC_BY_NC_SA_3: [
        "CC BY-NC-SA 3.0",
        "http://creativecommons.org/licenses/by-nc-sa/3.0",
        "https://creativecommons.org/licenses/by-nc-sa/3.0",
    ],
    CC_BY_NC_SA_4: [
        CC_BY_NC_SA_4,
        "http://creativecommons.org/licenses/by-nc-sa/4.0",
        "https://creativecommons.org/licenses/by-nc-sa/4.0",
    ],
    CC_BY_SA_3: [
        CC_BY_SA_3,
        "http://creativecommons.org/licenses/by-sa/3.0",
        "https://creativecommons.org/licenses/by-sa/3.0",
    ],
    CC_BY_NC_ND_3: [
        CC_BY_SA_3,
        "http://creativecommons.org/licenses/by-nc-nd/3.0",
        "https://creativecommons.org/licenses/by-nc-nd/3.0",
    ],
    CC_BY_NC_3: [
        CC_BY_NC_3,
        "http://creativecommons.org/licenses/by-nc/3.0",
        "https://creativecommons.org/licenses/by-nc/3.0",
    ],
    CC_BY_NC_4: [
        CC_BY_NC_4,
        "http://creativecommons.org/licenses/by-nc/4.0",
        "https://creativecommons.org/licenses/by-nc/4.0",
    ],
}

LICENSES: Mapping[str, Optional[str]] = {
    _v: _k for _k, _vs in REVERSE_LICENSES.items() for _v in _vs
}
