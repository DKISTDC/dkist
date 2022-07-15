from dkist.utils.inventory import dehumanize_inventory, humanize_inventory


def test_humanize_loop():
    inv = {
        "hasSpectralAxis": True,
        "notAKey": "wibble"
    }

    new_inv = humanize_inventory(inv)
    assert "Has Spectral Axis" in new_inv
    assert "hasSpectralAxis" not in new_inv
    assert "notAKey" in new_inv

    old_inv = dehumanize_inventory(new_inv)

    assert "Has Spectral Axis" not in old_inv
    assert "hasSpectralAxis" in old_inv
    assert "notAKey" in old_inv


    assert old_inv == inv
