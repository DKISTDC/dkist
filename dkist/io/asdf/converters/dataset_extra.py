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
            full_header_table=node["full_header_table"],
            header_rows=node.get("header_rows", None),
            ears=node["files"],
        )

    def to_yaml_tree(cls, node, tag, ctx):
        tree = {
            "name": node.name,
            "full_header_table": node._full_header_table,
            "files": node._ears,
        }
        if node._header_rows is not None:
            tree["header_rows"] = node._header_rows
        return tree
