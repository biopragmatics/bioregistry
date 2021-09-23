# Contributing

Contributions to the Bioregistry are welcomed and encouraged.

## Code Contribution

This project uses the [GitHub Flow](https://guides.github.com/introduction/flow)
model for code contributions. Follow these steps:

1. [Create a fork](https://help.github.com/articles/fork-a-repo) of the upstream
   repository
   at [`biopragmatics/bioregistry`](https://github.com/biopragmatics/bioregistry)
   on your GitHub account (or in one of your organizations)
2. [Clone your fork](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
   with `git clone https://github.com/<your namespace here>/bioregistry.git`
3. Commit changes to your fork with `git commit`
4. Push changes to your fork with `git push`
5. Repeat steps 3/4 as needed
6. Submit a pull request back to the upstream repository

### Merge Model

The Bioregistry
uses [squash merges](https://docs.github.com/en/github/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-pull-request-commits)
to group all related commits in a given pull request into a single commit upon
acceptance and merge into the main branch. This has several benefits:

1. TODO

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

### Documentation

darglint
sphinx

### Testing

unittests in tests/ directory
doctests in docstrings

### Syncing your fork

After cloning, you should add the upstream repository with

```shell
$ git remote add biopragmatics https://github.com/biopragmatics/bioregistry.git
```

### Python Version Compatibility

This project aims to support all versions of Python that have not passed their
end-of-life dates. See https://endoflife.date/python for a list.

### Logging

Python's builtin `print()` should not be used (except when writing to files),
it's checked by the
[`flake8-print`](https://github.com/jbkahn/flake8-print) plugin. If you're in a
command line setting or `main()` function for a module, you can use
`click.echo()`.