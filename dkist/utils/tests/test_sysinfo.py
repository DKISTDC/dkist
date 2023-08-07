import dkist


def test_system_info(capsys):
    """
    A very minimal test for system_info to test it runs.
    """
    dkist.system_info()
    captured_output = capsys.readouterr().out
    assert "dkist Installation Information" in captured_output
    assert f"dkist: {dkist.__version__}" in captured_output
