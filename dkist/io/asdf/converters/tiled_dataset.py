from asdf.extension import Converter

from dkist.io.file_manager import FileManager, StripedExternalArray
from dkist.io.loaders import AstropyFITSLoader


class TiledDatasetConverter(Converter):
    tags = [
        "tag:dkist.nso.edu:dkist/tiled_dataset-0.1.0",
        "asdf://dkist.nso.edu/tags/tiled_dataset-1.0.0",
    ]
    types = ["dkist.dataset.tiled_dataset.TiledDataset"]

    def from_yaml_tree(cls, node, tag, ctx):
        from dkist.dataset.tiled_dataset import TiledDataset

        tiled_dataset = TiledDataset(node["datasets"], node["inventory"])
        tiled_dataset._file_manager = FileManager(
            StripedExternalArray(
                fileuris = [[tile.files.filenames for tile in row] for row in tiled_dataset],
                target = 1,
                dtype = tiled_dataset[0, 0].files.fileuri_array.dtype,
                shape = tiled_dataset[0, 0]._data.chunksize,
                loader = AstropyFITSLoader,
                basepath = tiled_dataset[0, 0].files.basepath,
                chunksize = tiled_dataset[0, 0]._data.chunksize
            )
        )
        return tiled_dataset

    def to_yaml_tree(cls, tiled_dataset, tag, ctx):
        tree = {}
        tree["inventory"] = tiled_dataset._inventory
        tree["datasets"] = tiled_dataset._data.tolist()
        return tree
