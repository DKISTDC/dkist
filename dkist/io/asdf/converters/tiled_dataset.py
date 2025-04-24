import copy

from asdf.extension import Converter


class TiledDatasetConverter(Converter):
    tags = [
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.3.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.2.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.1.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.0.0",
        "tag:dkist.nso.edu:dkist/tiled_dataset-0.1.0",
    ]
    types = ["dkist.dataset.tiled_dataset.TiledDataset"]

    def from_yaml_tree(cls, node, tag, ctx):
        from dkist.dataset.tiled_dataset import TiledDataset

        # Support old files without meta, but with inventory
        meta = node.get("meta", {})

        if "inventory" not in meta and (inventory := node.get("inventory", None)):
            meta["inventory"] = inventory

        mask = node.get("mask", None)
        return TiledDataset(node["datasets"], mask=mask, meta=meta)

    def to_yaml_tree(cls, tiled_dataset, tag, ctx):
        tree = {}
        # Copy the meta so we don't pop from the one in memory
        meta = copy.copy(tiled_dataset.meta)
        # If the history key has been injected into the meta, do not save it
        meta.pop("history", None)
        tree["meta"] = meta
        # Go into dataset header attributes and replace with {"offset": ..., "size": ...}
        offset = 0
        for ds in tiled_dataset.flat:
            s = len(ds.files)
            ds.meta["headers"] = {"offset": offset, "size": s}
            offset += s
        tree["datasets"] = tiled_dataset._data.tolist()
        tree["mask"] = tiled_dataset.mask
        return tree
