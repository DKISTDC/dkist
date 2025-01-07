import copy
import gzip
import warnings
from pathlib import Path

import dask.array as da
import numpy as np
import pytest

import asdf
import astropy.modeling.models as m
import astropy.units as u
import gwcs
import gwcs.coordinate_frames as cf
from astropy.modeling import Model, Parameter
from astropy.table import Table
from astropy.time import Time

from sunpy.coordinates.frames import Helioprojective

from dkist import load_dataset, log
from dkist.data.test import rootdir
from dkist.dataset import Dataset
from dkist.dataset.tiled_dataset import TiledDataset
from dkist.io import FileManager
from dkist.io.loaders import AstropyFITSLoader


@pytest.fixture
def caplog_dkist(caplog):
    """
    A `dkist.log` specific equivalent to caplog.
    """
    log.addHandler(caplog.handler)
    return caplog


@pytest.fixture
def array():
    shape = 2**np.random.randint(2, 7, size=2)  # noqa: NPY002
    x = np.ones(np.prod(shape)) + 10
    x = x.reshape(shape)
    return da.from_array(x, tuple(shape))


class TwoDScale(Model):
    n_inputs = 2
    n_outputs = 2
    scale = Parameter()
    separable = False

    def evaluate(self, x, y, scale=1*u.deg):
        return u.Quantity([x, y]) * scale

    @property
    def inverse(self):
        return TwoDScale(1 / self.scale)


