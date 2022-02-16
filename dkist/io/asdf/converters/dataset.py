from asdf.extension import Converter


class DatasetConverter(Converter):
    tags = [
        "asdf://dkist.nso.edu/tags/dataset-1.0.0",
        "tag:dkist.nso.edu:dkist/dataset-0.3.0",
        "tag:dkist.nso.edu:dkist/dataset-0.2.0",
        "tag:dkist.nso.edu:dkist/dataset-0.1.0",
    ]
    types = ["dkist.dataset.dataset.Dataset"]

    def from_yaml_tree(self, node, tag, ctx):
        from dkist.dataset import Dataset

        data = node["data"]._generate_array()
        wcs = node["wcs"]
        meta = node.get("meta", {})
        unit = node.get("unit")
        mask = node.get("mask")

        # Support older versions of the schema where headers was it's own top
        # level property
        if tag in ("tag:dkist.nso.edu:dkist/dataset-0.1.0",
                   "tag:dkist.nso.edu:dkist/dataset-0.2.0"):
            meta["inventory"] = node.get("meta")
            meta["headers"] = node["headers"]

        dataset = Dataset(data, wcs=wcs, meta=meta,
                          unit=unit, mask=mask)
        dataset._file_manager = node["data"]
        return dataset

    def to_yaml_tree(self, dataset, tag, ctx):
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
