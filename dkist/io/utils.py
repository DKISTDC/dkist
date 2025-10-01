from textwrap import dedent

__all__ = ["filemanager_info_str"]


def filemanager_info_str(filemanager):
    return dedent(f"""\
        {type(filemanager).__name__} containing {len(filemanager)} files.
        Once downloaded, these files will be stored in {filemanager.basepath}.
        The files are arranged in a {filemanager.fileuri_array.shape} array, and each file contains a {filemanager.shape} data array."\
    """)
