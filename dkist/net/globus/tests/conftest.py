
import pytest

from dkist.net.globus.endpoints import get_transfer_client


@pytest.fixture()
def transfer_client(mocker):
    mocker.patch("globus_sdk.TransferClient.get_submission_id",
                 return_value={'value': "1234"})

    mocker.patch("dkist.net.globus.endpoints.get_refresh_token_authorizer",
                 return_value={'transfer.api.globus.org': None})

    tc = get_transfer_client()

    mocker.patch("dkist.net.globus.endpoints.get_transfer_client",
                 return_value=tc)
    mocker.patch("dkist.net.globus.transfer.get_transfer_client",
                 return_value=tc)
    mocker.patch("dkist.net.globus.auth.get_refresh_token_authorizer",
                 return_value=None)
    return tc
