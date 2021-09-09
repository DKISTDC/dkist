
import numpy as np

from asdf.yamlutil import custom_tree_to_tagged_tree

from dkist.dataset import Dataset

from ..types import DKISTType

__all__ = ["DatasetType"]


class DatasetType(DKISTType):
    name = "dataset"
    types = ["dkist.dataset.Dataset"]
    requires = ["dkist"]
    version = "0.2.0"
    supported_versions = ["0.2.0", "0.1.0"]

    @classmethod
    def from_tree(cls, node, ctx):
        data = node["data"]._generate_array()
        wcs = node["wcs"]
        headers = node["headers"]
        meta = node.get("meta")
        unit = node.get("unit")
        mask = node.get("mask")

        dataset = Dataset(data, wcs=wcs, meta=meta,
                          unit=unit, mask=mask, headers=headers)
        dataset._file_manager = node["data"]
        return dataset

    @classmethod
    def to_tree(cls, dataset, ctx):
        if dataset.files is None:
            raise ValueError("This Dataset object can not be saved to asdf as "
                             "it was not constructed from a set of FITS files.")
        node = {}
        node["meta"] = dataset.meta or None
        node["wcs"] = dataset.wcs
        node["headers"] = dataset.headers
        node["data"] = dataset.files
        if dataset.unit:
            node["unit"] = dataset.unit
        if dataset.mask:
            node["mask"] = dataset.mask

        return custom_tree_to_tagged_tree(node, ctx)

    @staticmethod
    def _assert_wcs_equal(old, new):
        from asdf.tests import helpers
        assert old.name == new.name
        assert len(old.available_frames) == len(new.available_frames)
        for old_step, new_step in zip(old.pipeline, new.pipeline):
            helpers.assert_tree_match(old_step.frame, new_step.frame)
            helpers.assert_tree_match(old_step.transform, new_step.transform)

    @classmethod
    def _assert_table_equal(cls, old, new):
        from asdf.tags.core.ndarray import NDArrayType
        assert old.meta == new.meta
        try:
            NDArrayType.assert_equal(np.array(old), np.array(new))
        except (AttributeError, TypeError, ValueError):
            for col0, col1 in zip(old, new):
                try:
                    NDArrayType.assert_equal(np.array(col0), np.array(col1))
                except (AttributeError, TypeError, ValueError):
                    assert col0 == col1

    @classmethod
    def assert_equal(cls, old, new):
        """
        This method is used by asdf to test that to_tree > from_tree gives an
        equivalent object.
        """
        assert old.meta == new.meta
        cls._assert_wcs_equal(old.wcs, new.wcs)
        cls._assert_table_equal(old.headers, new.headers)
        ac_new = new.files.external_array_references
        ac_old = old.files.external_array_references
        assert ac_new == ac_old
        assert old.unit == new.unit
        assert old.mask == new.mask
