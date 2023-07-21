import importlib.resources as importlib_resources
from pathlib import Path
from functools import singledispatch

from jsonschema.exceptions import ValidationError

import asdf


@singledispatch
def load_dataset():
    """Function to load a Dataset from either an asdf file path or a directory."""


@load_dataset.register
def _load_from_string(path: str):
    return _load_from_path(Path(path))


@load_dataset.register
def _load_from_path(path: Path):
    path = path.expanduser()
    if not path.is_dir():
        if not path.exists():
            raise ValueError(f"File {path} does not exist.")
        # elif raise error if extension is not .asdf
        return _load_from_asdf(path)
    else:
        return _load_from_directory(path)


def _load_from_directory(directory):
    """
    Construct a `~dkist.dataset.Dataset` from a directory containing one
    asdf file and a collection of FITS files.
    """
    base_path = Path(directory).expanduser()
    asdf_files = tuple(base_path.glob("*.asdf"))

    if not asdf_files:
        raise ValueError("No asdf file found in directory.")
    elif len(asdf_files) > 1:
        raise NotImplementedError("Multiple asdf files found in this "
                                    "directory. Use from_asdf to specify which "
                                    "one to use.")  # pragma: no cover

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
                ds = ff.tree['dataset']
                if isinstance(ds, TiledDataset):
                    for sub in ds.flat:
                        sub.files.basepath = base_path
                else:
                    ds.files.basepath = base_path
                return ds

    except ValidationError as e:
        err = f"This file is not a valid DKIST Level 1 asdf file, it fails validation with: {e.message}."
        raise TypeError(err) from e
