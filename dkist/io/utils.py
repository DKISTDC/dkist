from pathlib import Path
from textwrap import dedent

import asdf

__all__ = ["filemanager_info_str"]


def filemanager_info_str(filemanager):
    return dedent(f"""\
        {type(filemanager).__name__} containing {len(filemanager)} files.
        Once downloaded, these files will be stored in {filemanager.basepath}.
        The files are arranged in a {filemanager.fileuri_array.shape} array, and each file contains a {filemanager.shape} data array."\
    """)


def save_asdf(dataset, asdf_path, overwrite=False):
        """
        Writes a dataset to an asdf file
        """
        ## TODO better docstring
        from dkist.dataset import Inversion  # noqa: PLC0415

        if isinstance(asdf_path, str):
            asdf_path = Path(asdf_path)

        if not overwrite and asdf_path.exists():
            raise FileExistsError(f"ASDF file {asdf_path} already exists. Use overwrite=True to replace it.")

        ## TODO validate?
        asdf.AsdfFile({"inversion" if isinstance(dataset, Inversion) else "dataset": dataset}).write_to(asdf_path)
        ## TODO Create links to fits files if dir is different to original basepath?
