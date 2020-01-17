from pathlib import Path

import numpy as np

from asdf.yamlutil import custom_tree_to_tagged_tree

from dkist.dataset import Dataset
from dkist.io import AstropyFITSLoader, DaskFITSArrayContainer

from ..types import DKISTType

__all__ = ['ArrayContainerType']


class ArrayContainerType(DKISTType):
    name = "array_container"
    types = ['dkist.io.array_containers.BaseFITSArrayContainer']
    requires = ['dkist']
    version = "0.2.0"

    @classmethod
    def from_tree(cls, node, ctx):
        return DaskFITSArrayContainer.from_tree(node, ctx)

    @classmethod
    def to_tree(cls, array_container, ctx):
        return array_container.to_tree(array_container, ctx)

    @classmethod
    def assert_equal(cls, old, new):
        """
        This method is used by asdf to test that to_tree > from_tree gives an
        equivalent object.
        """
        assert new == old
