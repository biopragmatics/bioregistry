import click

from bioregistry.external.miriam import get_miriam_df
from bioregistry.external.obofoundry import get_obofoundry_df
from bioregistry.external.ols import get_ols_df


@click.command()
def main():
    get_miriam_df(force_download=True)
    get_ols_df(force_download=True)
    get_obofoundry_df(force_download=True)


if __name__ == '__main__':
    main()
