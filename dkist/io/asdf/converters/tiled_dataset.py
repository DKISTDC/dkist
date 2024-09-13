from asdf.extension import Converter


class TiledDatasetConverter(Converter):
    tags = [
        "tag:dkist.nso.edu:dkist/tiled_dataset-0.1.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.0.0",
    ]
    types = ["dkist.dataset.tiled_dataset.TiledDataset"]

    def from_yaml_tree(cls, node, tag, ctx):
        from dkist.dataset.tiled_dataset import TiledDataset

        return TiledDataset(node["datasets"], node["inventory"])

    def to_yaml_tree(cls, tiled_dataset, tag, ctx):
        tree = {}
        tree["inventory"] = tiled_dataset._inventory
        tree["datasets"] = tiled_dataset._data.tolist()
        return tree
