---
layout: page
title: Project Governance
permalink: /governance/
---

# Governance

The goal of the Bioregistry is to enable community-driven curation and
maintenance of a registry of prefixes and their associated metadata. This is a
first suggestion for some minimal governance (heavily inspired by
https://github.com/mapping-commons/SSSOM/issues/82, since that is a similar
community-driven effort). Discussion for this governance is taking place on
https://github.com/biopragmatics/bioregistry/issues/156.

## Manually Updating the Bioregistry

- Manual updates to the contents of the Bioregistry (e.g., adding a new prefix,
  merging prefixes, splitting prefixes, or updating a prefix's associated
  metadata) must be done either in the form of an issue or a pull request.
- The only updates that aren't considered manual are the ones done by the CI
  system on a chronological basis.
- Manual updates can be accepted if all continuous integration tests pass and a
  member of the Bioregistry Review Team approves. It's best practice that a
  member of the Review Team does not approve their own updates.
- New prefixes must conform to
  https://github.com/biopragmatics/bioregistry/issues/158 and
  https://github.com/biopragmatics/bioregistry/issues/133 and the
  [contribution guidelines](CONTRIBUTING.md).
- Attribution information for the requester and reviewer of manual updates must
  be collected in the form of an [ORCiD identifier](https://orcid.org).

## Review Team

The _Bioregistry Review Team_ is responsible for reviewing requests for new
prefixes, merging prefixes, splitting prefixes, and updating metadata associated
with prefixes. It is implemented as a GitHub team that has "triage" permissions
(e.g., able to maintain issues and pull requests).

Until all of the potential update interactions have been codified with GitHub
actions workflows, the review team is also responsible for either helping the
requester create an appropriate pull request or creating an appropriate pull
request directly if none has been given by the requester.

### Membership

- Membership to the Bioregistry Review Team is requested on the issue tracker
- Membership to the Bioregistry Review Team is granted at the discretion of the
  existing Bioregistry Review Team using
  [Disapproval Voting](https://en.wikipedia.org/wiki/Disapproval_voting)
- Members must join and participate the OBO Foundry Slack, the #prefixes
  channel, and the Review Team private chat.
- Members must be listed alphabetically by family name [below](#members)

#### Member Onboarding

- Add to private channel on OBO Foundry Slack
- Add to the GitHub
  [review team](https://github.com/orgs/biopragmatics/teams/bioregistry-reviewers)
  (note that GitHub hasn't yet enabled teams to be publicly viewed, and this
  link currently results in a 404 error)
- Add to membership list below in alphabetical order by last name in along with
  their GitHub handle, ORCID identifier, and date of joining.

#### Removing Members

- Members who unresponsive for 3 or more months can be removed by another member
  of the Bioregistry Review Team
- Members who do not conduct themselves according to the Bioregistry
  [Code of Conduct](CODE_OF_CONDUCT.md) can be suggested to be removed by a
  member of the Bioregistry Review Team.

#### Member Offboarding

- Remove from the private channel on OBO Foundry Slack
- Remove from the the GitHub
  [review team](https://github.com/orgs/biopragmatics/teams/bioregistry-reviewers)
  (note that GitHub hasn't yet enabled teams to be publicly viewed, and this
  link currently results in a 404 error)
- Add the date of exit and move their name and information ot the previous
  members list.

#### Members

- Meghan Balk (@megbalk; https://orcid.org/0000-0003-2699-3066; joined 2022-01)
- Tiffany Callahan (@callahantiff; https://orcid.org/0000-0002-8169-9049; joined
  2022-01)
- Benjamin M. Gyori (@bgyori; https://orcid.org/0000-0001-9439-5346)
- Charles Tapley Hoyt (@cthoyt; https://orcid.org/0000-0003-4423-4370)
- Tiago Lubiana (@lubianat; https://orcid.org/0000-0003-2473-2313; joined
  2022-01)

#### Previous Members

We're a new team and don't have any yet!

## Core Development Team

The _Core Development Team_ is responsible for maintaining the codebase
associated with the Bioregistry, which includes the Python package, the
Bioregistry web application, docker configurations/artifacts, and related GitHub
repositories. It is implemented as a GitHub team that has "maintain" permissions
(e.g., able to write to the repo as well as maintain issues and pull requests).

Contributions to the Bioregistry code must be submitted as pull requests to
https://github.com/biopragmatics/bioregistry. They must conform to the
[contribution guidelines](CONTRIBUTING.md). Code contributions must be approved
by a member of the Core Development Team as well as pass continuous integration
tests before merging.

### Membership

- Membership to the Bioregistry Core Development Team is requested on the issue
  tracker
- It is required that a potential member of the Bioregistry Core Development
  Team has previously made a contribution as an external contributor (to which
  there are no requirements)
- Membership to the Bioregistry Core Development Team is granted at the
  discretion of the existing Bioregistry Core Development Team using
  [Disapproval Voting](https://en.wikipedia.org/wiki/Disapproval_voting)
- Members must be listed alphabetically by family name [below](#members-1)

#### Members

- Benjamin M. Gyori (@bgyori; https://orcid.org/0000-0001-9439-5346)
- Charles Tapley Hoyt (@cthoyt; https://orcid.org/0000-0003-4423-4370)

## Publications / Attribution

All members of the core development and review teams are automatically authors
on Bioregistry papers and can propose other co-authors.

All contributors to the data underlying the Bioregistry, regardless of curation
size, should be considered for authorship on Bioregistry papers. These
contributions are automatically summarized at
https://bioregistry.io/contributors.

Larger external institutional contributors should be acknowledged in the
following places, where appropriate:

- On the [support](https://github.com/biopragmatics/bioregistry#-support) and
  [funding](https://github.com/biopragmatics/bioregistry#-funding) sections of
  the repository's main README.md
- On the [acknowledgements](https://bioregistry.io/acknowledgments) page of
  https://bioregistry.io

## Bootstrapping governance

This document's governance will go into effect after additional rounds of
editing and community discussion. The Bioregistry Review Team will announce when
it is officially in effect.

## Updating governance

This governance must updated through the following steps:

1. Create an issue on the Bioregistry's
   [issue tracker](https://github.com/biopragmatics/bioregistry/issues)
   describing the desired change and reasoning.
2. Engage potential stakeholders in discussion.
3. Solicit the Bioregistry Review Team for a review.
4. The Bioregistry Review Team will accept changes at their discretion.

This procedure doesn't apply to cosmetic or ergonomics changes, which are
allowed to be done in a more _ad-hoc_ manner. The Bioregistry Review Team may
later make explicit criteria for accepting changes to this governance.

## Partners

Please see https://github.com/biopragmatics/bioregistry/issues/755 for
discussions about a governance model for partnerships between the Bioregistry
and identifier space owners.
