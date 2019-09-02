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
    version = "0.1.0"

    @classmethod
    def from_tree(cls, node, ctx):
        filepath = Path(ctx.uri or ".")
        base_path = filepath.parent

        pointer_array = np.array(node['array_container'])

        # TODO: The choice of Dask and Astropy here should be in a config somewhere.
        array_container = DaskFITSArrayContainer(pointer_array,
                                                 loader=AstropyFITSLoader,
                                                 basepath=base_path)
        return array_container

    @classmethod
    def to_tree(cls, array_container, ctx):
        node = {}
        node['array_container'] = array_container.as_external_array_references()
        return custom_tree_to_tagged_tree(node, ctx)

    @classmethod
    def assert_equal(cls, old, new):
        """
        This method is used by asdf to test that to_tree > from_tree gives an
        equivalent object.
        """
