# Contributing

Contributions to the Bioregistry are welcomed and encouraged.

## Content Contribution

### New Prefixes

There are several ways to request a new prefix in the Bioregistry:

1. Fill out the [new prefix request form](https://github.com/biopragmatics/bioregistry/issues/new?assignees=cthoyt&labels=New%2CPrefix&template=new-prefix.yml&title=%5BResource%5D%3A%20xxxxx)
   on our GitHub issue tracker with as much information about the resource as
   possible (e.g., name, homepage, format URL pattern, example identifier,
   pattern). Don't worry if you don't understand everything, our Review Team
   will guide you through the process.
2. Add an entry yourself
   by [editing the Bioregistry](https://github.com/biopragmatics/bioregistry/edit/main/src/bioregistry/data/bioregistry.json)
   in GitHub through the web browser. As the Bioregistry is getting bigger, this
   is becoming more of an issue, so might not always be possible.
3. Make a pull request directly to the upstream repository
   [biopragmatics/bioregistry](https://github.com/biopragmatics/bioregistry).
4. Get in touch with us informally on
   Twitter [@bioregistry](https://twitter.com/bioregistry)

#### Who can request a prefix

A prefix can be requested by anyone, even if it is for a resource they do not
themselves maintain. A main goal of the Bioregistry is to be a detailed,
descriptive resource - expertise is welcome from anywhere. Ideally, the
requester should provide contact information for the main responsible person for
the resource or include them in discussion on GitHub directly. In many cases,
it's much easier for the resource responsible person to provide certain metadata
that's required to go with a given prefix.

#### Minimum New Prefix Requirements

1. New prefixes are allowed to contain letters [a-z], numbers [0-9], and a
   single dot `.` if a subspace is requested. More discussion on subspacing
   policy can be found https://github.com/biopragmatics/bioregistry/issues/133
   and https://github.com/biopragmatics/bioregistry/issues/65.
2. New prefixes must start with a letter.
3. New prefixes must be at least two characters. Ideally, prefixes should be
   three or more characters for legibility.
4. Subspaces must start with a letter.
5. Subspaces must be at least two characters. Ideally, subspaces should be three
   or more characters for legibility.
6. New prefixes must be lowercase. However, lexical variants can be stored as
   synonyms for reference (e.g., FBbt).
7. New prefixes must validate against the following regular expression:
   ^[a-z][a-z0-9]+(\.[a-z][a-z0-9]+?)$
8. New prefixes must pass all metadata checks, which are canonically defined by
   the quality assurance workflow.

Unfortunately, these requirements can not be applied retroactively and can not
be trivially applied to automatically imported prefixes. In some cases,
historical prefixes can be modified to follow these requirements. For example,
Identifiers.org's `ec-code` was renamed to `eccode` while maintaining `ec-code`
as a synonym.

Original discussion about minimum prefix requirements can be found at
https://github.com/biopragmatics/bioregistry/issues/158.

#### Choosing a Good Prefix

1. Prefixes should be chosen in a way to minimize confusion (e.g., prefixes
   should correspond to the name of the resource they are minted for. Most
   commonly, people use acronyms.)
2. Multiple prefixes will not be issued for multiple versions of a resource (
   e.g., the fact that there is a mesh.2012 and mesh.2013 prefix registered in
   Identifiers.org was a huge mistake and causes massive confusion)
3. Prefixes must not be too generic or common entity types like gene or
   chemical. Reviewers will use their best judgment since it's hard to list all
   possible generic entity types. For example, gene would be bad while hgnc.gene
   would be better.
4. Subspacing should not be used unnecessarily, i.e., when a nomenclature only
   has one entity type. For example, chebi.chemical would be bad while chebi
   would be better.
5. Prefixes should not end in "O" for "Ontology", "T" for "Terminology" or any
   letters denoting related words about vocabularies

These policies were developed in parallel with the OBO Foundry policy on
choosing a prefix (i.e., IDSPACE) at http://obofoundry.org/id-policy.html.

#### Handling Collisions

While they have proven to be rather infrequent between high quality resources,
collisions do happen. The Bioregistry has the following policy for handling
collisions:

- New prefixes must not collide with any canonical prefixes, preferred prefixes,
  synonyms, or normalized variants thereof.
  See https://github.com/biopragmatics/bioregistry/issues/359 for an example of
  a prefix request that duplicated the synonyms of an existing prefix and how it
  was able to be resolved.
- New prefixes should not collide with any prefixes in external registries, even
  if they are not explicitly imported in the Bioregistry. In these cases, a
  thoughtful discussion should take place explaining why the prefix is being
  reused (e.g., it has been parked by an inactive or low-quality resource in
  Bioportal).
- If a new contributor wants to register a prefix that is already present in the
  Bioregistry, then precedence will be given to the already existing prefix and
  the contributor will be asked to choose a different prefix.

It has not happened often that prefixes have even collided. One example is two
maintained resources, Gene Expression Omnibus vs. Geographical Entity Ontology,
collided on using `geo` when Geographical Entity Ontology was added to the OBO
Foundry. This was resolved
in https://github.com/biopragmatics/bioregistry/issues/67 after deciding to
change the prefix used in Geographical Entity Ontology due to the fact that the
Gene Expression Omnibus was both much older and more well-known. This particular
case motivated the OBO Foundry to update its ontology registration guidelines to
require conflicts with existing Bioregistry records
in https://github.com/OBOFoundry/OBOFoundry.github.io/issues/1519. Another
example is the disease class annotation (legacy classification from the hard
fork of the Disease Ontology that later became MONDO) and Dublin Core, where one
is subjectively more important than the other.

#### Removal of Prefixes

Typically, prefixes should not be removed from the Bioregistry, even if they
correspond to subsumed, abandoned, or dead resources, because it is also a
historical archive and reference for anyone who might run into legacy prefixes
in legacy resources.

## Code Contribution

This project uses the [GitHub Flow](https://guides.github.com/introduction/flow)
model for code contributions. Follow these steps:

1. [Create a fork](https://help.github.com/articles/fork-a-repo) of the upstream
   repository
   at [`biopragmatics/bioregistry`](https://github.com/biopragmatics/bioregistry)
   on your GitHub account (or in one of your organizations)
2. [Clone your fork](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
   with `git clone https://github.com/<your namespace here>/bioregistry.git`
3. Make and commit changes to your fork with `git commit`
4. Push changes to your fork with `git push`
5. Repeat steps 3 and 4 as needed
6. Submit a pull request back to the upstream repository

### Merge Model

The Bioregistry
uses [squash merges](https://docs.github.com/en/github/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-pull-request-commits)
to group all related commits in a given pull request into a single commit upon
acceptance and merge into the main branch. This has several benefits:

1. Keeps the commit history on the main branch focused on high-level narrative
2. Enables people to make lots of small commits without worrying about muddying
   up the commit history
3. Commits correspond 1-to-1 with pull requests

### Code Style

This project encourages the use of optional static typing. It
uses [`mypy`](http://mypy-lang.org/) as a type checker
and [`sphinx_autodoc_typehints`](https://github.com/agronholm/sphinx-autodoc-typehints)
to automatically generate documentation based on type hints. You can check if
your code passes `mypy` with `tox -e mypy`.

This project uses [`black`](https://github.com/psf/black) to automatically
enforce a consistent code style. You can apply `black` and other pre-configured
linters with `tox -e lint`.

This project uses [`flake8`](https://flake8.pycqa.org) and several plugins for
additional checks of documentation style, security issues, good variable
nomenclature, and more (
see [`tox.ini`](tox.ini) for a list of flake8 plugins). You can check if your
code passes `flake8` with `tox -e flake8`.

Each of these checks are run on each commit using GitHub Actions as a continuous
integration service. Passing all of them is required for accepting a
contribution. If you're unsure how to address the feedback from one of these
tools, please say so either in the description of your pull request or in a
comment, and we will help you.

### Logging

Python's builtin `print()` should not be used (except when writing to files),
it's checked by the
[`flake8-print`](https://github.com/jbkahn/flake8-print) plugin to `flake8`. If
you're in a command line setting or `main()` function for a module, you can use
`click.echo()`. Otherwise, you can use the builtin `logging` module by adding
`logger = logging.getLogger(__name__)` below the imports at the top of your
file.

### Documentation

All public functions (i.e., not starting with an underscore `_`) must be
documented using
the [sphinx documentation format](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format).
The [`darglint`](https://github.com/terrencepreilly/darglint) plugin to `flake8`
reports on functions that are not fully documented.

This project uses [`sphinx`](https://www.sphinx-doc.org) to automatically build
documentation into a narrative structure. You can check that the documentation
properly builds with `tox -e docs`.

### Testing

Functions in this repository should be unit tested. These can either be written
using the `unittest` framework in the `tests/` directory or as embedded
doctests. You can check that the unit tests pass with `tox -e py` and that the
doctests pass with `tox -e doctests`. These tests are required to pass for
accepting a contribution.

### Syncing your fork

If other code is updated before your contribution gets merged, you might need to
resolve conflicts against the main branch. After cloning, you should add the
upstream repository with

```shell
$ git remote add biopragmatics https://github.com/biopragmatics/bioregistry.git
```

Then, you can merge upstream code into your branch. You can also use the GitHub
UI to do this by following [this tutorial](https://docs.github.com/en/github/collaborating-with-pull-requests/working-with-forks/syncing-a-fork).

### Python Version Compatibility

This project aims to support all versions of Python that have not passed their
end-of-life dates. After end-of-life, the version will be removed from the Trove
qualifiers in the [`setup.cfg`](setup.cfg) and from the GitHub Actions testing
configuration.

See https://endoflife.date/python for a timeline of Python release and
end-of-life dates.

