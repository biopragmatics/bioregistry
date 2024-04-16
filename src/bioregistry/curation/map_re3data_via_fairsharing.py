"""Add re3data mappings via FAIRsharing."""

from bioregistry import manager
from bioregistry.external.re3data import get_re3data


def _main():
    fairsharing_invmap = manager.get_registry_invmap("fairsharing")
    re3data_map = manager.get_registry_map("re3data")
    fairsharing_to_re3data = {
        value["xrefs"]["fairsharing"]: key
        for key, value in get_re3data(force_download=False).items()
        if "fairsharing" in value.get("xrefs", {})
    }
    for fairsharing_id, prefix in fairsharing_invmap.items():
        re3data_id = fairsharing_to_re3data.get(fairsharing_id)
        if re3data_id and re3data_id not in re3data_map:
            manager.registry[prefix].mappings["re3data"] = re3data_id
    manager.write_registry()


if __name__ == "__main__":
    _main()
