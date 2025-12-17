import copy

import pytest

from dkist.data.test import rootdir


@pytest.fixture(params=[
                        rootdir / "eit_dataset-0.1.0.asdf",
                        rootdir / "eit_dataset-0.2.0.asdf",
                        rootdir / "eit_dataset-0.3.0.asdf",
                        rootdir / "eit_dataset-1.0.0.asdf",
                        rootdir / "eit_dataset-1.1.0.asdf",
                        rootdir / "eit_dataset-1.2.0.asdf",
])
def eit_dataset_asdf_path(request):
    return request.param


@pytest.fixture(params=[
                        rootdir / "test_tiled_dataset-1.0.0_dataset-1.0.0.asdf",
                        rootdir / "test_tiled_dataset-1.0.0_dataset-1.1.0.asdf",
                        rootdir / "test_tiled_dataset-1.0.0_dataset-1.2.0.asdf",
                        rootdir / "test_tiled_dataset-1.1.0_dataset-1.2.0.asdf",
                        rootdir / "test_tiled_dataset-1.2.0_dataset-1.2.0.asdf",
                        rootdir / "test_tiled_dataset-1.3.0_dataset-1.2.0.asdf",
])
def tiled_dataset_asdf_path(request):
    return request.param


@pytest.fixture
def break_manifest():
    mandir = rootdir.parent.parent / "io" / "asdf" / "resources" / "manifests"
    latest_dkist_manifest = sorted(mandir.glob("dkist-?.*.*.yaml"))[-1]
    # Fudge the version in the latest manifest file
    with open(latest_dkist_manifest, mode="r+", encoding="utf-8") as f:
        oldlines = f.readlines()
        newlines = copy.copy(oldlines)
        newlines[2] = newlines[2].replace(latest_dkist_manifest.name[-10:-5], "9.9.9")
        newlines[3] = newlines[3].replace(latest_dkist_manifest.name[-10:-5], "9.9.9")
        f.seek(0)
        f.write("".join(newlines))
    yield
    with open(latest_dkist_manifest, mode="w", encoding="utf-8") as f:
        f.write("".join(oldlines))


@pytest.fixture
def orphan_schema():
    # Create a schema file that isn't listed anywhere else
    orphan_schema = rootdir.parent.parent / "io" / "asdf" / "resources" / "schemas" / "null-0.1.0.yaml"
    with open(orphan_schema, "w") as f:
        f.writelines([
            "%YAML 1.1\n",
            "---\n",
            '$schema: "http://stsci.edu/schemas/yaml-schema/draft-01"\n',
            'id: "asdf://dkist.nso.edu/schemas/null-0.99.0"\n',
        ])
    yield
    orphan_schema.unlink()
