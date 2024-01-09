import yaml
import requests

__all__ = [
    "get_togoid",
]

URL = (
    "https://raw.githubusercontent.com/togoid/togoid-converter/develop/swagger/swagger-config.yaml"
)


def get_togoid():
    rv = {}
    data = yaml.safe_load(requests.get(URL).text)
    subdata = data["paths"]["/config/dataset"]["get"]["responses"][200]["schema"]["properties"]
    for prefix, record in subdata.items():
        dd = {k: v["example"] for k, v in record["properties"].items() if "example" in v}
        rr = {
            "prefix": prefix,
            "name": dd["label"],
            "pattern": dd["regex"].replace("<id>", ""),
            "uri_format": dd["prefix"] + "$1",  # this is right, they named it weird
        }
        examples_lists = dd.get("examples", [])
        if examples_lists:
            rr["examples"] = examples_lists[0]
        category = dd.get("category")
        if category:
            rr["keywords"] = [category]
        rv[prefix] = rr
    return rv


if __name__ == "__main__":
    import pprint; pprint.pprint(get_togoid())
