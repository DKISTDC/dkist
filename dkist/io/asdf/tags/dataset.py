from pathlib import Path

import numpy as np

from asdf.yamlutil import custom_tree_to_tagged_tree

from dkist.dataset import Dataset
from dkist.io import AstropyFITSLoader, DaskFITSArrayContainer

from ..types import DKISTType

__all__ = ['DatasetType']


class DatasetType(DKISTType):
    name = "dataset"
    types = ['dkist.dataset.Dataset']
    requires = ['dkist']
    version = "0.1.0"

    @classmethod
    def from_tree(cls, node, ctx):
        data = node['data'].array
        wcs = node['wcs']
        meta = node['meta']
        headers = node['headers']
        unit = node.get('unit')
        mask = node.get('mask')

        dataset = Dataset(data, header_table=headers, wcs=wcs, meta=meta,
                          unit=unit, mask=mask)
        dataset._array_container = node['data']
        return dataset

    @classmethod
    def to_tree(cls, dataset, ctx):
        if dataset._array_container is None:
            raise ValueError("This Dataset object can not be saved to asdf as "
                             "it was not constructed from a set of FITS files.")
        node = {}
        node['meta'] = dataset.meta
        node['wcs'] = dataset.wcs
        node['headers'] = dataset.headers
        node['data'] = dataset._array_container
        node['unit'] = dataset.unit
        node['mask'] = dataset.mask

        return custom_tree_to_tagged_tree(node, ctx)

    @classmethod
    def assert_equal(cls, old, new):
        """
        This method is used by asdf to test that to_tree > from_tree gives an
        equivalent object.
        """
        assert old.meta == new.meta
        assert old.wcs == new.wcs
        assert old.headers == new.headers
        assert old._array_container == new._array_container
        assert old.unit == new.unit
        assert old.mask == new.mask
