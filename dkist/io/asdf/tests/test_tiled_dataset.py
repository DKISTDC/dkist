import importlib.resources as importlib_resources

import asdf


def test_verify_tiled_dataset_schema(tiled_dataset_asdf_path):
    with importlib_resources.as_file(importlib_resources.files("dkist.io") / "level_1_dataset_schema.yaml") as schema_path:

        # Firstly verify that the tag versions in the test filename are the ones used in the file
        with asdf.open(tiled_dataset_asdf_path, _force_raw_types=True) as afile:
            assert afile["dataset"]._tag.rsplit("/")[-1] in str(tiled_dataset_asdf_path)
            assert afile["dataset"]["datasets"][0][0]._tag.rsplit("/")[-1] in str(tiled_dataset_asdf_path)
