from asdf.extension import Converter
from astropy.table import Table, vstack


class TiledDatasetConverter(Converter):
    tags = [
        "tag:dkist.nso.edu:dkist/tiled_dataset-0.1.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.0.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.1.0",
    ]
    types = ["dkist.dataset.tiled_dataset.TiledDataset"]

    def from_yaml_tree(cls, node, tag, ctx):
        from dkist.dataset.tiled_dataset import TiledDataset

        for row in node["datasets"]:
            for ds in row:
                if ds:
                    ds._is_mosaic_tile = True

        if node.get("headers"):
            headers = node["headers"]
        else:
            headers = vstack([Table(ds.headers) for ds in row for row in node["datasets"]])

        return TiledDataset(node["datasets"], node["inventory"], headers)

    def to_yaml_tree(cls, tiled_dataset, tag, ctx):
        tree = {}
        tree["inventory"] = tiled_dataset._inventory
        tree["datasets"] = tiled_dataset._data.tolist()
        tree["headers"] = tiled_dataset.combined_headers.as_array()
        return tree
