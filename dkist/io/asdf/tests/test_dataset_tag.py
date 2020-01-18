import pytest

from asdf.tests import helpers

from dkist.io import AstropyFITSLoader, DaskFITSArrayContainer


@pytest.fixture
def tagobj(request):
    """
    A fixture to lookup other fixtures.
    """
    return request.getfixturevalue(request.param)


@pytest.fixture
def array_container():
    return DaskFITSArrayContainer(['test1.fits', 'test2.fits'], 0, 'float', (10, 10),
                                  loader=AstropyFITSLoader)


@pytest.mark.parametrize("tagobj",
                         ["array_container",
                          "dataset"],
                         indirect=True)
def test_tags(tagobj, tmpdir):
    tree = {'object': tagobj}
    helpers.assert_roundtrip_tree(tree, tmpdir)
