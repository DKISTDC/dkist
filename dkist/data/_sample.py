import os
import tarfile
from pathlib import Path
from urllib.parse import urljoin

from parfive import Downloader, Results

from astropy.io import fits

from dkist import conf

VISP_HEADER = fits.Header.fromtextfile(Path(__file__).parent / "VISP_HEADER.hdr")
_BASE_URL = "https://g-a36282.cd214.a567.data.globus.org/user_tools_tutorial_data/test/"
_SAMPLE_DATASETS = {
    "VISP_L1_KMUPT": (_BASE_URL, "BKPLX_stokesI.tar"),
    "VBI_L1_NZJTB": (_BASE_URL, "YCDRFH_single_mosaic.tar"),
    "CRYO_L1_TJKGC": (_BASE_URL, "DBXVEL_full.tar"),
    "CRYO_L1_MSCGD": (_BASE_URL, "POKNUM_first_step.tar"),
}
_DEPRECATED_NAMES = {
    "VISP_BKPLX": "VISP_L1_KMUPT",
    "VBI_AJQWW": "VBI_L1_NZJTB",
}


def _download_and_extract_sample_data(names, overwrite, path):
    """
    Downloads a list of files.

    Parameters
    ----------
    names : list[str]
        The names of the datasets to download and extract
    overwrite : bool
        Will overwrite a file on disk if True.
    path : `pathlib.Path`
        The sample data path to save the tar files

    Returns
    -------
    `parfive.Results`
        Download results. Will behave like a list of files.
    """
    dl = Downloader(overwrite=overwrite, progress=True)

    existing_files = []

    for name in names:
        base_url, filename = _SAMPLE_DATASETS[name]
        if (filepath := path / filename).exists():
            existing_files.append(filepath)
            continue

        url = urljoin(base_url, filename)
        dl.enqueue_file(url, path=path)

    results = Results()
    if dl.queued_downloads:
        results = dl.download()
    results += existing_files

    file_folder = {filename: name for name, (_, filename) in _SAMPLE_DATASETS.items() if name in names}

    for i, tarpath in enumerate(results):
        output_path = path / file_folder[Path(tarpath).name]
        with tarfile.open(tarpath, "r:*") as tar:
            tar.extractall(path=output_path, filter=tarfile.fully_trusted_filter)
        results[i] = output_path

    return results


def _get_sample_datasets(dataset_names, no_download=False, force_download=False):
    """
    Returns a list of disk locations corresponding to a list of filenames for
    sample data, downloading the sample data files as necessary.

    Parameters
    ----------
    no_download : `bool`
        If ``True``, do not download any files, even if they are not present.
        Default is ``False``.
    force_download : `bool`
        If ``True``, download all files, and overwrite any existing ones.
        Default is ``False``.

    Returns
    -------
    `list` of `pathlib.Path`
        List of disk locations corresponding to the list of filenames.  An entry
        will be ``None`` if ``no_download == True`` and the file is not present.

    Raises
    ------
    RuntimeError
        Raised if any of the files cannot be downloaded from any of the mirrors.
    """
    sampledata_dir = Path(conf.sample_data_directory)
    if env_override := os.environ.get("DKIST_SAMPLE_DIR"):
        # For some reason, RTD adds ' around the path in the env var.
        sampledata_dir = Path(env_override.strip("'"))
    sampledata_dir = sampledata_dir.expanduser()

    datasets = dict((k,v) for k, v in _SAMPLE_DATASETS.items() if k in dataset_names)  # noqa: C402
    download_paths = [sampledata_dir / fn for _, fn in datasets.values()]

    if no_download:
        return [sampledata_dir / name for name in datasets.keys() if (sampledata_dir / name).exists()]

    results = _download_and_extract_sample_data(datasets.keys(), overwrite=force_download, path=sampledata_dir)

    if results.errors:
        raise RuntimeError(
            f"{len(results.errors)} sample data files failed "
            "to download, the first error is above.") from results.errors[0].exception

    return list(results)
