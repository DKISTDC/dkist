"""
Functions and classes for searching and downloading from the data center.
"""
import datetime
from os import PathLike
from typing import Literal
from pathlib import Path
from collections.abc import Iterable

from astropy import table

from sunpy.net.attr import or_
from sunpy.net.base_client import QueryResponseRow
from sunpy.net.fido_factory import UnifiedResponse

from dkist.net import conf
from dkist.net.attrs import Dataset
from dkist.net.client import DKISTClient, DKISTQueryResponseTable
from dkist.net.globus.transfer import _orchestrate_transfer_task
from dkist.utils.inventory import path_format_inventory

__all__ = ["transfer_complete_datasets"]


def _get_dataset_inventory(dataset_id: str | Iterable[str]) -> DKISTQueryResponseTable:  # pragma: no cover
    """
    Do a search for a single dataset id
    """
    if isinstance(dataset_id, str):
        search = Dataset(dataset_id)
    else:
        search = or_(*[Dataset(d) for d in dataset_id])
    results = DKISTClient().search(search)
    if len(results) == 0:
        raise ValueError(f"No results available for dataset {dataset_id}")
    return results


def _get_globus_path_for_dataset(dataset: QueryResponseRow):
    """
    Given a dataset ID get the directory on the source endpoint.
    """
    if not isinstance(dataset, QueryResponseRow):
        raise TypeError("Input should be a single row of dataset inventory.")

    # At this point we only have one dataset, and it should be a row not a table
    dataset_id = dataset["Dataset ID"]
    proposal_id = dataset["Primary Proposal ID"]
    bucket = dataset["Storage Bucket"]

    return Path(conf.dataset_path.format(
        datasetId=dataset_id,
        primaryProposalId=proposal_id,
        bucket=bucket
    ))


def transfer_complete_datasets(datasets: str | Iterable[str] | QueryResponseRow | DKISTQueryResponseTable | UnifiedResponse,
                               path: PathLike = "/~/",
                               destination_endpoint: str = None,
                               progress: bool | Literal["verbose"] = True,
                               wait: bool = True,
                               label: str | None = None) -> list[str] | str:
    """
    Transfer one or more complete datasets to a path on a globus endpoint.

    Parameters
    ----------
    dataset
        The dataset to transfer. This can either be a string dataset id, or it
        can be a table or a row from the search results returned by a call to
        ``Fido.search``.

    path
        The path to save the data in, must be accessible by the Globus endpoint.
        The default value is ``/~/``.  It is possible to put placeholder strings
        in the path with any key from inventory which can be shown with
        :meth:`dkist.utils.inventory.path_format_keys`.  An example of this
        would be ``path="~/dkist/{primary_proposal_id}"`` to save the files in a
        folder named for the proposal id.  **Note** that ``{dataset_id}`` is
        always added to the path if it is not already the last element.

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
    path = Path(path)
    if path.parts[-1] != "{dataset_id}":
        path = path / "{dataset_id}"

    if isinstance(datasets, DKISTQueryResponseTable):
        # This we don't have to pre-process
        pass

    elif isinstance(datasets, QueryResponseRow):
        datasets = DKISTQueryResponseTable(datasets)

    elif isinstance(datasets, UnifiedResponse):
        # If we have a UnifiedResponse object, it could contain one or more dkist tables.
        # Stack them and then treat them like we were passed a single table with many rows.
        datasets = datasets["dkist"]
        if isinstance(datasets, UnifiedResponse) and len(datasets) > 1:
            datasets = table.vstack(datasets, metadata_conflicts="silent")

    elif isinstance(datasets, str) or all(isinstance(d, str) for d in datasets):
        # If we are passed just dataset IDs as strings search for them to get the inventory records
        datasets = _get_dataset_inventory(datasets)

    else:
        # Anything else, error
        raise TypeError(f"{type(datasets)} is of an unknown type, it should be search results or one or more dataset IDs.")


    source_paths = []
    for record in datasets:
        source_paths.append(_get_globus_path_for_dataset(record))

    destination_paths = []
    for dataset in datasets:
        dataset_id = dataset["Dataset ID"]
        proposal_id = dataset["Primary Proposal ID"]
        bucket = dataset["Storage Bucket"]

        path_inv = path_format_inventory(dict(dataset))
        destination_paths.append(Path(str(path).format(**path_inv)))

    if not label:
        now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M")
        datasetids = ",".join(datasets["Dataset ID"])
        if len(datasetids) > 80:
            datasetids = f"{len(datasets['Dataset ID'])} datasets"
        label = f"DKIST Python Tools - {now} - {datasetids}"

    # Globus limits labels to 128 characters, so truncate if needed
    # In principle this can't happen because of the truncation above, but just in case
    if len(label) > 128:
        label = label[:125] + "..."  # pragma: no cover

    _orchestrate_transfer_task(source_paths,
                               recursive=True,
                               destination_path=destination_paths,
                               destination_endpoint=destination_endpoint,
                               progress=progress,
                               wait=wait,
                               label=label)

    return destination_paths
