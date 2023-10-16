import astropy.units as u
from astropy.coordinates import SkyCoord, SpectralCoord, StokesCoord
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

    assert cropped.wcs.pixel_n_dim == croppable_visp_dataset.wcs.pixel_n_dim - 1
    assert cropped.data.shape == croppable_visp_dataset.data.shape[1:]
    # This won't be true yet because of bugs in the Stokes WCS
    # assert (cropped.headers['DINDEX4'] == 1).all()


def test_crop_visp_by_time(croppable_visp_dataset):
    coords = (croppable_visp_dataset.wcs.pixel_to_world(0, 0, 200, 0),
              croppable_visp_dataset.wcs.pixel_to_world(2554, 975, 400, 3))
    cropped = croppable_visp_dataset.crop([
        SpectralCoord(630.242*u.nm),
        SkyCoord(-426.41*u.arcsec, 169.40*u.arcsec,
                 frame="helioprojective",
                 obstime="2022-10-24T19:15:38",
                 observer=coords[0][0].observer),
        Time("2022-10-24T19:08:09"),
        None,
    ],
    [
        SpectralCoord(631.827*u.nm),
        SkyCoord(-420.85*u.arcsec, 304.45*u.arcsec,
                 frame="helioprojective",
                 obstime="2022-10-24T19:18:32",
                 observer=coords[1][0].observer),
        Time("2022-10-24T19:18:32"),
        None,
    ])

    assert cropped.wcs.pixel_n_dim == croppable_visp_dataset.wcs.pixel_n_dim
    assert cropped.data.shape[0] == croppable_visp_dataset.data.shape[0]
    assert cropped.data.shape[1] == 201
    assert cropped.data.shape[2:] == croppable_visp_dataset.data.shape[2:]

    orig_coords = croppable_visp_dataset.axis_world_coords()
    cropped_coords = cropped.axis_world_coords()
    assert (cropped_coords[0][0] == orig_coords[0][200]).all()
    assert (cropped_coords[0][-1] == orig_coords[0][400]).all()
    assert (cropped_coords[1] == orig_coords[1]).all()
    assert (cropped_coords[2] == orig_coords[2][200:401]).all()
    assert (cropped_coords[3] == orig_coords[3]).all()


def test_crop_visp_by_lonlat(croppable_visp_dataset):
    coords = (croppable_visp_dataset.wcs.pixel_to_world(500, 200, 0, 0),
              croppable_visp_dataset.wcs.pixel_to_world(1000, 600, 687, 4))

    coord0 = SkyCoord(-432.38*u.arcsec, 195.78*u.arcsec,
                      frame="helioprojective",
                      obstime="2022-10-24T19:15:38",
                      observer=coords[0][0].observer)

    coord1 = SkyCoord(-412.17*u.arcsec, 222.38*u.arcsec,
                      frame="helioprojective",
                      obstime="2022-10-24T19:15:38",
                      observer=coords[1][0].observer)

    cropped = croppable_visp_dataset.crop([
        SpectralCoord(630.568*u.nm),
        coord0,
        Time("2022-10-24T18:57:46"),
        None,
    ],
    [
        SpectralCoord(631.218*u.nm),
        coord1,
        Time("2022-10-24T19:33:26"),
        None,
    ])

    assert cropped.wcs.pixel_n_dim == croppable_visp_dataset.wcs.pixel_n_dim
    assert cropped.data.shape[:1] == croppable_visp_dataset.data.shape[:1]
    assert cropped.data.shape[2] == 401
    assert cropped.data.shape[3] == 501
    # Should also test here for consistency of world coords


def test_crop_cryo_by_only_stokes(croppable_cryo_dataset):
    cropped = croppable_cryo_dataset.crop([
        None,
        None,
        StokesCoord('I'),
    ],
    [
        None,
        None,
        StokesCoord('I'),
    ])

    assert cropped.wcs.pixel_n_dim == croppable_cryo_dataset.wcs.pixel_n_dim - 1
    assert cropped.data.shape == croppable_cryo_dataset.data.shape[1:]
    # This won't be true yet because of bugs in the Stokes WCS
    # assert (cropped.headers['DINDEX4'] == 1).all()


def test_crop_cryo_by_time(croppable_cryo_dataset):
    coords = (croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0),
              croppable_cryo_dataset.wcs.pixel_to_world(1751, 1888, 1, 1, 3))
    coord0 = SkyCoord(-1010.9*u.arcsec, 314.2*u.arcsec,
                      frame="helioprojective",
                      obstime="2023-01-01T13:03:13.863",
                      observer=coords[0][0].observer)
    coord1 = SkyCoord(-1275.1*u.arcsec, 174.4*u.arcsec,
                      frame="helioprojective",
                      obstime="2023-01-01T13:03:13.863",
                      observer=coords[1][0].observer)

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

    assert cropped.wcs.pixel_n_dim == croppable_cryo_dataset.wcs.pixel_n_dim
    assert cropped.data.shape[0] == croppable_cryo_dataset.data.shape[0]
    assert cropped.data.shape[1] == croppable_cryo_dataset.data.shape[1] - 1
    assert cropped.data.shape[2] == croppable_cryo_dataset.data.shape[2] - 1
    assert cropped.data.shape[3:] == croppable_cryo_dataset.data.shape[3:]
    # Should also test here for consistency of world coords


def test_crop_cryo_by_only_lonlat(croppable_cryo_dataset):
    coords = (croppable_cryo_dataset.wcs.pixel_to_world(0, 0, 0, 0, 0),
              croppable_cryo_dataset.wcs.pixel_to_world(1000, 1000, 2, 2, 3))
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
    cropped = croppable_cryo_dataset.crop([
        coord0,
        Time("2023-01-01T13:00:04"),
        None,
    ],
    [
        coord1,
        Time("2023-01-01T13:06:23"),
        None,
    ])

    assert cropped.wcs.pixel_n_dim == croppable_cryo_dataset.wcs.pixel_n_dim
    assert cropped.data.shape[:3] == croppable_cryo_dataset.data.shape[:3]
    assert cropped.data.shape[3] == 1001
    assert cropped.data.shape[4] == 999
    # Should also test here for consistency of world coords
