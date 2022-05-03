"""
Functions and classes for searching and downloading from the data center.
"""
from os import PathLike
from typing import List, Union, Literal
from pathlib import Path

from sunpy.net.base_client import QueryResponseRow

from dkist.net.attrs import Dataset
from dkist.net.client import DKISTClient, DKISTQueryResponseTable
from dkist.net.globus.transfer import _orchestrate_transfer_task

__all__ = ["transfer_complete_datasets"]


def _get_dataset_inventory(dataset_id: str):  # pragma: no cover
    """
    Do a search for a single dataset id
    """
    return DKISTClient().search(Dataset(dataset_id))


def transfer_complete_datasets(datasets: Union[str, QueryResponseRow, DKISTQueryResponseTable],
                               path: PathLike = "/~/",
                               destination_endpoint: str = None,
                               progress: Union[bool, Literal["verbose"]] = True,
                               wait: bool = True) -> Union[List[str], str]:
    """
    Transfer one or more complete datasets to a path on a globus endpoint.

    Parameters
    ----------
    dataset
        The dataset to transfer. This can either be a string dataset id, or it
        can be a table or a row from the search results returned by a call to
        ``Fido.search``.

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
    The path to the directory containing the dataset on the destination endpoint.

    """
    # Avoid circular import
    from dkist.net import conf

    if isinstance(datasets, str):
        datasets = _get_dataset_inventory(datasets)[0]

    if isinstance(datasets, DKISTQueryResponseTable) and len(datasets) > 1:
        paths = []
        for record in datasets:
            paths.append(transfer_complete_datasets(record,
                                                    path=path,
                                                    destination_endpoint=destination_endpoint,
                                                    progress=progress,
                                                    wait=wait))
        return paths

    # At this point we only have one dataset
    dataset = datasets
    dataset_id = dataset["Dataset ID"]
    proposal_id = dataset["Primary Proposal ID"]
    bucket = dataset["Storage Bucket"]

    destination_path = Path(path) / proposal_id

    file_list = [Path(conf.dataset_path.format(
        datasetId=dataset_id,
        primaryProposalId=proposal_id,
        bucket=bucket
    ))]

    _orchestrate_transfer_task(file_list,
                               recursive=True,
                               destination_path=destination_path,
                               destination_endpoint=destination_endpoint,
                               progress=progress,
                               wait=wait)

    return destination_path / dataset_id
