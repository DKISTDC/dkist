"""
Shared pytest fixtures.
"""

import pytest

import astropy.units as u
from astropy.modeling.models import Identity, Multiply, Pix2Sky_AZP, Shift


@pytest.fixture
def double_input_flat():
    return (Identity(1) | Identity(1)) & Identity(1)


@pytest.fixture
def triple_input_flat():
    return Identity(1) & Identity(1) & Identity(1)


@pytest.fixture
def triple_input_nested():
    return (Identity(1) | Identity(1) | Identity(1)) & (Identity(1) | Identity(1)) & Identity(1)


@pytest.fixture
def single_non_separable():
    return Pix2Sky_AZP() | Identity(2)


@pytest.fixture
def double_non_separable():
    return (Pix2Sky_AZP() | Identity(2)) & Identity(1)


def spatial_like_model():
    crpix1, crpix2 = (100, 100) * u.pix
    cdelt1, cdelt2 = (10, 10) * (u.arcsec / u.pix)

    shiftu = Shift(-crpix1) & Shift(-crpix2)
    scale = Multiply(cdelt1) & Multiply(cdelt2)

    return (shiftu | scale | Pix2Sky_AZP()) & Identity(1)


@pytest.fixture
def spatial_like():
    return spatial_like_model()
