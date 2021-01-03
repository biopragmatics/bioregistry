# -*- coding: utf-8 -*-

"""Constants and utilities for registries."""

import os
from typing import Any

import pystow

__all__ = [
    'HERE',
    'DATA_DIRECTORY',
    'BIOREGISTRY_PATH',
    'BIOREGISTRY_MODULE',
    'EnsureEntry',
]

HERE = os.path.abspath(os.path.dirname(__file__))
DATA_DIRECTORY = os.path.join(HERE, 'data')
BIOREGISTRY_PATH = os.path.join(DATA_DIRECTORY, 'bioregistry.json')

BIOREGISTRY_MODULE = pystow.module('bioregistry')
EnsureEntry = Any

DOCS = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, 'docs'))
DOCS_DATA = os.path.join(DOCS, '_data')
DOCS_IMG = os.path.join(DOCS, 'img')
