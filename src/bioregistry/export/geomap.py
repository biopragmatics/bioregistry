"""Create a map of where resources are curated."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import TYPE_CHECKING

import bioregistry
from bioregistry import Resource
from bioregistry.constants import MAP_SVG_PATH, MAP_TSV_PATH

if TYPE_CHECKING:
    import geopandas

URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"


def get_country_counter(resources: Iterable[Resource]) -> Counter[str]:
    """Get country counter."""
    from ror_downloader.api import get_organization_to_country

    ror_to_countries = get_organization_to_country()
    return Counter(
        str(country_code)
        for resource in resources
        for owner in resource.get_owners()
        if owner.ror
        for country_code in ror_to_countries.get(owner.ror, [])
    )


def get_df() -> geopandas.GeoDataFrame:
    """Get GeoPandas world dataframe."""
    import geopandas as gpd
    import pystow

    path = pystow.ensure("geopandas", url=URL)
    world = gpd.read_file(path)
    return world


def main() -> None:
    """Do it."""
    import matplotlib.pyplot as plt
    import pandas as pd

    counter = get_country_counter(bioregistry.resources())

    world = get_df()

    long_names = dict(world[["ISO_A2_EH", "SOVEREIGNT"]].values)

    world = world[world["ADMIN"] != "Antarctica"]

    world = world.to_crs(epsg=3395)

    # Create a column to distinguish the highlighted countries
    world["highlight"] = world["ISO_A2_EH"].apply(lambda x: 1 if counter.get(x) else 0)

    # Plot the world map
    _fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    world.boundary.plot(ax=ax, linewidth=1)  # Plot country borders
    world[world["highlight"] == 1].plot(ax=ax, color="lightgreen")

    # Add title and display the map
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(MAP_SVG_PATH)

    df = pd.DataFrame(
        [(code, long_names.get(code), count) for code, count in counter.most_common()],
        columns=["code", "name", "n_resources"],
    )
    df.to_csv(MAP_TSV_PATH, sep="\t", index=False)


if __name__ == "__main__":
    main()
