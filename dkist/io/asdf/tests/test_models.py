import numpy as np

import astropy.units as u
from asdf.testing.helpers import roundtrip_object
from astropy.coordinates.matrix_utilities import rotation_matrix

from dkist.wcs.models import VaryingCelestialTransform


def test_roundtrip_vct():
    varying_matrix_lt = [rotation_matrix(a)[:2, :2]
                         for a in np.linspace(0, 90, 10)] * u.arcsec

    vct = VaryingCelestialTransform(crpix=(5, 5) * u.pix,
                                    cdelt=(1, 1) * u.arcsec/u.pix,
                                    crval_table=(0, 0) * u.arcsec,
                                    pc_table=varying_matrix_lt,
                                    lon_pole=180 * u.deg)
    new_vct = roundtrip_object(vct)
    new_ivct = roundtrip_object(vct.inverse)

    assert u.allclose(u.Quantity(new_vct.crpix), (5, 5) * u.pix)
    assert u.allclose(u.Quantity(new_ivct.crpix), (5, 5) * u.pix)

    assert u.allclose(u.Quantity(new_vct.pc_table), varying_matrix_lt)
    assert u.allclose(u.Quantity(new_ivct.pc_table), varying_matrix_lt)

    pixel = (0*u.pix, 0*u.pix, 5*u.pix)
    world = new_vct(*pixel)
    assert u.allclose(world, (359.99804329*u.deg, 0.00017119*u.deg))

    assert u.allclose(new_ivct.inverse(*world, 5*u.pix), pixel[:2], atol=0.01*u.pix)
