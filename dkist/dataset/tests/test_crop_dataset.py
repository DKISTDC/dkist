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


def test_crop_cryo_by_only_stokes(croppable_cryo_dataset):
    croppable_cryo_dataset.crop([
        None,
        None,
        StokesCoord('I'),
    ],
    [
        None,
        None,
        StokesCoord('I'),
    ])


def test_crop_cryo_by_only_time(croppable_cryo_dataset):
    coords = croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0), croppable_cryo_dataset.wcs.pixel_to_world(1751, 1888, 1, 1, 3)
    print(coords)
    croppable_cryo_dataset.crop(*coords)


def test_crop_cryo_by_only_lonlat(croppable_cryo_dataset):
    coords = croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0), croppable_cryo_dataset.wcs.pixel_to_world(1000, 1000, 2, 2, 3)
    print(coords)
    # Using calculated coords
    cropped = croppable_cryo_dataset.crop(*coords)
