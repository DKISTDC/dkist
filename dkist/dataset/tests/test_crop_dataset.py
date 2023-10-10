from astropy.coordinates import StokesCoord
from astropy.time import Time


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


def test_crop_cryo_by_time(croppable_cryo_dataset):
    coords = (croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0),
              croppable_cryo_dataset.wcs.pixel_to_world(1751, 1888, 1, 1, 3))
    # ([<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km,
    #         observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km):
    #             (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1010.91878194, 314.16916108)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:00:03.863>,
    #     StokesCoord('?')],
    # [<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km, observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km): (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1275.05503382, 174.35004711)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:03:13.863>,
    #     StokesCoord('U')])

    # Crop using all calculated coords
    croppable_cryo_dataset.crop(*coords)

    # Crop using relevant calculated coords
    # Time and space are coupled in this ds so need the coords for both
    cropped1 = croppable_cryo_dataset.crop([
        coords[0][0],
        coords[0][1],
        None,
    ],
    [
        coords[1][0],
        coords[1][1],
        None,
    ])

    # Crop using user-defined coords
    cropped2 = croppable_cryo_dataset.crop([
        coords[0][0],
        # Time has to be later than the start time becuase the crop is the smallest range that includes specified values
        Time("2023-01-01T13:00:04"),
        None,
    ],
    [
        coords[1][0],
        Time("2023-01-01T13:03:13"),
        None,
    ])

    cropped3 = croppable_cryo_dataset.crop([
        coords[0][0],
        # Time has to be later than the start time becuase the crop is the smallest range that includes specified values
        Time("2023-01-01T13:00:04"),
        None,
    ],
    [
        coords[0][0],
        Time("2023-01-01T13:03:13"),
        None,
    ])

def test_crop_cryo_by_only_lonlat(croppable_cryo_dataset):
    coords = (croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0),
              croppable_cryo_dataset.wcs.pixel_to_world(1000, 1000, 2, 2, 3))
    # ([<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km, observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km): (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1010.91878194, 314.16916108)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:00:03.863>,
    #     StokesCoord('?')],
    # [<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km, observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km): (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1153.0021188, 231.97726162)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:06:23.863>,
    #     StokesCoord('U')])
    # Using calculated coords
    cropped1 = croppable_cryo_dataset.crop(*coords)
