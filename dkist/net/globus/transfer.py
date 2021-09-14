"""
Functions and helpers for orchestrating and monitoring transfers using Globus.
"""
import copy
import json
import time
import pathlib
import datetime

import globus_sdk
from parfive.utils import in_notebook
from tqdm import tqdm, tqdm_notebook

from .endpoints import auto_activate_endpoint, get_endpoint_id, get_transfer_client

__all__ = ['watch_transfer_progress', 'start_transfer_from_file_list']


def start_transfer_from_file_list(src_endpoint, dst_endpoint, dst_base_path, file_list,
                                  src_base_path=None):
    """
    Start a new transfer task for a list of files.

    Parameters
    ----------
    src_endpoint : `str`
        The endpoint to copy file from. Can be any identifier accepted by
        `~dkist.net.globus.get_endpoint_id`.

    dst_endpoint : `str`
        The endpoint to copy file to. Can be any identifier accepted by
        `~dkist.net.globus.get_endpoint_id`.

    dst_base_path : `~pathlib.Path`
        The destination path, must be accessible from the endpoint, will be
        created if it does not exist.

    file_list : `list`
        The list of file paths on the ``src_endpoint`` to transfer to the ``dst_endpoint``.

    src_base_path : `~pathlib.Path`, optional
        The path prefix on the items in ``file_list`` to be stripped before
        copying to ``dst_base_path``. i.e. if the file path in ``path_list`` is
        ``/spam/eggs/filename.fits`` and ``src_base_path`` is ``/spam`` the
        ``eggs/`` folder will be copied to ``dst_base_path``. By default only
        the filenames are kept, and none of the directories.

    Returns
    -------
    `str`
        Task ID.
    """

    # Get a transfer client instance
    tc = get_transfer_client()

    # Resolve to IDs and activate endpoints
    src_endpoint = get_endpoint_id(src_endpoint, tc)
    auto_activate_endpoint(src_endpoint, tc)

    dst_endpoint = get_endpoint_id(dst_endpoint, tc)
    auto_activate_endpoint(dst_endpoint, tc)

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    transfer_manifest = globus_sdk.TransferData(tc, src_endpoint, dst_endpoint,
                                                label=f"DKIST Python Tools - {now}",
                                                sync_level="checksum",
                                                verify_checksum=True)

    dst_base_path = pathlib.Path(dst_base_path)
    src_file_list = copy.copy(file_list)
    dst_file_list = []
    for src_file in src_file_list:
        # If a common prefix is not specified just copy the filename
        if not src_base_path:
            src_filepath = src_file.name
        else:
            # Otherwise use the filepath relative to the base path
            src_filepath = src_file.relative_to(src_base_path)
        dst_file_list.append(dst_base_path / src_filepath)

    for src_file, dst_file in zip(src_file_list, dst_file_list):
        transfer_manifest.add_item(str(src_file), str(dst_file))

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
    events = set(map(lambda x: tuple(x.data.items()),
                     tfr_client.task_event_list(task_id, None)))
    # Drop all events we have seen before
    new_events = events.difference(prev_events)

    # Filter out the events which are json (start with {)
    json_events = set(filter(lambda x: dict(x).get("details", "").startswith("{"), new_events))
    # All the other events are message events
    message_events = tuple(map(dict, (new_events.difference(json_events))))

    def json_loader(x):
        """Modify the event so the json is a dict."""
        x['details'] = json.loads(x['details'])
        return x

    # If some of the events are json events, load the json.
    if json_events:
        json_events = tuple(map(dict, map(json_loader, map(dict, json_events))))
    else:
        json_events = tuple()

    return events, json_events, message_events


def _get_speed(event):
    """
    A helper function to extract the speed from an event.
    """
    if event.get('code', "").lower() == "progress" and isinstance(event['details'], dict):
        return event['details'].get("mbps")


def get_progress_bar(*args, **kwargs):  # pragma: no cover
    """
    Return the correct tqdm instance.
    """
    notebook = in_notebook()
    if not notebook:
        kwargs['bar_format'] = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}]'
    else:
        # TODO: Both having this and not having it breaks things.
        kwargs['total'] = kwargs.get("total", 1e9) or 1e9
    the_tqdm = tqdm if not in_notebook() else tqdm_notebook
    return the_tqdm(*args, **kwargs)


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
    while True:
        (prev_events,
         json_events,
         message_events) = _process_task_events(task_id, prev_events, tfr_client)

        if ('code', 'STARTED') not in prev_events and not started:
            started = True
            progress.write("PENDING: Starting Transfer")

        # Print status messages if verbose or if they are errors
        for event in message_events:
            if event['is_error'] or verbose:
                progress.write(f"{event['code']}: {event['details']}")

        # Extract and calculate the transfer speed from the event list
        speed = (list(map(_get_speed, json_events)) or [None])[0]
        speed = f"{speed} Mb/s" if speed else ""
        if speed:
            progress.set_postfix_str(speed)

        # Get the status of the task to see how many files we have processed.
        task = tfr_client.get_task(task_id)
        status = task['status']
        progress.total = task['files']
        progress.update((task['files_skipped'] + task['files_transferred']) - progress.n)

        # If the status of the task is not active we are finished.
        if status != "ACTIVE":
            progress.write(f"Task completed with {status} status.")
            progress.close()
            break

        # Wait for next poll
        time.sleep(poll_interval)
