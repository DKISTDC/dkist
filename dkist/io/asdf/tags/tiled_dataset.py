from asdf.yamlutil import custom_tree_to_tagged_tree

from dkist.dataset.tiled_dataset import TiledDataset

from ..types import DKISTType

__all__ = ["DatasetType"]


class TiledDatasetType(DKISTType):
    name = "tiled_dataset"
    types = ["dkist.dataset.TiledDataset"]
    requires = ["dkist"]
    version = "0.1.0"
    supported_versions = ["0.1.0"]

    @classmethod
    def from_tree(cls, node, ctx):
        return TiledDataset(node["datasets"], node["inventory"])

    @classmethod
    def to_tree(cls, tiled_dataset, ctx):
        tree = {}
        tree["inventory"] = tiled_dataset._inventory
        tree["datasets"] = tiled_dataset._data.tolist()

        return custom_tree_to_tagged_tree(tree, ctx)

    @classmethod
    def assert_equal(cls, old, new):
        pass
