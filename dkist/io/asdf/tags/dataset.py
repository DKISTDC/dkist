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
