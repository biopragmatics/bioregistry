"""Get twitter accounts."""

import json

import bioregistry

if __name__ == '__main__':
    twitters = {
        resource.prefix: twitter
        for resource in bioregistry.resources()
        if (twitter := resource.get_twitter())
    }
    with open("bioregistry_twitter.json", "w") as file:
        json.dump(twitters, file, indent=2)
