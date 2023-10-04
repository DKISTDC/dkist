from astropy.coordinates import StokesCoord


def test_crop_visp_by_only_stokes(croppable_visp_dataset):
    croppable_visp_dataset.crop([
        None,
        None,
        None,
        StokesCoord('I'),
    ],
    [
        None,
        None,
        None,
        StokesCoord('I'),
    ])
