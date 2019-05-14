# Licensed under a 3-clause BSD style license - see LICENSE.rst

# This sub-module is destined for common non-package specific utility
# functions.


def in_notebook():  # pragma: no cover
    """
    Attempts to detect if this python process is connected to a Jupyter Notebook.
    """
    try:
        import ipykernel.zmqshell
        shell = get_ipython()  # noqa
        if isinstance(shell, ipykernel.zmqshell.ZMQInteractiveShell):
            # Check that we can import the right widget
            from tqdm import _tqdm_notebook
            _tqdm_notebook.IntProgress
            return True
        return False
    except Exception:
        return False