@pytest.fixture
def identity_gwcs():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds

    Note this WCS does not have a correct axis correlation matrix.
    """
    identity = m.Multiply(1*u.arcsec/u.pixel) & m.Multiply(1*u.arcsec/u.pixel)
    sky_frame = cf.CelestialFrame(axes_order=(0, 1),
                                  name="helioprojective",
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  unit=(u.arcsec, u.arcsec),
                                  axis_physical_types=("custom:pos.helioprojective.lat",
                                                       "custom:pos.helioprojective.lon"))
    detector_frame = cf.CoordinateFrame(name="detector", naxes=2,
                                        axes_order=(0, 1),
                                        axes_type=("pixel", "pixel"),
                                        axes_names=("x", "y"),
                                        unit=(u.pix, u.pix))
    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=sky_frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20)
    wcs.array_shape = wcs.pixel_shape[::-1]
    return wcs


@pytest.fixture
def identity_gwcs_3d():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = (TwoDScale(1 * u.arcsec / u.pixel) &
                m.Multiply(1 * u.nm / u.pixel))

    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name="helioprojective",
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  axes_names=("longitude", "latitude"),
                                  unit=(u.arcsec, u.arcsec),
                                  axis_physical_types=("custom:pos.helioprojective.lon", "custom:pos.helioprojective.lat"))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm, axes_names=("wavelength",))

    frame = cf.CompositeFrame([sky_frame, wave_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=3,
                                        axes_order=(0, 1, 2),
                                        axes_type=("pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z"), unit=(u.pix, u.pix, u.pix))

    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30)
    wcs.array_shape = wcs.pixel_shape[::-1]

    return wcs


@pytest.fixture
def identity_gwcs_3d_temporal():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = (TwoDScale(1 * u.arcsec / u.pixel) &
                m.Multiply(1 * u.s / u.pixel))

    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name="helioprojective",
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  axes_names=("longitude", "latitude"),
                                  unit=(u.arcsec, u.arcsec),
                                  axis_physical_types=("custom:pos.helioprojective.lon", "custom:pos.helioprojective.lat"))
    time_frame = cf.TemporalFrame(Time("2020-01-01T00:00", format="isot", scale="utc"),
                                  axes_order=(2,), unit=u.s)

    frame = cf.CompositeFrame([sky_frame, time_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=3,
                                        axes_order=(0, 1, 2),
                                        axes_type=("pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z"), unit=(u.pix, u.pix, u.pix))
    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30)
    wcs.array_shape = wcs.pixel_shape[::-1]
    return wcs


@pytest.fixture
def identity_gwcs_4d():
    """
    A simple 1-1 gwcs that converts from pixels to arcseconds
    """
    identity = (TwoDScale(1 * u.arcsec / u.pixel) &
                m.Multiply(1 * u.nm/u.pixel) & m.Multiply(1 * u.s/u.pixel))
    sky_frame = cf.CelestialFrame(axes_order=(0, 1), name="helioprojective",
                                  reference_frame=Helioprojective(obstime="2018-01-01"),
                                  unit=(u.arcsec, u.arcsec),
                                  axis_physical_types=("custom:pos.helioprojective.lon", "custom:pos.helioprojective.lat"))
    wave_frame = cf.SpectralFrame(axes_order=(2, ), unit=u.nm)
    time_frame = cf.TemporalFrame(Time("2020-01-01T00:00", format="isot", scale="utc"), axes_order=(3, ), unit=u.s)

    frame = cf.CompositeFrame([sky_frame, wave_frame, time_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=4,
                                        axes_order=(0, 1, 2, 3),
                                        axes_type=("pixel", "pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z", "s"),
                                        unit=(u.pix, u.pix, u.pix, u.pix))

    wcs = gwcs.wcs.WCS(forward_transform=identity, output_frame=frame, input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30, 40)
    wcs.array_shape = wcs.pixel_shape[::-1]

    return wcs


# This function lives in dkist_inventory, but is copied here to avoid a test dep
def generate_lookup_table(lookup_table, interpolation="linear", points_unit=u.pix, **kwargs):
    if not isinstance(lookup_table, u.Quantity):
        raise TypeError("lookup_table must be a Quantity.")

    # The integer location is at the centre of the pixel.
    points = (np.arange(lookup_table.size) - 0) * points_unit

    kwargs = {
        "bounds_error": False,
        "fill_value": np.nan,
        "method": interpolation,
        **kwargs
        }

    return m.Tabular1D(points, lookup_table, **kwargs)


@pytest.fixture
def identity_gwcs_5d_stokes(identity_gwcs_4d):
    stokes_frame = cf.StokesFrame(axes_order=(4,))
    stokes_model = generate_lookup_table([1, 2, 3, 4] * u.one, interpolation="nearest")
    transform = identity_gwcs_4d.forward_transform
    frame = cf.CompositeFrame([*identity_gwcs_4d.output_frame.frames, stokes_frame])

    detector_frame = cf.CoordinateFrame(name="detector", naxes=5,
                                        axes_order=(0, 1, 2, 3, 4),
                                        axes_type=("pixel", "pixel", "pixel", "pixel", "pixel"),
                                        axes_names=("x", "y", "z", "t", "s"),
                                        unit=(u.pix, u.pix, u.pix, u.pix, u.pix))

    wcs = gwcs.wcs.WCS(forward_transform=transform & stokes_model, output_frame=frame,
                       input_frame=detector_frame)
    wcs.pixel_shape = (10, 20, 30, 40, 4)
    wcs.array_shape = wcs.pixel_shape[::-1]

    return wcs


@pytest.fixture
def dataset(array, identity_gwcs):
    meta = {
        "inventory": {
            "bucket": "data",
            "datasetId": "test_dataset",
            "primaryProposalId": "test_proposal",
            "asdfObjectKey": "test_proposal/test_dataset/test_dataset.asdf",
            "browseMovieObjectKey": "test_proposal/test_dataset/test_dataset.mp4",
            "qualityReportObjectKey": "test_proposal/test_dataset/test_dataset.pdf",
            "wavelengthMin": 0,
            "wavelengthMax": 0,
        },
        "headers": Table()
    }

    identity_gwcs.array_shape = array.shape
    identity_gwcs.pixel_shape = array.shape[::-1]
    ds = Dataset(array, wcs=identity_gwcs, meta=meta, unit=u.count)
    # Sanity checks
    assert ds.data is array
    assert ds.wcs is identity_gwcs

    # Construct the filename here as a scalar array to make sure that works as
    # it's what dkist-inventory does
    ds._file_manager = FileManager.from_parts(np.array("test1.fits"), 0, "float", array.shape,
                                              loader=AstropyFITSLoader)

    return ds


@pytest.fixture
def empty_meta():
    return {"inventory": {}, "headers": {}}


@pytest.fixture
def dataset_3d(identity_gwcs_3d, empty_meta):
    shape = (25, 50, 50)
    x = np.ones(shape)
    array = da.from_array(x, tuple(shape))

    identity_gwcs_3d.pixel_shape = array.shape[::-1]
    identity_gwcs_3d.array_shape = array.shape

    return Dataset(array, wcs=identity_gwcs_3d, meta=empty_meta, unit=u.count)


@pytest.fixture
def dataset_4d(identity_gwcs_4d, empty_meta):
    shape = (50, 60, 70, 80)
    x = np.ones(shape)
    array = da.from_array(x, tuple(shape))

    identity_gwcs_4d.pixel_shape = array.shape[::-1]
    identity_gwcs_4d.array_shape = array.shape

    return Dataset(array, wcs=identity_gwcs_4d, meta=empty_meta, unit=u.count)


@pytest.fixture
def dataset_5d(identity_gwcs_5d_stokes, empty_meta):
    shape = (4, 40, 30, 20, 10)
    x = np.ones(shape)
    array = da.from_array(x, tuple(shape))

    identity_gwcs_4d.pixel_shape = array.shape[::-1]
    identity_gwcs_4d.array_shape = array.shape

    ds = Dataset(array, wcs=identity_gwcs_5d_stokes, meta={"inventory": {}, "headers": Table()}, unit=u.count)
    fileuris = np.array([f"dummyfile_{i}" for i in range(np.prod(shape[:-2]))]).reshape(shape[:-2])
    ds._file_manager = FileManager.from_parts(fileuris, 0, float, shape[-2:], loader=AstropyFITSLoader, basepath="./")

    return ds


@pytest.fixture
def dataset_5d_dummy_filemanager_axis(dataset_5d):
    shape = dataset_5d.data.shape
    fileuris = np.array([f"dummyfile_{i}" for i in range(np.prod(shape[:-2]))]).reshape(shape[:-2])
    dataset_5d._file_manager = FileManager.from_parts(fileuris, 0, float, (1, *shape[-2:]), loader=AstropyFITSLoader, basepath="./")

    return dataset_5d


@pytest.fixture
def eit_dataset():
    eitdir = Path(rootdir) / "EIT"
    with asdf.open(eitdir / "eit_test_dataset.asdf") as f:
        return f.tree["dataset"]


@pytest.fixture
def simple_tiled_dataset(dataset):
    datasets = [copy.deepcopy(dataset) for i in range(4)]
    for ds in datasets:
        ds.meta["inventory"] = dataset.meta["inventory"]
    dataset_array = np.array(datasets).reshape((2,2))
    return TiledDataset(dataset_array, dataset.meta["inventory"])


@pytest.fixture
def large_tiled_dataset(tmp_path_factory):
    vbidir = tmp_path_factory.mktemp("data")
    with gzip.open(Path(rootdir) / "large_vbi.asdf.gz", mode="rb") as gfo:
        with open(vbidir / "test_vbi.asdf", mode="wb") as afo:
            afo.write(gfo.read())
    return load_dataset(vbidir / "test_vbi.asdf")


@pytest.fixture
def small_visp_dataset():
    """
    This fixture is used to test when the array in the FITS file has a length
    one NAXIS 3.
    """
    # This asdf file won't work with sunpy less than 4
    pytest.importorskip("sunpy", "4.0.0")

    # This dataset was generated by the following code:
    # from dkist_data_simulator.spec214.visp import SimpleVISPDataset
    # from dkist_inventory.asdf_generator import dataset_from_fits
    # import astropy.units as u

    # ds = SimpleVISPDataset(n_maps=1, n_steps=3, n_stokes=1, time_delta=10,
    #                        linewave=500*u.nm, detector_shape=(10, 25))
    # ds.generate_files(vispdir)
    # dataset_from_fits(vispdir, "test_visp.asdf")

    vispdir = Path(rootdir) / "small_visp"
    with asdf.open(vispdir / "test_visp.asdf") as f:
        return f.tree["dataset"]


@pytest.fixture(scope="session")
def large_visp_dataset_file(tmp_path_factory):
    vispdir = tmp_path_factory.mktemp("data")
    with gzip.open(Path(rootdir) / "large_visp.asdf.gz", mode="rb") as gfo:
        with open(vispdir / "test_visp.asdf", mode="wb") as afo:
            afo.write(gfo.read())
    return vispdir / "test_visp.asdf"


@pytest.fixture(scope="session")
def large_visp_dataset(large_visp_dataset_file):
    # This dataset was generated by the following code:
    # from dkist_data_simulator.spec214.visp import SimpleVISPDataset
    # from dkist_inventory.asdf_generator import dataset_from_fits

    # tmp_path = tmp_path_factory.mktemp("data")
    # vispdir = Path(tmp_path) / "large_visp"
    # ds = SimpleVISPDataset(n_maps=1, n_steps=20, n_stokes=4, time_delta=10,
    #                        linewave=500*u.nm, detector_shape=(50, 128))
    # ds.generate_files(vispdir)
    # dataset_from_fits(vispdir, "test_visp.asdf")

    return load_dataset(large_visp_dataset_file)


@pytest.fixture(scope="session")
def visp_dataset_no_headers(tmp_path_factory):
    vispdir = tmp_path_factory.mktemp("data")
    with gzip.open(Path(rootdir) / "visp_no_headers.asdf.gz", mode="rb") as gfo:
        with open(vispdir / "test_visp_no_headers.asdf", mode="wb") as afo:
            afo.write(gfo.read())
    return load_dataset(vispdir / "test_visp_no_headers.asdf")


@pytest.fixture
def large_visp_no_dummy_axis(large_visp_dataset):
    # Slightly tweaked dataset to remove the dummy axis in the file manager array shape.
    shape = large_visp_dataset.data.shape[:2]
    fileuris = np.array([f"dummyfile_{i}" for i in range(np.prod(shape))]).reshape(shape)
    large_visp_dataset._file_manager = FileManager.from_parts(fileuris, 0, float, (50, 128), loader=AstropyFITSLoader, basepath="./")

    return large_visp_dataset


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    try:
        ds = item.config.getoption("--ds")
        tds = item.config.getoption("--tiled-ds")

        # Only one of accept_cli_dataset and accept_cli_tiled_dataset should be available
        mark = item.get_closest_marker("accept_cli_dataset") or item.get_closest_marker("accept_cli_tiled_dataset")
        if mark:
            # Replace either the fixture specified as the first arg of the marker, or the first fixture in the test definition
            replace_arg = mark.args[0] if mark.args else item.fixturenames[0]
            if ds:
                item.funcargs[replace_arg] = load_dataset(ds)
            if tds:
                item.funcargs[replace_arg] = load_dataset(tds)

        yield item
    except ValueError:
        # If CLI arguments can't be found, need to return gracefully
        # TODO raise a warning here
        warnings.warn("--ds and --tiled-ds were not found. Any supplied datasets will not be used.")
        yield item


@pytest.fixture(scope="session")
def croppable_visp_dataset(tmp_path_factory):
    vispdir = tmp_path_factory.mktemp("data")
    # This asdf file is for dataset ID BKEWK
    with gzip.open(Path(rootdir) / "croppable_visp.asdf.gz", mode="rb") as gfo:
        with open(vispdir / "croppable_visp.asdf", mode="wb") as afo:
            afo.write(gfo.read())
    return load_dataset(vispdir / "croppable_visp.asdf")


@pytest.fixture(scope="session")
def croppable_cryo_dataset():
    with gzip.open(Path(rootdir) / "croppable_cryo.asdf.gz", mode="rb") as gfo:
        with open(rootdir / "croppable_cryo.asdf", mode="wb") as afo:
            afo.write(gfo.read())
    return load_dataset(Path(rootdir) / "croppable_cryo.asdf")
