import copy

import numpy as np
from packaging.version import Version

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
        datasets = np.array(node["datasets"])

        # For all versions of tile_dataset newer than or equal to
        # 1.3.0 the header table for each sub-dataset is stored as
        # proxy dict
        tag_version = Version(tag.rsplit("-")[1])
        if tag_version >= Version("1.3.0"):
            # Convert from offset / size dicts to header table slices
            for ds in datasets.flat:
                if ds is not None:  # skip masked elements
                    if not isinstance(ds.headers, dict):  # pragma: nocover
                        raise TypeError("Expected offset/size header proxy object")

                    offset, size = ds.headers["offset"], ds.headers["size"]
                    ds.meta["headers"] = meta["headers"][offset:offset+size]

        return TiledDataset(datasets, mask=mask, meta=meta)

    def to_yaml_tree(cls, tiled_dataset, tag, ctx):
        tree = {}
        # Copy the meta so we don't pop from the one in memory
        meta = copy.copy(tiled_dataset.meta)
        # If the history key has been injected into the meta, do not save it
        meta.pop("history", None)
        tree["meta"] = meta
        # Copy the data as well so we aren't editing dataset headers in place
        datasets = []
        for ds in tiled_dataset._data.flat:
            if ds:
                new_ds = copy.copy(ds)
                new_ds.meta = copy.copy(ds.meta)
                datasets.append(new_ds)
            else:
                datasets.append(None)
        # Go into dataset header attributes and replace with {"offset": ..., "size": ...}
        offset = 0
        for ds in datasets:
            if ds:
                s = len(ds.files)
                ds.meta["headers"] = {"offset": offset, "size": s}
                offset += s
        tree["datasets"] = np.array(datasets).reshape(tiled_dataset.shape).tolist()
        tree["mask"] = tiled_dataset.mask
        return tree
