import copy

from asdf.extension import Converter
from astropy.table import Table, vstack


class TiledDatasetConverter(Converter):
    tags = [
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.1.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.0.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.1.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.2.0",
        "tag:dkist.nso.edu:dkist/tiled_dataset-0.1.0",
    ]
    types = ["dkist.dataset.tiled_dataset.TiledDataset"]

    def from_yaml_tree(cls, node, tag, ctx):
        from dkist.dataset.tiled_dataset import TiledDataset

        for row in node["datasets"]:
            for ds in row:
                if ds:
                    ds._is_mosaic_tile = True

        # Support old files without meta, but with inventory
        meta = node.get("meta", {})

        meta["headers"] = node.get("headers", vstack([Table(ds.headers) for ds in row for row in node["datasets"]]))

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
        tree["datasets"] = tiled_dataset._data.tolist()
        tree["headers"] = tiled_dataset.combined_headers.as_array()
        tree["mask"] = tiled_dataset.mask
        return tree
