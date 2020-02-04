import pytest

from sunpy.net import attrs as a

import dkist.net.attrs as da  # noqa
from dkist.net.client import DKISTDatasetClient


@pytest.fixture
def client():
    return DKISTDatasetClient()


# @pytest.mark.remote_data
def test_search(client):
    res = client.search(a.Time("2019/01/01", "2021/01/01"))
    print(res)
