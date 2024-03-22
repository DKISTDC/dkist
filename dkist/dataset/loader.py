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

    >>> dkist.load_dataset("/path/to/VISP_L1_ABCDE.asdf")  # doctest: +SKIP

    >>> dkist.load_dataset("/path/to/ABCDE/")  # doctest: +SKIP

    >>> dkist.load_dataset(Path("/path/to/ABCDE"))  # doctest: +SKIP

    >>> from sunpy.net import Fido, attrs as a
    >>> import dkist.net
    >>> search_results = Fido.search(a.dkist.Dataset("AGLKO"))   # doctest: +REMOTE_DATA
    >>> files = Fido.fetch(search_results)   # doctest: +REMOTE_DATA
    >>> dkist.load_dataset(files)   # doctest: +REMOTE_DATA
    <dkist.dataset.dataset.Dataset object at ...>
    This Dataset has 4 pixel and 5 world dimensions
    <BLANKLINE>
    dask.array<reshape, shape=(4, 1000, 976, 2555), dtype=float64, chunksize=(1, 1, 976, 2555), chunktype=numpy.ndarray>
    <BLANKLINE>
    Pixel Dim  Axis Name                Data size  Bounds
            0  polarization state               4  None
            1  raster scan step number       1000  None
            2  dispersion axis                976  None
            3  spatial along slit            2555  None
    <BLANKLINE>
    World Dim  Axis Name                  Physical Type                   Units
            0  stokes                     phys.polarization.stokes        unknown
            1  time                       time                            s
            2  helioprojective latitude   custom:pos.helioprojective.lat  arcsec
            3  wavelength                 em.wl                           nm
            4  helioprojective longitude  custom:pos.helioprojective.lon  arcsec
    <BLANKLINE>
    Correlation between pixel and world axes:
    <BLANKLINE>
                   Pixel Dim
    World Dim    0    1    2    3
            0  yes   no   no   no
            1   no  yes   no   no
            2   no  yes   no  yes
            3   no   no  yes   no
            4   no  yes   no  yes

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
                           lazy_load=False, copy_arrays=True) as ff:
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
