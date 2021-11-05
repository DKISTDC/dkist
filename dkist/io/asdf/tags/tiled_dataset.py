from asdf.yamlutil import custom_tree_to_tagged_tree

from dkist.tiled_dataset import TiledDataset

from ..types import DKISTType

__all__ = ["DatasetType"]


class TiledDatasetType(DKISTType):
    name = "tiled_dataset"
    types = ["dkist.dataset.tiled_dataset.TiledDataset"]
    requires = ["dkist"]
    version = "0.1.0"
    supported_versions = ["0.1.0"]

    @classmethod
    def from_tree(cls, node, ctx):
        return TiledDataset(node["datasets"], node["inventory"])

    @classmethod
    def to_tree(cls, tiled_dataset, ctx):
        tree = {}
        tree["datasets"] = tiled_datasets._data.tolist()
        tree["inventory"] = tiled_datasets._inventory

        return custom_tree_to_tagged_tree(tree, ctx)

    @classmethod
    def assert_equal(cls, old, new):
        pass
