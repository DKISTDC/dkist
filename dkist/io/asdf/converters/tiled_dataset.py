from asdf.extension import Converter


class TiledDatasetConverter(Converter):
    tags = [
        "tag:dkist.nso.edu:dkist/tiled_dataset-0.1.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.0.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.1.0",
    ]
    types = ["dkist.dataset.tiled_dataset.TiledDataset"]

    def from_yaml_tree(cls, node, tag, ctx):
        from dkist.dataset.tiled_dataset import TiledDataset

        return TiledDataset(node["datasets"], node["inventory"], meta=node.get("meta"))

    def to_yaml_tree(cls, tiled_dataset, tag, ctx):
        tree = {}
        meta = copy.deepcopy(tiled_dataset.meta)
        inventory = meta.pop("inventory")
        # If the history key has been injected into the meta, do not save it
        meta.pop("history")
        tree["inventory"] = inventory
        tree["meta"] = meta
        tree["datasets"] = tiled_dataset._data.tolist()
        return tree
