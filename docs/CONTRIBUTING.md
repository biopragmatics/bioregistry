---
layout: page
title: Contributing
permalink: /contributing/
---

Contributions to the Bioregistry are welcomed and encouraged. Thanks for
considering to participate.

All contributors, maintainers, and participants of the Bioregistry project are
expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md). This document is
organized as follows:

1. [Content Contribution](#content-contribution)
   1. [Submitting New Prefixes](#submitting-new-prefixes)
   2. [Editing Records](#editing-records)
   3. [Removing Records](#removing-records)
2. [Code Contribution](#code-contribution)

## Content Contribution

There are several ways to request a new prefix in the Bioregistry:

1. Fill out the
   [new prefix request form](https://github.com/biopragmatics/bioregistry/issues/new?assignees=cthoyt&labels=New%2CPrefix&template=new-prefix.yml&title=%5BResource%5D%3A%20xxxxx)
   on our GitHub issue tracker with as much information about the resource as
   possible (e.g., name, homepage, format URL pattern, example identifier,
   pattern). Don't worry if you don't understand everything, our Review Team
   will guide you through the process.
2. ~Add an entry yourself by
   [editing the Bioregistry](https://github.com/biopragmatics/bioregistry/edit/main/src/bioregistry/data/bioregistry.json)
   in GitHub through the web browser.~ As the Bioregistry has surpassed the size
   limit of in-browser editing on GitHub, this is no longer possible.
3. Make a pull request directly to the upstream repository
   [biopragmatics/bioregistry](https://github.com/biopragmatics/bioregistry).
   Make sure that you run `tox -e bioregistry-lint` from the shell after editing
   the source JSON files in order to canonically order the data.

### Submitting New Prefixes

#### Who Can Request a New Prefix

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
7. New prefixes must validate against the regular expression for the W3C
   definition of an
   [`NCNAME`](https://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-NCName):
   `^[A-Za-z_][A-Za-z0-9\\.\\-_]*$`. As an additional requirement, new prefixes
   must not start with an underscore.
8. New prefixes must pass all metadata checks, which are canonically defined by
   the quality assurance workflow.

Unfortunately, these requirements can not be applied retroactively and can not
be trivially applied to automatically imported prefixes. In some cases,
historical prefixes can be modified to follow these requirements. For example,
Identifiers.org's `ec-code` was renamed to `ec` while maintaining `ec-code` as a
synonym.

Some external registries' prefixes are not W3C conformant because they start
with a number, such as `3dmet` in MIRIAM. If it's not clear what a better prefix
might be, add an underscore to the start of the prefix and maintain the other
prefix as a synonym.

Original discussion about minimum prefix requirements can be found at
https://github.com/biopragmatics/bioregistry/issues/158.

#### Miscellaneous Requirements

- Do not include titles (e.g., Dr.) in contact information for the requester,
  reviewer, nor contact for a resource.

#### Choosing a Good Prefix

1. Prefixes should be chosen in a way to minimize confusion (e.g., prefixes
   should correspond to the name of the resource they are minted for. Most
   commonly, people use acronyms.)
2. Multiple prefixes will not be issued for multiple versions of a resource (
   e.g., the fact that there is a `mesh.2012` and `mesh.2013` prefix registered
   in Identifiers.org was a huge mistake and causes massive confusion)
3. Prefixes must not be too generic or common entity types like gene or
   chemical. Reviewers will use their best judgment since it's hard to list all
   possible generic entity types. For example, gene would be bad while
   `hgnc.gene` would be better.
4. Subspacing should not be used unnecessarily, i.e., when a nomenclature only
   has one entity type. For example, `chebi.chemical` would be bad while `chebi`
   would be better.
5. Prefixes should not end in "O" for "Ontology", "T" for "Terminology" or any
   letters denoting related words about vocabularies
6. New prefixes should not end with "ID" as a way to signify that the prefix is
   used for identifiers, like in `doid` for the Disease Ontology or `caid` for
   ClinGen Canonical Allele identifier.
7. New prefixes should be singular instead of plural. For example `hgnc.genes`
   would be bad while `hgnc.gene` would be better.

These policies were developed in parallel with the OBO Foundry policy on
choosing a prefix (i.e., IDSPACE) at http://obofoundry.org/id-policy.html.

#### Handling Collisions

While they have proven to be rather infrequent between high quality resources,
collisions do happen. The Bioregistry has the following policy for handling
collisions:

- New prefixes must not collide with any canonical prefixes, preferred prefixes,
  synonyms, or normalized variants thereof. See
  https://github.com/biopragmatics/bioregistry/issues/359 for an example of a
  prefix request that duplicated the synonyms of an existing prefix and how it
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
Foundry. This was resolved in
https://github.com/biopragmatics/bioregistry/issues/67 after deciding to change
the prefix used in Geographical Entity Ontology due to the fact that the Gene
Expression Omnibus was both much older and more well-known. This particular case
motivated the OBO Foundry to update its ontology registration guidelines to
require conflicts with existing Bioregistry records in
https://github.com/OBOFoundry/OBOFoundry.github.io/issues/1519. Another example
is the disease class annotation (legacy classification from the hard fork of the
Disease Ontology that later became MONDO) and Dublin Core, where one is
subjectively more important than the other.

#### Bulk Contribution

If you would like to submit more than 5 prefixes at once, you can fill out the
[bulk prefix request template](bulk_prefix_request_template.tsv) spreadsheet and
submit it in an
[issue](https://github.com/biopragmatics/bioregistry/issues/new). The template
contains several examples - please review them then delete them before
submission. Please number all of the rows in sequential order the first column
(`request_id`). The first columns of the template are all required, even if some
of the examples don't have an entry there for historic reasons. All optional
fields are marked as such.

Anyone is welcome to submit a bulk prefix request, but ideally submitters have a
large working knowledge of the Bioregistry, its requirements, etc. as reviewing
issues in a bulk request is much less ergonomic and more time-consuming than in
individual prefix requests, which each get their own discussion thread, pull
request, and CI/CD runs. Submitters of bulk prefix requests that contain many
issues may be asked to re-submit as individual prefix requests.

#### Prefix Parking

A prefix and its corresponding semantic space are **substantiated** when it's
provable that a semantic space exists by one or more of the following:

1. There's a public place where you can get the entire list of terms. Ontologies
   (e.g., [Gene Ontology](https://bioregistry.io/go)) and databases (e.g.,
   [HGNC](https://bioregistry.io/hgnc)) usually make this pretty
   straightforwards by offering download links for the ontology or full
   database.
2. There's a working, public URI format string that either lets you get HTML,
   JSON, RDF, or some other kind of information artifact for a given local
   unique identifier. For example, [OMIM.PS](https://bioregistry.io/omim.ps)
   doesn't have a way to get a full list of terms but if you have a given local
   unique identifier, you can use it with the URI format string to retrieve some
   information about the entity corresponding to that LUI.

A potential less strict third criteria for substantiation could be when
references to entities in a semantic space (i.e., in the form of CURIEs) can be
found in public resources or ontologies that are external to the resource in
which the prefix/semantic space are defined. This is more common for historical
prefixes (e.g., OpenCyc references appear quite frequently, but this resource
was taken down more than a decade ago) and is less applicable to new prefix
requests. Therefore, this relaxed criteria will not be considered as sufficient
for substantiation.

We define **prefix parking** as a special case of a prefix request in which the
corresponding resource/semantic space for the prefix does not yet exist or is
currently under development (and by definition, is not yet substantiated). The
Bioregistry does not explicitly discourage prefix parking, but new prefix
requests qualifying as prefix parking require additional guidelines, partially
motivated by the difficulty of the discussion on
https://github.com/biopragmatics/bioregistry/issues/359.

1. While it's not typically under the purview of the Bioregistry Review Team to
   judge the utility of a prefix nor comment on its corresponding design
   decisions (e.g., choice of local unique identifier scheme, regular expression
   pattern, URI format string), submitters seeking to park a prefix must both
   actively publicly seek out and seriously consider suggestions and advice from
   the Bioregistry Review Team with regards to these matters (e.g., in the issue
   corresponding to a new prefix request). Submissions unable/unwilling to
   follow these guidelines may be dismissed and asked to re-submit after their
   prefix has been substantiated.
2. Submissions to park a prefix must include a primary contact person for the
   resource that is available for public discussion on GitHub. Even though this
   is likely the same as the submitter, it is important that this person can be
   contacted. If they are unresponsive within two weeks of contact regarding the
   parked prefix, then the parked prefix is subject to removal.
3. Parked prefixes that are not substantiated within three months are subject to
   removal. In the case that someone else wants to use that prefix, the fact
   that the parked prefix has not been substantiated will, by definition, result
   in no impact or confusion that would normally result from the removal of a
   prefix. It is the responsibility of the submitter/primary contact person for
   the prefix to inform the Bioregistry Review Team of the updates and/or to
   submit the updates to their prefix record themselves that demonstrates it has
   been substantiated.
4. It's not the job of the Bioregistry to support parking prefixes for semantic
   spaces that will not be public or that won't be used in other public
   resources - these can be rejected without further discussion.

Original discussion about prefix parking can be found at
https://github.com/biopragmatics/bioregistry/issues/365.

#### Contact and Attribution

The Bioregistry collects the name, email, and optionally, the GitHub username
and ORCID identifier for individuals in several places:

1. As the primary responsible contact person for the semantic space associated
   with a prefix.
2. As the creator, contributor, or reviewer of record in the Bioregistry

We require in each situation that all fields explicitly correspond to the
individual with the goal to promote transparency and decrease the diffusion of
responsibility. This is inspired by and mirrors the OBO Foundry's
[Principle 11 "Locus of Authority"](https://obofoundry.org/principles/fp-011-locus-of-authority.html).

For the email field, this means that the following kinds of email addresses are
not acceptable:

1. Mailing lists
2. Help desks
3. Group emails
4. Issue trackers
5. Email addresses associated with a responsible person's assistant or
   administration

For the GitHub field, this means that GitHub organizations or GitHub users that
represent a group, such as a lab, are not acceptable.

For the ORCID field, it understood that an ORCID record should correspond to an
individual in the same spirit as this policy, and that the ORCID service should
not be abused to represent any non-individual.

In addition to the primary responsible contact person, the Bioregistry has
structured fields for additional contact methods, such as:

- `contact_extras` for annotating secondary contact people
- `contact_group_email` for annotating a contact email such as a mailing list
  that might be preferred by the resource over directly contacting the primary
  person. Only curate this field in addition to a primary contact person, to
  promote transparency.
- `contact_page` for annotating the URL of a web page that has contact
  information, e.g., containing a contact form. Only curate this field if a
  direct email is not available, as this is the least transparent option for
  contact

#### Review of New Prefix Requests

Review of new prefix requests is handled by the Bioregistry Review Team, whose
membership and conduct is described in the Bioregistry's
[Project Governance](GOVERNANCE.md).

### Editing Records

There are several ways to update a prefix's record in the Bioregistry:

1. Fill out one of the issue templates on our GitHub issue tracker with the
   requested information. If no template exists for your update, feel free to
   fill out a blank issue. We will help make the update and attribute you
   properly.
2. ~Edit an entry yourself by
   [editing the Bioregistry](https://github.com/biopragmatics/bioregistry/edit/main/src/bioregistry/data/bioregistry.json)
   in GitHub through the web browser.~ As the Bioregistry has surpassed the size
   limit of in-browser editing on GitHub, this is no longer possible.
3. Make a pull request directly to the upstream repository
   [biopragmatics/bioregistry](https://github.com/biopragmatics/bioregistry).
   Make sure that you run `tox -e bioregistry-lint` from the shell after editing
   the source JSON files in order to canonically order the data.

#### Who can edit an existing prefix's record

A prefix's record can be edited by anyone, even if it is for a resource they do
not themselves maintain. A main goal of the Bioregistry is to be a detailed,
descriptive resource - expertise is welcome from anywhere. In many cases,
editing an existing prefix's record is useful to override incorrect information
from integrated repositories, such as Identifiers.org.

#### Change of Prefix

Typically, prefixes should not be changed since the Bioregistry acts as an
archive of all usages, even deprecated ones. As an alternative, someone wishing
to change a prefix can do the following:

1. Mark the old prefix as deprecated
2. Include in the `comment` field information about when and why the prefix was
   deprecated
3. Add a `has_canonical` relationship from the old prefix's record to the new
   prefix

Like with all edits, these are subject to review by the Bioregistry Review team.
Extra care should be given with this kind of edit.

#### Review of Edits

Review of edits to existing records is handled by the Bioregistry Review Team,
whose membership and conduct is described in the Bioregistry's
[Project Governance](GOVERNANCE.md).

### Removing Records

Typically, prefixes should not be removed from the Bioregistry, even if they
correspond to subsumed, abandoned, or dead resources, because it is also a
historical archive and reference for anyone who might run into legacy prefixes
in legacy resources.

#### Review of Removals

Review of removals of existing records is handled by the Bioregistry Review
Team, whose membership and conduct is described in the Bioregistry's
[Project Governance](GOVERNANCE.md).

## Adding a new Registry

New registries can be added by anyone, similarly to prefixes, but there is a lot
more required curation. See the source
[metaregistry.json](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/metaregistry.json)
file for inspiration. Entries in this file should follow the schema defined by
the
[`Registry` pydantic model class](https://bioregistry.readthedocs.io/en/latest/api/bioregistry.Registry.html#bioregistry.Registry).
See also the corresponding entry in the Bioregistry's
[JSON schema](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/schema/schema.json)

While not strictly required, it's also useful for each registry to add a
corresponding getter script and aligner class in `bioregistry.external`. See
examples there, or get in touch on the issue tracker for help.

## Code Contribution

This project uses the [GitHub Flow](https://guides.github.com/introduction/flow)
model for code contributions. Follow these steps:

1. [Create a fork](https://help.github.com/articles/fork-a-repo) of the upstream
   repository at
   [`biopragmatics/bioregistry`](https://github.com/biopragmatics/bioregistry)
   on your GitHub account (or in one of your organizations)
2. [Clone your fork](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
   with `git clone https://github.com/<your namespace here>/bioregistry.git`
3. Make changes to the code
4. Test that your code passes quality assurance by running `tox`
5. Commit changes to your fork with `git commit`
6. Push changes to your fork with `git push`
7. Repeat steps 3-6 as needed
8. Submit a pull request back to the upstream repository

### Merge Model

The Bioregistry uses
[squash merges](https://docs.github.com/en/github/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-pull-request-merges#squash-and-merge-your-pull-request-commits)
to group all related commits in a given pull request into a single commit upon
acceptance and merge into the main branch. This has several benefits:

1. Keeps the commit history on the main branch focused on high-level narrative
2. Enables people to make lots of small commits without worrying about muddying
   up the commit history
3. Commits correspond 1-to-1 with pull requests

### Code Style

This project encourages the use of optional static typing. It uses
[`mypy`](http://mypy-lang.org/) as a type checker and
[`sphinx_autodoc_typehints`](https://github.com/agronholm/sphinx-autodoc-typehints)
to automatically generate documentation based on type hints. You can check if
your code passes `mypy` with `tox -e mypy`.

This project uses [`black`](https://github.com/psf/black) to automatically
enforce a consistent code style. You can apply `black` and other pre-configured
linters with `tox -e lint`.

This project uses [`flake8`](https://flake8.pycqa.org) and several plugins for
additional checks of documentation style, security issues, good variable
nomenclature, and more ( see [`tox.ini`](tox.ini) for a list of flake8 plugins).
You can check if your code passes `flake8` with `tox -e flake8`.

Each of these checks are run on each commit using GitHub Actions as a continuous
integration service. Passing all of them is required for accepting a
contribution. If you're unsure how to address the feedback from one of these
tools, please say so either in the description of your pull request or in a
comment, and we will help you.

### Logging

Python's builtin `print()` should not be used (except when writing to files),
it's checked by the [`flake8-print`](https://github.com/jbkahn/flake8-print)
plugin to `flake8`. If you're in a command line setting or `main()` function for
a module, you can use `click.echo()`. Otherwise, you can use the builtin
`logging` module by adding `logger = logging.getLogger(__name__)` below the
imports at the top of your file.

### Documentation

All public functions (i.e., not starting with an underscore `_`) must be
documented using the
[sphinx documentation format](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format).
The [`darglint`](https://github.com/terrencepreilly/darglint) plugin to `flake8`
reports on functions that are not fully documented.

This project uses [`sphinx`](https://www.sphinx-doc.org) to automatically build
documentation into a narrative structure. You can check that the documentation
properly builds with `tox -e docs-test`.

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
UI to do this by following
[this tutorial](https://docs.github.com/en/github/collaborating-with-pull-requests/working-with-forks/syncing-a-fork).

### Python Version Compatibility

This project aims to support all versions of Python that have not passed their
end-of-life dates. After end-of-life, the version will be removed from the Trove
qualifiers in the
[`setup.cfg`](https://github.com/biopragmatics/bioregistry/blob/main/setup.cfg)
and from the GitHub Actions testing configuration.

See https://endoflife.date/python for a timeline of Python release and
end-of-life dates.

#### Review of Pull Requests

Review of edits to existing records is handled by the Bioregistry Core
Development Team, whose membership and conduct is described in the Bioregistry's
[Project Governance](GOVERNANCE.md).

## Meta-contributions

### Retroactive Application of Curation Guidelines

As the Bioregistry matures, new fields may be added and more strict curation
guidelines may be imposed (both from a philosophical and technical perspective).
When imposing new rules, reasonable efforts should be made to backfill existing
records. Alternatively, existing prefixes can be "grandfathered" in to less
strict requirements.
