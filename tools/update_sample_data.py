# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy",
#   "astropy",
#   "sunpy[net]",
#   "dkist",
# ]
# ///
"""
This script recreates the sample data files and uploads the recreated versions to Asgard.
"""
import sys
import tarfile
import argparse
from pathlib import Path

import numpy as np

from sunpy.net import Fido
from sunpy.net import attrs as a

import dkist
import dkist.net
from dkist.net.globus import start_transfer_from_file_list, watch_transfer_progress
from dkist.net.globus.endpoints import get_local_endpoint_id, get_transfer_client

datasets = {
    "AJQWW": {
        "tiled": True,
        "tile_slice": np.s_[0],
        "filename": "AJQWW_single_mosaic.tar",
    },
    "YCDRFH": {
        "tiled": True,
        "tile_slice": np.s_[0],
        "filename": "YCDRFH_single_mosaic.tar",
    },
    "BKPLX": {
        "tiled": False,
        "slice": np.s_[0],
        "filename": "BKPLX_stokesI.tar",
    },
    "DBXVEL": {
        "tiled": False,
        "filename": "DBXVEL_full.tar",
    },
    "POKNUM": {
        "tiled": False,
        "slice": np.s_[0],
        "filename": "POKNUM_first_step.tar",
    },
}

def main(datasets, working_directory, destination_path="/user_tools_tutorial_data/"):
    working_directory = Path(working_directory)
    working_directory.mkdir(parents=True, exist_ok=True)
    sample_files_for_upload = []

    for did, props in datasets.items():
        res = Fido.search(a.dkist.Dataset(did), a.dkist.Status("any"))
        asdf_file = Fido.fetch(res, path=working_directory / "{dataset_id}", progress=False, overwrite=True)

        ds = dkist.load_dataset(asdf_file)
        if "slice" in props:
            ds = ds[props["slice"]]
        if "tile_slice" in props:
            ds = ds.slice_tiles[props["tile_slice"]]

        if props.get("tiled", False):
            for i, sds in enumerate(ds.flat):
                sds.files.download(path=working_directory / "{dataset_id}", wait=(i == (len(ds.flat) - 1)))
        else:
            ds.files.download(path=working_directory / "{dataset_id}", wait=True)

        dataset_path = working_directory / did
        # Remove the preview movie and quality report
        [f.unlink() for f in dataset_path.glob("*.mp4")]
        [f.unlink() for f in dataset_path.glob("*.pdf")]
        assert len(list(dataset_path.glob("*.asdf"))) == 1
        dataset_files = tuple(dataset_path.glob("*"))

        sample_filename = working_directory / props["filename"]
        with tarfile.open(sample_filename, mode="w") as tfile:
            for dfile in dataset_files:
                tfile.add(dfile, arcname=dfile.name, recursive=False)

        sample_files_for_upload.append(sample_filename)


    local_endpoint_id = get_local_endpoint_id()
    asgard_endpoint_id = "20fa4840-366a-494c-b009-063280ecf70d"

    resp = input(f"About to upload ({', '.join([f.name for f in sample_files_for_upload])}) to {destination_path} on Asgard. Are you sure? [y/N]")
    if resp.lower() == "y":
        task_id = start_transfer_from_file_list(
            local_endpoint_id,
            asgard_endpoint_id,
            dst_base_path=destination_path,
            file_list=sample_files_for_upload,
            label="Sample data upload to Asgard",
        )

        watch_transfer_progress(task_id, get_transfer_client(), verbose=True, initial_n=len(sample_files_for_upload))

if __name__ == "__main__":
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("working_dir", help="local directory to use to build the dataset files.")
    argp.add_argument(
        "--destination-dir",
        default="/user_tools_tutorial_data/test/",
        help="path to the destination directory on Asgard (defaults to '/user_tools_tutorial_data/test'"
             " so must be explicitly set to override production data)."
    )

    args = argp.parse_args(sys.argv[1:])

    main(datasets, args.working_dir, args.destination_dir)
