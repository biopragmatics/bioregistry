"""Align the EcoPortal with the Bioregistry."""

from .bioportal import EcoPortalAligner

if __name__ == "__main__":
    EcoPortalAligner.cli()
