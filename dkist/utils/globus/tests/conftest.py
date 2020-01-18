
import pytest

from dkist.utils.globus.endpoints import get_transfer_client


@pytest.fixture()
def transfer_client(mocker):
    mocker.patch("globus_sdk.TransferClient.get_submission_id",
                 return_value={'value': "1234"})

    tc = get_transfer_client()

    mocker.patch("dkist.utils.globus.endpoints.get_transfer_client",
                 return_value=tc)
    mocker.patch("dkist.utils.globus.transfer.get_transfer_client",
                 return_value=tc)
    mocker.patch("dkist.utils.globus.auth.get_refresh_token_authorizer",
                 return_value=None)
    return tc
