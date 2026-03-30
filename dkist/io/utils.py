from pathlib import Path
from textwrap import dedent

import asdf

__all__ = ["filemanager_info_str", "save_dataset"]


def filemanager_info_str(filemanager):
    return dedent(f"""\
        {type(filemanager).__name__} containing {len(filemanager)} files.
        Once downloaded, these files will be stored in {filemanager.basepath}.
        The files are arranged in a {filemanager.fileuri_array.shape} array, and each file contains a {filemanager.shape} data array."\
    """)


def save_dataset(dataset, asdf_path, overwrite=False):
        """
        Write a DKIST dataset to an ASDF file

        This function takes a `dkist.Dataset`, `dkist.TiledDataset` or
        `dkist.Inversion` object and saves it to a new file.

        Parameters
        ----------
        dataset : `dkist.Dataset`, `dkist.TiledDataset` or `dkist.Inversion`
            Level-1 or -2 dataset object to save

        asdf_path : Path or str
            Location to save the dataset to

        overwrite : bool
            If `True`, overwrites the existing file at `asdf_path`, otherwise raises `FileExistsError`.
            Default `False`.
        """
        from dkist.dataset import Inversion  # noqa: PLC0415

        if isinstance(asdf_path, str):
            asdf_path = Path(asdf_path)

        if not overwrite and asdf_path.exists():
            raise FileExistsError(f"ASDF file {asdf_path} already exists. Use overwrite=True to replace it.")

        asdf.AsdfFile({"inversion" if isinstance(dataset, Inversion) else "dataset": dataset}).write_to(asdf_path)
