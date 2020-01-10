from pathlib import Path

import numpy as np

from asdf import ExternalArrayReferenceCollection
from asdf.yamlutil import custom_tree_to_tagged_tree

from dkist.dataset import Dataset
from dkist.io import AstropyFITSLoader, DaskFITSArrayContainer

from ..types import DKISTType

__all__ = ['ArrayContainerType']


class ArrayContainerType(DKISTType):
    name = "array_container"
    types = ['dkist.io.array_containers.BaseFITSArrayContainer']
    requires = ['dkist']
    version = "0.1.0"

    @classmethod
    def from_tree(cls, node, ctx):
        # TODO: Work out a way over overriding this at dataset load.
        filepath = Path((ctx.uri or ".").replace("file:", ""))
        base_path = filepath.parent

        # TODO: The choice of Dask and Astropy here should be in a config somewhere.
        array_container = DaskFITSArrayContainer(node['fileuris'],
                                                 node['target'],
                                                 node['dtype'],
                                                 node['shape'],
                                                 loader=AstropyFITSLoader,
                                                 basepath=base_path)
        return array_container

    @classmethod
    def to_tree(cls, array_container, ctx):
        return ExternalArrayReferenceCollection.to_tree(array_container, ctx)

    @classmethod
    def assert_equal(cls, old, new):
        """
        This method is used by asdf to test that to_tree > from_tree gives an
        equivalent object.
        """
        assert new == old
