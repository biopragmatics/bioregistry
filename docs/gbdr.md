---
layout: page
permalink: /gbdr/
title: Global Core Biodata Resources Application
---
While the Bioregistry was established in 2020 and is relatively young compared to the resources
applying for
[Global Core Biodata Resource (GCBR)](https://globalbiodata.org/scientific-activities/global-core-biodata-resources/)
status, its quick adoption as a key resource (as a database, web service, and software package) for FAIR
and TRUSTworthy data in the life and natural sciences and its exceptional governance and maintenance
model that ensures its longevity position it to be a strong applicant in 2024 (we're going to sit out in 2023 since the
Bioregistry doesn't yet achieve the "5 year" old status). Following the project's core value of
openness, this document will chronicle the preparation for application.

Some useful information about GCBR:

- [2023 Application Materials Overview](https://globalbiodata.org/scientific-activities/global-core-biodata-resources/gcbr-selection-2023/)
    - [2023 Pre-Application (Expression of Interest)](https://zenodo.org/record/5846742)
    - [2023 Application](https://zenodo.org/record/5846758)

## Section 1 - Description of Biodata Resource

### D1

> Please provide a concise description of your biodata resource, addressing how it falls within scope as a Global Core
> Biodata Resource.
> Word limit - 200 words

### D2

> Is this biodata resource......
> A deposition database serving as a repository of record for a specified data type(s)?
> Yes/No (Delete as applicable)
> A knowledgebase where, for example, expert manual curation adds value? Yes/No (Delete as applicable)

### D3: Consortium context.

> For biodata resources that belong to a larger consortium, or biodata resources that are an umbrella resource to which
> several collaborating databases contribute: please a) summarise that setting, and b) explain why the application is
> made as a consortium, or, conversely, as an individual resource.
> Word limit - 100 words

## Section 2 - Eligibility Criteria

### EC1: Has the resource been providing its services for at least 5 years?

> To qualify as a Core Biodata Resource it is necessary that the resource is sufficiently mature to contribute a high
> standard of service to the research data infrastructure.
> Yes/No
> Delete as applicable

No

The Bioregistry made its first release as a stand-alone database and web service on Dec 27<sup>th</sup>, 2020
with [v0.0.4](https://github.com/biopragmatics/bioregistry/releases/tag/v0.0.4). Previously, it was a component of
the [PyOBO project](https://github.com/pyobo/pyobo) which dated back to August, 2019.

Conservatively, the Bioregistry would not qualify for eligibility under EC1, but given the exceptional focus we placed
on longevity and sustainability for this resource (see [here](https://bioregistry.io/sustainability)), we ask for
exceptional exemption from this criterion.

### EC2: Is the resource able to provide usage statistics covering the scale of users and a statement of geographic distribution of users?

> To qualify as a Core Biodata Resource it needs to be able to demonstrate global usage beyond the country in which the
> data resource is housed, at scale.

- To do: implement tracking
- Add citations and demonstrations of its integration in various other tools (e.g., OLS in the United Kingdom, BERN in
  South Korea)

### EC3: Is the data resource able to provide details of community-recognised standards being used for their metadata and data?

> To qualify as a Core Biodata Resource it needs to be able to demonstrate implementation of FAIR data principles.

- to do: think about this question harder

The Bioregistry is a standards-issuing tool, with respect to the semantics under which references are made to biomedical
entities and concepts within the compact uniform resource identifier (CURIE) reccomendation set forth by the World Wide
Web Consortium.

### EC4: Does the data resource make its data available in a variety of formats?

> Core Biodata Resources encourage data re-usability by providing data in formats suitable for large scale re-use as
> well for individual queries via a web-based user interface.

Yes.

The Bioregistry distributes its data in JSON and YAML according to a well-defined schema. It also provides an RDF dump
of the data for ready integration into semantic web applications. Further, it makes exports in other use-case standard
specific formats such as the SSSOM which serves mappings, the cyberinfrastructure exchange (CX) for use with the Network
Data Exchange (NDEx) and Cytoscape.

### EC5: Does the resource have a Scientific Advisory Board or equivalent formal advisory body?

> A dedicated advisory body will be required for eligibility.

TODO! People to include:

- Chris Mungall
- Michel Dumontier
- Melissa Haendel XOR Julie McMurray
- Someone from Identifiers.org / N2T?

### EC6: Does the biodata resource have an open data licence with no requirement for permission from a data access committee or other authority for access to the resource or data within?

> An open data license will be required for eligibility, e.g. Creative Commons licenses CC0, CC-BY or CC-BY-SA are all
> conformant with the [Open Definition](http://opendefinition.org/licenses/).

Yes.

All original content in the Bioregistry is licensed under the CC0-1.0 license.
All code is served under the MIT License, an Open Source Initiative (OSI)-compliant license.
All external data is redistributed under original licenses, almost all of which are explicitly annotated as being highly
permissive. More specific information is available [here](https://bioregistry.io/acknowledgements).

### EC7: Does the biodata resource provide access to its data free of charge to the user?

> To qualify as a Core Biodata Resource the biodata resource must not require payment or subscription for access to data
> from any user.

Yes.

All data is openly available under the CC0-1.0 license.

### EC8: Is the biodata resource web site available in the English language?

> To qualify as a Core Biodata Resource the biodata resource must have an English language user interface as at least
> one option for users.

Yes.

### ~EC9: For Deposition Databases only: Does the biodata resource accept deposition of in-scope experimental data from the wider international community?~

> To qualify as a Core Biodata Resource a deposition database needs to accept deposition from across the global research
> community without geographic restriction.

N/A

### EC10: If qualification/explanation is needed for any of the above answers, please include that here: Word limit - 200 words

## Short Answer Questions

### SA1

> How does the resource serve as a fundamental resource across scientific approaches and disciplines, rather than for
> example serving a specific project or field of research?

It's a standards definition that is cross-disciplinary and not tied to any project - anyone using ontologies, semantic
web, or building databases can align to the Bioregistry standard.

### SA2

> Approximately how many users access the data resource per year? Please explain the basis for the count given, and
> include a statement addressing the geographical distribution of the users.

### SA3

> What would be the impact on other data resources and/or on the biodata resources ecosystem were this data resource to
> be withdrawn from service?

The two main issues would be no more resolver and no nice interface for people to explore prefixes.

However, it relies on Python infrastructure, which is pretty sustainable

People could re-deploy their own instance and continue updating it on their own because of the way we have set up its
build, deploymnt, etc.

### SA4

> How does the data resource support users? Examples might include a help desk, user training or workshops or social
> media Q&A. What opportunities for gathering user feedback do you provide?

1. Issue tracker - fully transparent discussion system
2. OBO Foundry Community Slack Channel
3. Social Media (twitter/mastodon)
4. Organizing yearly workshops
    - https://biopragmatics.github.io/workshops/WPCI2021
    - https://biopragmatics.github.io/workshops/WPCI2022
5. Participating in various related community efforts like SSSOM, OBO Foundry

### SA5

> What management structure and governance measures are in place for the data resource? Is there a dedicated resource
> manager? How frequently does the oversight committee meet? What is the relationship between the data resource and the
> host institution?

- [Code of Conduct](https://github.com/biopragmatics/bioregistry/blob/main/docs/CODE_OF_CONDUCT.md)
- [Governance](https://github.com/biopragmatics/bioregistry/blob/main/docs/GOVERNANCE.md)
- [Contribution Guidelines](https://github.com/biopragmatics/bioregistry/blob/main/docs/CONTRIBUTING.md)
