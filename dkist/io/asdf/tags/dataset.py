import numpy as np

from dkist.dataset import Dataset

from ..types import DKISTType

__all__ = ["DatasetType"]


class DatasetType(DKISTType):
    name = "dataset"
    types = ["dkist.dataset.Dataset"]
    requires = ["dkist"]
    version = "0.3.0"
    supported_versions = ["0.3.0", "0.2.0", "0.1.0"]

    @classmethod
    def from_tree(cls, node, ctx):
        data = node["data"]._generate_array()
        wcs = node["wcs"]
        meta = node.get("meta", {})
        unit = node.get("unit")
        mask = node.get("mask")

        # Support older versions of the schema where headers was it's own top
        # level property
        if "headers" in node and "headers" not in meta:
            meta = {}
            meta["inventory"] = node.get("meta")
            meta["headers"] = node["headers"]

        dataset = Dataset(data, wcs=wcs, meta=meta,
                          unit=unit, mask=mask)
        dataset._file_manager = node["data"]
        return dataset

    @classmethod
    def to_tree(cls, dataset, ctx):
        if dataset.files is None:
            raise ValueError("This Dataset object can not be saved to asdf as "
                             "it was not constructed from a set of FITS files.")
        node = {}
        node["meta"] = dataset.meta or {}
        node["wcs"] = dataset.wcs
        node["data"] = dataset.files
        if dataset.unit:
            node["unit"] = dataset.unit
        if dataset.mask:
            node["mask"] = dataset.mask

        return node

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
        old_headers = old.meta.pop("headers")
        new_headers = new.meta.pop("headers")
        cls._assert_table_equal(old_headers, new_headers)
        assert old.meta == new.meta
        old.meta["headers"] = old_headers
        new.meta["headers"] = new_headers
        cls._assert_wcs_equal(old.wcs, new.wcs)
        ac_new = new.files.external_array_references
        ac_old = old.files.external_array_references
        assert ac_new == ac_old
        assert old.unit == new.unit
        assert old.mask == new.mask
