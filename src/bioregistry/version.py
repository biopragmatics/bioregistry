# -*- coding: utf-8 -*-

"""Version information for the bioregistry."""

import os
from subprocess import CalledProcessError, check_output  # noqa: S404
from typing import Optional

__all__ = [
    "VERSION",
    "get_version",
    "get_git_hash",
]

VERSION = "0.9.88"


def get_git_hash() -> Optional[str]:
    """Get the bioregistry git hash."""
    with open(os.devnull, "w") as devnull:
        try:
            ret = check_output(  # noqa: S603,S607
                ["git", "rev-parse", "HEAD"],
                cwd=os.path.dirname(__file__),
                stderr=devnull,
            )
        except OSError:  # git isn't available
            return None
        except CalledProcessError:
            return None
        else:
            return ret.strip().decode("utf-8")[:8]


def get_version(with_git_hash: bool = False):
    """Get the bioregistry version string, including a git hash."""
    return f"{VERSION}-{get_git_hash()}" if with_git_hash else VERSION


if __name__ == "__main__":
    print(get_version(with_git_hash=True))  # noqa: T201
