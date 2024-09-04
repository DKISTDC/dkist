import importlib.resources as importlib_resources
from pathlib import Path
from functools import singledispatch

from parfive import Results

import asdf

try:
    # first try to import from asdf.exceptions for asdf 2.15+
    from asdf.exceptions import ValidationError
except ImportError:
    # fall back to top level asdf for older versions of asdf
    from asdf import ValidationError


def asdf_open_memory_mapping_kwarg(memmap: bool) -> dict:
    if asdf.__version__ > "3.1.0":
        return {"memmap": memmap}
    return {"copy_arrays": not memmap}


@singledispatch
def load_dataset(target):
    """
    Load a DKIST dataset from a variety of inputs.

    This function loads one or more DKIST ASDF files into `dkist.Dataset` or
    `dkist.TiledDataset` classes. It can take a variety of inputs (listed below)
    and will either return a single object or a list of objects if multiple
    datasets are loaded.

    Parameters
    ----------
    target : {types}
        The location of one or more ASDF files.

        {types_list}

    Returns
    -------
    datasets
        An instance of `dkist.Dataset` or `dkist.TiledDataset` or a list thereof.

    Examples
    --------

    >>> import dkist

    >>> dkist.load_dataset("/path/to/VISP_L1_ABCDE.asdf")  # doctest: +SKIP

    >>> dkist.load_dataset("/path/to/ABCDE/")  # doctest: +SKIP

    >>> dkist.load_dataset(Path("/path/to/ABCDE"))  # doctest: +SKIP

    >>> from dkist.data.sample import VISP_BKPLX  # doctest: +REMOTE_DATA
    >>> print(dkist.load_dataset(VISP_BKPLX))  # doctest: +REMOTE_DATA
    This VISP Dataset BKPLX consists of 1700 frames.
    Files are stored in ...VISP_BKPLX
    <BLANKLINE>
    This Dataset has 4 pixel and 5 world dimensions.
    <BLANKLINE>
    The data are represented by a <class 'dask.array.core.Array'> object:
    dask.array<reshape, shape=(4, 425, 980, 2554), dtype=float64, chunksize=(1, 1, 980, 2554), chunktype=numpy.ndarray>
    <BLANKLINE>
    Array Dim  Axis Name                Data size  Bounds
            0  polarization state               4  None
            1  raster scan step number        425  None
            2  dispersion axis                980  None
            3  spatial along slit            2554  None
    <BLANKLINE>
    World Dim  Axis Name                  Physical Type                   Units
            4  stokes                     phys.polarization.stokes        unknown
            3  time                       time                            s
            2  helioprojective latitude   custom:pos.helioprojective.lat  arcsec
            1  wavelength                 em.wl                           nm
            0  helioprojective longitude  custom:pos.helioprojective.lon  arcsec
    <BLANKLINE>
    Correlation between pixel and world axes:
    <BLANKLINE>
                              |                      PIXEL DIMENSIONS
                              |   spatial    |  dispersion  | raster scan  | polarization
             WORLD DIMENSIONS |  along slit  |     axis     | step number  |    state
    ------------------------- | ------------ | ------------ | ------------ | ------------
    helioprojective longitude |      x       |              |      x       |
                   wavelength |              |      x       |              |
     helioprojective latitude |      x       |              |      x       |
                         time |              |              |      x       |
                       stokes |              |              |              |      x
    """
    known_types = _known_types_docs().keys()
    raise TypeError(f"Input type {type(target).__name__} not recognised. It must be one of {', '.join(known_types)}.")


@load_dataset.register(Results)
def _load_from_results(results):
    """
    The results from a call to ``Fido.fetch``, all results must be valid DKIST ASDF files.
    """
    return _load_from_iterable(results)


# In Python 3.11 we can use the Union type here
@load_dataset.register(list)
@load_dataset.register(tuple)
def _load_from_iterable(iterable):
    """
    A list or tuple of valid inputs to ``load_dataset``.
    """
    datasets = [load_dataset(item) for item in iterable]
    if len(datasets) == 1:
        return datasets[0]
    return datasets


@load_dataset.register
def _load_from_string(path: str):
    """
    A string representing a directory or an ASDF file.
    """
    # TODO Adjust this to accept URLs as well
    return _load_from_path(Path(path))


@load_dataset.register
def _load_from_path(path: Path):
    """
    A path object representing a directory or an ASDF file.
    """
    path = path.expanduser()
    if not path.is_dir():
        if not path.exists():
            raise ValueError(f"{path} does not exist.")
        return _load_from_asdf(path)

    return _load_from_directory(path)


def _load_from_directory(directory):
    """
    Construct a `~dkist.dataset.Dataset` from a directory containing one
    asdf file and a collection of FITS files.
    """
    base_path = Path(directory).expanduser()
    asdf_files = tuple(base_path.glob("*.asdf"))

    if not asdf_files:
        raise ValueError(f"No asdf file found in directory {base_path}.")

    if len(asdf_files) > 1:
        return _load_from_iterable(asdf_files)

    asdf_file = asdf_files[0]

    return _load_from_asdf(asdf_file)


def _load_from_asdf(filepath):
    """
    Construct a dataset object from a filepath of a suitable asdf file.
    """
    from dkist.dataset import TiledDataset
    filepath = Path(filepath).expanduser()
    base_path = filepath.parent
    try:
        with importlib_resources.as_file(importlib_resources.files("dkist.io") / "level_1_dataset_schema.yaml") as schema_path:
            with asdf.open(filepath, custom_schema=schema_path.as_posix(),
                           lazy_load=False, **asdf_open_memory_mapping_kwarg(memmap=False)) as ff:
                ds = ff.tree["dataset"]
                if isinstance(ds, TiledDataset):
                    for sub in ds.flat:
                        sub.files.basepath = base_path
                else:
                    ds.files.basepath = base_path
                return ds

    except ValidationError as e:
        err = f"This file is not a valid DKIST Level 1 asdf file, it fails validation with: {e.message}."
        raise TypeError(err) from e


def _known_types_docs():
    known_types = load_dataset.registry.copy()
    known_types.pop(object)
    known_types_docs = {}
    for t, func in known_types.items():
        name = t.__qualname__
        if t.__module__ != "builtins":
            name = f"{t.__module__}.{name}"
        known_types_docs[name] = func.__doc__.strip()
    return known_types_docs


def _formatted_types_docstring(known_types):
    lines = [f"| `{fqn}` - {doc}" for fqn, doc in known_types.items()]
    return "\n        ".join(lines)


load_dataset.__doc__ = load_dataset.__doc__.format(types_list=_formatted_types_docstring(_known_types_docs()),
                                                   types=", ".join([f"`{t}`" for t in _known_types_docs().keys()]))
