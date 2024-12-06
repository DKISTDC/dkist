#!/usr/bin/env python3
import tempfile

import numpy as np

import astropy.units as u

from dkist.data.test import rootdir

if __name__ == "__main__":
    from dkist_data_simulator.spec214.vbi import MosaicedVBIBlueDataset

    from dkist_inventory.asdf_generator import dataset_from_fits

    class DemoMosaicedVBIBlueDataset(MosaicedVBIBlueDataset):
        @property
        def data(self):
            return np.zeros(self.array_shape) + (self.mosaic_keys("MINDEX1") * self.mosaic_keys("MINDEX2"))

    mosaic = MosaicedVBIBlueDataset(2, 1, linewave=500*u.nm, detector_shape=(2, 2))

    with tempfile.TemporaryDirectory() as tempdir:
        mosaic.generate_files(tempdir, required_only=True)

        asdf_filename = rootdir / "test_tiled_dataset.asdf"
        ds = dataset_from_fits(tempdir, asdf_filename)
        print(ds)
