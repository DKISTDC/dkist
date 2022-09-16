"""
Functions and classes for searching and downloading from the data center.
"""
import datetime
from os import PathLike
from typing import List, Union, Literal, Optional
from pathlib import Path

from astropy import table
from sunpy.net.base_client import QueryResponseRow
from sunpy.net.fido_factory import UnifiedResponse

from dkist.net.attrs import Dataset
from dkist.net.client import DKISTClient, DKISTQueryResponseTable
from dkist.net.globus.transfer import _orchestrate_transfer_task

__all__ = ["transfer_complete_datasets"]


def _get_dataset_inventory(dataset_id: str):  # pragma: no cover
    """
    Do a search for a single dataset id
    """
    results = DKISTClient().search(Dataset(dataset_id))
    if len(results) == 0:
        raise ValueError(f"No results available for dataset {dataset_id}")

    return results


def transfer_complete_datasets(datasets: Union[str, QueryResponseRow, DKISTQueryResponseTable, UnifiedResponse],
                               path: PathLike = "/~/",
                               destination_endpoint: str = None,
                               progress: Union[bool, Literal["verbose"]] = True,
                               wait: bool = True,
                               label: Optional[str] = None) -> Union[List[str], str]:
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
       If `True` (the default) the function will wait for the Globus transfer
       task to complete before processing the next dataset or returning from the
       function. To run multiple dataset transfer tasks in parallel (one task per
       dataset) specify ``wait=False``.

    label : `str`
        Label for the Globus transfer. If `None` then a default will be used.

    Returns
    -------
    The path to the directories containing the dataset(s) on the destination endpoint.

    """
    # Avoid circular import
    from dkist.net import conf

    if isinstance(datasets, str):
        datasets = _get_dataset_inventory(datasets)[0]

    # If we have a UnifiedResponse object, it could contain one or more dkist tables.
    # Stack them and then treat them like we were passed a single table with many rows.
    if isinstance(datasets, UnifiedResponse):
        datasets = datasets["dkist"]
        if len(datasets) > 1:
            datasets = table.vstack(datasets, metadata_conflicts="silent")

    if isinstance(datasets, DKISTQueryResponseTable) and len(datasets) > 1:
        paths = []
        for record in datasets:
            paths.append(transfer_complete_datasets(record,
                                                    path=path,
                                                    destination_endpoint=destination_endpoint,
                                                    progress=progress,
                                                    wait=wait,
                                                    label=label))
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

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M")
    label = f"DKIST Python Tools - {now} {dataset_id}" if label is None else label

    _orchestrate_transfer_task(file_list,
                               recursive=True,
                               destination_path=destination_path,
                               destination_endpoint=destination_endpoint,
                               progress=progress,
                               wait=wait,
                               label=label)

    return destination_path / dataset_id
