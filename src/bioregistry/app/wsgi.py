# -*- coding: utf-8 -*-

"""Web application for the Bioregistry."""

from bioregistry.app.impl import get_app

app = get_app()

if __name__ == "__main__":
    app.run(debug=True)  # noqa
