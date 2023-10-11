import astropy.units as u
from astropy.coordinates import SkyCoord, StokesCoord
from astropy.time import Time


def test_crop_visp_by_only_stokes(croppable_visp_dataset):
    cropped = croppable_visp_dataset.crop([
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

    assert cropped.wcs.pixel_n_dim == croppable_visp_dataset.pixel_n_dims - 1
    assert cropped.data.shape == croppable_visp_dataset.data.shape[1:]
    # This won't be true yet because of bugs in the Stokes WCS
    # assert (cropped.headers['DINDEX4'] == 1).all()


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

    assert cropped.wcs.pixel_n_dim == croppable_cryo_dataset.pixel_n_dims - 1
    assert cropped.data.shape == croppable_cryo_dataset.data.shape[1:]
    # This won't be true yet because of bugs in the Stokes WCS
    # assert (cropped.headers['DINDEX4'] == 1).all()


def test_crop_cryo_by_time(croppable_cryo_dataset):
    coords = (croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0),
              croppable_cryo_dataset.wcs.pixel_to_world(1751, 1888, 1, 1, 3))
    # ([<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km,
    #         observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km):
    #             (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1010.91878194, 314.16916108)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:00:03.863>,
    #     StokesCoord('?')],
    # [<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km,
    #         observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km):
    #             (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1275.05503382, 174.35004711)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:03:13.863>,
    #     StokesCoord('U')])

    coord0 = SkyCoord(-1011*u.arcsec, 314*u.arcsec,
                      frame="helioprojective",
                      obstime="2023-01-01T13:03:13.863",
                      observer=coords[0][0].observer)
    coord1 = SkyCoord(-1275*u.arcsec, 174*u.arcsec,
                      frame="helioprojective",
                      obstime="2023-01-01T13:03:13.863",
                      observer=coords[1][0].observer)

    # Crop using user-defined coords
    cropped = croppable_cryo_dataset.crop([
        coord0,
        # Time has to be later than the start time becuase the crop is the smallest range that includes specified values
        Time("2023-01-01T13:00:04"),
        None,
    ],
    [
        coord1,
        Time("2023-01-01T13:03:13"),
        None,
    ])

    assert cropped.wcs.pixel_n_dim == croppable_cryo_dataset.pixel_n_dims
    assert cropped.data.shape[0] == croppable_cryo_dataset.data.shape[0]
    assert cropped.data.shape[1] == croppable_cryo_dataset.data.shape[1] - 1
    assert cropped.data.shape[2] == croppable_cryo_dataset.data.shape[2] - 1
    assert cropped.data.shape[3:] == croppable_cryo_dataset.data.shape[3:]


def test_crop_cryo_by_only_lonlat(croppable_cryo_dataset):
    coords = (croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0),
              croppable_cryo_dataset.wcs.pixel_to_world(1000, 1000, 2, 2, 3))
    pixel_coords = (croppable_cryo_dataset.wcs.world_to_pixel(*coords[0]),
                    croppable_cryo_dataset.wcs.world_to_pixel(*coords[1]))

    # ([<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km,
    #         observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km):
    #             (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1010.91878194, 314.16916108)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:00:03.863>,
    #     StokesCoord('?')],
    # [<SkyCoord (Helioprojective: obstime=2023-01-01T13:03:13.863, rsun=695700.0 km,
    #         observer=<HeliographicStonyhurst Coordinate (obstime=2023-01-01T13:03:13.863, rsun=695700.0 km):
    #             (lon, lat, radius) in (deg, deg, m) (0.00145788, -3.03322841, 1.47108585e+11)>):
    #     (Tx, Ty) in arcsec (-1153.0021188, 231.97726162)>,
    #     <Time object: scale='utc' format='isot' value=2023-01-01T13:06:23.863>,
    #     StokesCoord('U')])
    # Using calculated coords
    cropped1 = croppable_cryo_dataset.crop(*coords)

    coord0 = SkyCoord(-1011*u.arcsec, 314*u.arcsec,
                      frame="helioprojective",
                      obstime="2023-01-01T13:03:13.863",
                      # observer=SkyCoord(0.00145788*u.deg, -3.03322841*u.deg, 1.47108585e+11*u.m,
                      #                   frame="heliographic_stonyhurst", obstime="2023-01-01T13:03:13.863"))
                      observer=coords[0][0].observer)
    coord1 = SkyCoord(-1153*u.arcsec, 232*u.arcsec,
                      frame="helioprojective",
                      obstime="2023-01-01T13:03:13.863",
                      # observer=SkyCoord(0.00145788*u.deg, -3.03322841*u.deg, 1.47108585e+11*u.m,
                      #                   frame="heliographic_stonyhurst", obstime="2023-01-01T13:03:13.863"))
                      observer=coords[1][0].observer)

    # Crop using user-defined coords
    cropped2 = croppable_cryo_dataset.crop([
        coord0,
        Time("2023-01-01T13:00:04"),
        None,
    ],
    [
        coord1,
        Time("2023-01-01T13:06:23"),
        None,
    ])
