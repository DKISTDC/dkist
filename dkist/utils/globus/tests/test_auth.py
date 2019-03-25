from unittest import mock

import pytest
import requests

from dkist.utils.globus.auth import start_local_server


def test_http_server():
    server = start_local_server()
