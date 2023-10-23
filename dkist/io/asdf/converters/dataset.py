from asdf.extension import Converter


class DatasetConverter(Converter):
    tags = [
        "asdf://dkist.nso.edu/tags/dataset-1.2.0",
        "asdf://dkist.nso.edu/tags/dataset-1.1.0",
        "asdf://dkist.nso.edu/tags/dataset-1.0.0",
        "tag:dkist.nso.edu:dkist/dataset-0.3.0",
        "tag:dkist.nso.edu:dkist/dataset-0.2.0",
        "tag:dkist.nso.edu:dkist/dataset-0.1.0",
    ]
    types = ["dkist.dataset.dataset.Dataset"]

    def select_tag(self, obj, tags, ctx):
        # asdf sorts the tags supported by the current extension
        # in the case that multiple tags are relevant, pick the first
        # tag version as this most closely matches what asdf
        # used to do prior to 3.0
        return tags[0]

    def from_yaml_tree(self, node, tag, ctx):
        tag_version = tuple(map(int, tag.split("-")[1].split(".")))
        from dkist.dataset import Dataset

        data = node["data"]._striped_external_array._generate_array()
        wcs = node["wcs"]
        meta = node.get("meta", {})
        unit = node.get("unit")
        mask = node.get("mask")

        # If we have a tag older than 1.2.0 then we are going to see if we can
        # find a stokes table, and if we do then we are going to change it to be
        # compatible with gWCS 0.19
        if tag_version[0] == 0 or (tag_version[0] == 1 and tag_version[1] < 2):
            # Put imports here to reduce import time on entry point load
            import numpy as np

            import astropy.units as u
            from astropy.modeling.tabular import Tabular1D

            # Find all the Tabular 1D models in the transform
            for tabular in filter(lambda x: isinstance(x, Tabular1D), wcs.forward_transform.traverse_postorder()):
                # Assert that the lookup table and points are what we expect for an old stokes table
                if np.all(tabular.lookup_table == np.arange(4)) and u.allclose(tabular.points, np.arange(4)*u.pix):
                    tabular.lookup_table = np.arange(1, 5) * u.one

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
