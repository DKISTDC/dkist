"""
Functions and classes for searching and downloading from the data center.
"""
from os import PathLike
from typing import Union, Literal
from pathlib import Path

from sunpy.net.base_client import QueryResponseRow

from dkist.net.attrs import Dataset
from dkist.net.client import DKISTClient
from dkist.net.globus import start_transfer_from_file_list, watch_transfer_progress
from dkist.net.globus.endpoints import (get_data_center_endpoint_id,
                                        get_local_endpoint_id, get_transfer_client)

__all__ = ['transfer_whole_dataset']


def _get_dataset_inventory(dataset_id: str):
    """
    Do a search for a single dataset id
    """
    return DKISTClient().search(Dataset(dataset_id))


def transfer_whole_dataset(dataset: Union[str, QueryResponseRow],
                           path: PathLike = "/~/",
                           destination_endpoint: str = None,
                           progress: Union[bool, Literal["verbose"]] = True,
                           wait: bool = True):
    """
    Transfer a whole dataset to a path on a globus endpoint.

    Parameters
    ----------
    dataset
        The dataset to transfer. This can either be a string dataset id, or it
        can be a single row from a `.DKISTQueryResponseTable` as returned in a
        call to ``Fido.search``.

    destination_endpoint
        A unique specifier for a Globus endpoint. If `None` a local
        endpoint will be used if it can be found, otherwise an error will
        be raised. See `~dkist.net.globus.get_endpoint_id` for valid
        endpoint specifiers.

    progress
        If `True` status information and a progress bar will be displayed
        while waiting for the transfer to complete.
        If ``progress="verbose"`` then all globus events generated during the
        transfer will be shown (by default only error messages are shown.)

    wait
       If `False` then the function will return while the Globus transfer task
       is still running. Setting ``wait=False`` implies ``progress=False``.

    Returns
    -------
    destination_path
        The path to the directory containing the dataset on the destination
        endpoint.

    """
    # Avoid circular import
    from dkist.net import conf

    if isinstance(dataset, str):
        dataset = _get_dataset_inventory(dataset)[0]

    dataset_id = dataset["Dataset ID"]
    proposal_id = dataset["Primary Proposal ID"]
    bucket = dataset["Storage Bucket"]

    if not destination_endpoint:
        destination_endpoint = get_local_endpoint_id()

    destination_path = Path(path) / proposal_id

    base_path = Path(conf.dataset_path.format(bucket=bucket,
                                              primaryProposalId=proposal_id,
                                              datasetId=dataset_id))

    task_id = start_transfer_from_file_list(get_data_center_endpoint_id(),
                                            destination_endpoint,
                                            destination_path,
                                            [base_path])

    tc = get_transfer_client()

    if wait:
        if progress:
            watch_transfer_progress(task_id, tc,
                                    verbose=progress == "verbose")
        else:
            tc.task_wait(task_id, timeout=1e6)

    return destination_path / dataset_id
