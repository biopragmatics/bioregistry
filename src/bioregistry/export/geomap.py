"""Create a map of where resources are curated."""

from collections import Counter
from collections.abc import Iterable

import bioregistry
from bioregistry import Resource
from bioregistry.constants import EXPORT_DIRECTORY


def get_country_counter(resources: Iterable[Resource]) -> Counter[str]:
    """Get country counter."""
    from ror_downloader.api import get_organization_to_country

    ror_to_countries = get_organization_to_country()
    return Counter(
        country_code
        for resource in resources
        for owner in resource.get_owners()
        if owner.ror
        for country_code in ror_to_countries.get(owner.ror, [])
    )


def main() -> None:
    """Do it."""
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import pandas as pd
    import pystow

    counter = get_country_counter(bioregistry.resources())

    pystow.ensure(
        "isb",
        url="https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip",
    )
    path = pystow.join("isb", "ne_110m_admin_0_countries", name="ne_110m_admin_0_countries.shp")
    world = gpd.read_file(path)

    long_names = dict(world[["FIPS_10", "FORMAL_EN"]].values)
    # print(long_names)
    # print(world.to_markdown())

    world = world[world["ADMIN"] != "Antarctica"]

    # Change the projection to Plate Carrée (central longitude at 0 degrees)
    world = world.to_crs("+proj=robin")  # Use Miller cylindrical projection

    # Create a column to distinguish the highlighted countries
    world["highlight"] = world["FIPS_10"].apply(lambda x: 1 if counter.get(x) else 0)

    # Plot the world map
    _fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    world.boundary.plot(ax=ax, linewidth=1)  # Plot country borders
    world[world["highlight"] == 1].plot(ax=ax, color="lightgreen")

    # Add title and display the map
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(EXPORT_DIRECTORY.joinpath("countries.svg"), dpi=500)

    df = pd.DataFrame(
        [(code, long_names[code], count) for code, count in counter.most_common()],
        columns=["code", "name", "n_resources"],
    )
    df.to_csv(EXPORT_DIRECTORY.joinpath("countries.tsv"), sep="\t", index=False)


if __name__ == "__main__":
    main()
