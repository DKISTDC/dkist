import pytest

import dkist.net.attrs as da


def test_embargoed_inputs():
    assert not da.Embargoed(False).value
    assert da.Embargoed(True).value
    assert not da.Embargoed("False").value
    assert da.Embargoed("True").value
    assert not da.Embargoed.false.value
    assert da.Embargoed.true.value

    with pytest.raises(ValueError, match="is_embargoed must be either True or False"):
        da.Embargoed("neither up nor down")

    with pytest.raises(ValueError, match="is_embargoed must be either True or False"):
        da.Embargoed(42)
