"""
Functions and helpers for orchestrating and monitoring transfers using Globus.
"""
import json
import time
import pathlib
import datetime
from os import PathLike
from typing import Literal

import globus_sdk
from tqdm.auto import tqdm
from tqdm.notebook import tqdm as tqdm_notebook

from .endpoints import (auto_activate_endpoint, get_data_center_endpoint_id,
                        get_endpoint_id, get_local_endpoint_id, get_transfer_client)

__all__ = ["start_transfer_from_file_list", "watch_transfer_progress"]


def start_transfer_from_file_list(
    src_endpoint: str,
    dst_endpoint: str,
    dst_base_path: PathLike,
    file_list: list[PathLike],
    src_base_path: PathLike = None,
    recursive: bool | list[bool] = False,
    label: str = None
) -> str:
    """
    Start a new transfer task for a list of files.

    Parameters
    ----------
    src_endpoint
        The endpoint to copy file from. Can be any identifier accepted by
        `~dkist.net.globus.get_endpoint_id`.

    dst_endpoint
        The endpoint to copy file to. Can be any identifier accepted by
        `~dkist.net.globus.get_endpoint_id`.

    dst_base_path
        The destination path, must be accessible from the endpoint, will be
        created if it does not exist.

    file_list
        The list of file paths on the ``src_endpoint`` to transfer to the ``dst_endpoint``.

    src_base_path
        The path prefix on the items in ``file_list`` to be stripped before
        copying to ``dst_base_path``. i.e. if the file path in ``path_list`` is
        ``/spam/eggs/filename.fits`` and ``src_base_path`` is ``/spam`` the
        ``eggs/`` folder will be copied to ``dst_base_path``. By default only
        the filenames are kept, and none of the directories.

    recursive
       Controls if the path in ``file_list`` is added to the Globus task with
       the recursive flag or not.
       This should be `True` if the element of ``file_list`` is a directory.
       If you need to set this per-item in ``file_list`` it should be a `list`
       of `bool` of equal length as ``file_list``.

    label
       Label for the Globus transfer. If None then a default will be used.

    Returns
    -------
    `str`
        Task ID.
    """
    if isinstance(recursive, bool):
        recursive = [recursive] * len(file_list)
    if len(recursive) != len(file_list):
        raise ValueError(
            "The length of recursive should equal the length of file_list when specified as a list."
        )

    # Get a transfer client instance
    tc = get_transfer_client()

    # Resolve to IDs and activate endpoints
    src_endpoint = get_endpoint_id(src_endpoint, tc)
    auto_activate_endpoint(src_endpoint, tc)

    dst_endpoint = get_endpoint_id(dst_endpoint, tc)
    auto_activate_endpoint(dst_endpoint, tc)

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M")
    label = f"DKIST Python Tools - {now}" if label is None else label
    transfer_manifest = globus_sdk.TransferData(tc, src_endpoint, dst_endpoint,
                                                label=label,
                                                sync_level="checksum",
                                                verify_checksum=True)

    src_file_list = file_list
    if not isinstance(dst_base_path, (list, tuple)):
        dst_base_path = pathlib.Path(dst_base_path)
        dst_file_list = []
        for src_file in src_file_list:
            # If a common prefix is not specified just copy the filename or last directory
            if not src_base_path:
                src_filepath = src_file.name
            else:
                # Otherwise use the filepath relative to the base path
                src_filepath = src_file.relative_to(src_base_path)
            dst_file_list.append(dst_base_path / src_filepath)
    else:
        dst_file_list = dst_base_path

    for src_file, dst_file, rec in zip(src_file_list, dst_file_list, recursive):
        transfer_manifest.add_item(src_file.as_posix(), dst_file.as_posix(), recursive=rec)

    return tc.submit_transfer(transfer_manifest)["task_id"]


def _process_task_events(task_id, prev_events, tfr_client):
    """
    Process a globus task event list.

    This splits the events up into message events, which are events where the
    details field is a string, and json events, which is where the details
    field is a json object.

    Parameters
    ----------
    prev_events : `set`
        A set of already processed events.

    tfr_client : `globus_sdk.TransferClient`
        The transfer client to use to get the events.

    Returns
    -------
    prev_events : `set`
        The complete list of all event processed so far.

    json_events : `tuple` of `dict`
        All the events with json bodies.

    message_events : `tuple` of `dict`
        All the events with message bodies.
    """

    # Convert all the events into a (key, value) tuple pair
    events = {tuple(x.items()) for x in tfr_client.task_event_list(task_id)}
    # Drop all events we have seen before
    new_events = events.difference(prev_events)

    # Filter out the events which are json (start with {)
    json_events = set(filter(lambda x: dict(x).get("details", "").startswith("{"), new_events))
    # All the other events are message events
    message_events = tuple(map(dict, (new_events.difference(json_events))))

    def json_loader(x):
        """Modify the event so the json is a dict."""
        x["details"] = json.loads(x["details"])
        return x

    # If some of the events are json events, load the json.
    if json_events:
        json_events = tuple(map(dict, map(json_loader, map(dict, json_events))))
    else:
        json_events = ()

    return events, json_events, message_events


