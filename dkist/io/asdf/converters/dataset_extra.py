from asdf.extension import Converter


class DatasetExtraConverter(Converter):
    tags = [
        "asdf://dkist.nso.edu/tags/dataset_extra-1.0.0"
    ]
    types = ["dkist.dataset.extras.DatasetExtra"]

    def from_yaml_tree(cls, node, tag, ctx):
        from dkist.dataset.extras import DatasetExtra
        return DatasetExtra(
            name=node["name"],
            headers=node["headers"],
            ears=node["files"],
        )

    def to_yaml_tree(cls, node, tag, ctx):
        return {
            "name": node.name,
            "headers": node.headers,
            "files": node._ears,
        }