def _get_speed(event):
    """
    A helper function to extract the speed from an event.
    """
    if event.get("code", "").lower() == "progress" and isinstance(event["details"], dict):
        return event["details"].get("mbps")


def get_progress_bar(*args, **kwargs):  # pragma: no cover
    """
    Return the correct tqdm instance.
    """
    notebook = tqdm is tqdm_notebook
    if not notebook:
        kwargs["bar_format"] = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}]"
    else:
        # TODO: Both having this and not having it breaks things.
        kwargs["total"] = kwargs.get("total", 1e9) or 1e9
    return tqdm(*args, **kwargs)


def watch_transfer_progress(task_id, tfr_client, poll_interval=5,
                            verbose=False, initial_n=None):  # pragma: no cover
    """
    Wait for a Globus transfer task to finish and display a progress bar.

    Parameters
    ----------
    task_id : `str`
        The task to monitor.

    tfr_client : `globus_sdk.TransferClient`
        The transfer client to use to monitor the task.

    poll_interval : `int`, optional
        The number of seconds to wait between API calls.

    verbose : `bool`
        If `True` print all events received from Globus, defaults to `False`
        which just prints Error events.
    """
    started = False
    prev_events = set()
    progress = None
    progress = get_progress_bar(unit="file",
                                dynamic_ncols=True,
                                total=initial_n)

    try:
        while True:
            (prev_events,
             json_events,
             message_events) = _process_task_events(task_id, prev_events, tfr_client)

            if ("code", "STARTED") not in prev_events and not started:
                started = True
                progress.write("PENDING: Starting Transfer")

            # Print status messages if verbose or if they are errors
            for event in message_events:
                if event["is_error"] or verbose:
                    progress.write(f"{event['code']}: {event['details']}")

            for event in json_events:
                # This block was coded off one example, as I can't find any
                # documentation of the structure of events. This is why it's
                # all very tolerant of missing keys etc.
                if event["is_error"] or verbose:
                    progress.write(f"{event.get('code', '')}: {event.get('description', '')}")
                    details = event.get("details", {})
                    if "error" in details and "body" in details["error"]:
                        extra_message = details["error"]["body"]
                        if "context" in details:
                            context = details["context"][0]
                            operation = context.get("operation", "")
                            path = context.get("path", "")
                            extra_message = f"{operation} | {path}".strip() + " | " + extra_message
                        progress.write(extra_message)

            # Extract and calculate the transfer speed from the event list
            speed = (list(map(_get_speed, json_events)) or [None])[0]
            speed = f"{speed} Mb/s" if speed else ""
            if speed:
                progress.set_postfix_str(speed)

            # Get the status of the task to see how many files we have processed.
            task = tfr_client.get_task(task_id)
            status = task["status"]
            progress.total = task["files"]
            progress.update((task["files_skipped"] + task["files_transferred"]) - progress.n)

            # If the status of the task is not active we are finished.
            if status != "ACTIVE":
                progress.write(f"Task completed with {status} status.")
                progress.close()
                break

            # Wait for next poll
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        progress.write("Cancelling Task")
        task = tfr_client.cancel_task(task_id)
        progress.close()


def _orchestrate_transfer_task(file_list: list[PathLike],
                               recursive: list[bool],
                               destination_path: PathLike | list[PathLike] = "/~/",
                               destination_endpoint: str = None,
                               *,
                               progress: bool | Literal["verbose"] = True,
                               wait: bool = True,
                               label: str = None):
    """
    Transfer the files given in file_list to the path on ``destination_endpoint``.

    Parameters
    ----------
    file_list
        The list of file paths on the source endpoint to transfer to the
        ``destination_endpoint``.

    recursive
       Controls if the path in ``file_list`` is added to the Globus task with
       the recursive flag or not.

    destination_path
        The path to the directory containing the dataset on the destination
        endpoint.

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
        This keyword is only used if ``wait=True``.

    wait
       If `False` then the function will return while the Globus transfer task
       is still running. Setting ``wait=False`` implies ``progress=False``.

    label : `str`
       Label for the Globus transfer. If `None` then a default will be used.

    Returns
    -------
    destination_path
        The path to the directory containing the dataset on the destination
        endpoint.

    """

    if not destination_endpoint:
        destination_endpoint = get_local_endpoint_id()

    task_id = start_transfer_from_file_list(get_data_center_endpoint_id(),
                                            destination_endpoint,
                                            destination_path,
                                            file_list,
                                            recursive=recursive,
                                            label=label)

    tc = get_transfer_client()

    if wait:
        if progress:
            watch_transfer_progress(task_id,
                                    tc,
                                    verbose=progress == "verbose")
        else:
            tc.task_wait(task_id, timeout=1e6)

    return destination_path
