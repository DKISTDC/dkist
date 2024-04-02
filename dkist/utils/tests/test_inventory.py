from dkist.data.test import rootdir
from dkist.net.client import DKISTQueryResponseTable
from dkist.utils.inventory import (_path_format_table, dehumanize_inventory,
                                   humanize_inventory, path_format_inventory)


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


def test_path_format_table():
    output = """<thead><tr><th>Inventory Keyword</th><th>Path Key</th></tr></thead>
<tr><td>asdfObjectKey</td><td>asdf_filename</td></tr>
<tr><td>boundingBox</td><td>bounding_box</td></tr>
<tr><td>browseMovieObjectKey</td><td>movie_filename</td></tr>
<tr><td>browseMovieUrl</td><td>preview_url</td></tr>
<tr><td>bucket</td><td>storage_bucket</td></tr>
<tr><td>contributingExperimentIds</td><td>experiment_ids</td></tr>
<tr><td>contributingProposalIds</td><td>proposal_ids</td></tr>
<tr><td>createDate</td><td>creation_date</td></tr>
<tr><td>datasetId</td><td>dataset_id</td></tr>
<tr><td>datasetSize</td><td>dataset_size</td></tr>
<tr><td>embargoEndDate</td><td>embargo_end_date</td></tr>
<tr><td>endTime</td><td>end_time</td></tr>
<tr><td>experimentDescription</td><td>experiment_description</td></tr>
<tr><td>exposureTime</td><td>exposure_time</td></tr>
<tr><td>filterWavelengths</td><td>filter_wavelengths</td></tr>
<tr><td>frameCount</td><td>number_of_frames</td></tr>
<tr><td>hasAllStokes</td><td>full_stokes</td></tr>
<tr><td>instrumentName</td><td>instrument</td></tr>
<tr><td>isDownloadable</td><td>downloadable</td></tr>
<tr><td>isEmbargoed</td><td>embargoed</td></tr>
<tr><td>observables</td><td>observables</td></tr>
<tr><td>originalFrameCount</td><td>level_0_frame_count</td></tr>
<tr><td>primaryExperimentId</td><td>primary_experiment_id</td></tr>
<tr><td>primaryProposalId</td><td>primary_proposal_id</td></tr>
<tr><td>qualityAverageFriedParameter</td><td>average_fried_parameter</td></tr>
<tr><td>qualityAveragePolarimetricAccuracy</td><td>average_polarimetric_accuracy</td></tr>
<tr><td>recipeId</td><td>recipe_id</td></tr>
<tr><td>recipeInstanceId</td><td>recipe_instance_id</td></tr>
<tr><td>recipeRunId</td><td>recipe_run_id</td></tr>
<tr><td>startTime</td><td>start_time</td></tr>
<tr><td>stokesParameters</td><td>stokes_parameters</td></tr>
<tr><td>targetTypes</td><td>target_types</td></tr>
<tr><td>updateDate</td><td>last_updated</td></tr>
<tr><td>wavelengthMax</td><td>wavelength_max</td></tr>
<tr><td>wavelengthMin</td><td>wavelength_min</td></tr>
<tr><td>hasSpectralAxis</td><td>has_spectral_axis</td></tr>
<tr><td>hasTemporalAxis</td><td>has_temporal_axis</td></tr>
<tr><td>averageDatasetSpectralSampling</td><td>average_spectral_sampling</td></tr>
<tr><td>averageDatasetSpatialSampling</td><td>average_spatial_sampling</td></tr>
<tr><td>averageDatasetTemporalSampling</td><td>average_temporal_sampling</td></tr>
<tr><td>qualityReportObjectKey</td><td>quality_report_filename</td></tr>
</table>"""

    test_keymap = {
        "asdfObjectKey": "asdf Filename",
        "boundingBox": "Bounding Box",
        "browseMovieObjectKey": "Movie Filename",
        "browseMovieUrl": "Preview URL",
        "bucket": "Storage Bucket",
        "contributingExperimentIds": "Experiment IDs",
        "contributingProposalIds": "Proposal IDs",
        "createDate": "Creation Date",
        "datasetId": "Dataset ID",
        "datasetSize": "Dataset Size",
        "embargoEndDate": "Embargo End Date",
        "endTime": "End Time",
        "experimentDescription": "Experiment Description",
        "exposureTime": "Exposure Time",
        "filterWavelengths": "Filter Wavelengths",
        "frameCount": "Number of Frames",
        "hasAllStokes": "Full Stokes",
        "instrumentName": "Instrument",
        "isDownloadable": "Downloadable",
        "isEmbargoed": "Embargoed",
        "observables": "Observables",
        "originalFrameCount": "Level 0 Frame count",
        "primaryExperimentId": "Primary Experiment ID",
        "primaryProposalId": "Primary Proposal ID",
        "qualityAverageFriedParameter": "Average Fried Parameter",
        "qualityAveragePolarimetricAccuracy": "Average Polarimetric Accuracy",
        "recipeId": "Recipe ID",
        "recipeInstanceId": "Recipe Instance ID",
        "recipeRunId": "Recipe Run ID",
        "startTime": "Start Time",
        "stokesParameters": "Stokes Parameters",
        "targetTypes": "Target Types",
        "updateDate": "Last Updated",
        "wavelengthMax": "Wavelength Max",
        "wavelengthMin": "Wavelength Min",
        "hasSpectralAxis": "Has Spectral Axis",
        "hasTemporalAxis": "Has Temporal Axis",
        "averageDatasetSpectralSampling": "Average Spectral Sampling",
        "averageDatasetSpatialSampling": "Average Spatial Sampling",
        "averageDatasetTemporalSampling": "Average Temporal Sampling",
        "qualityReportObjectKey": "Quality Report Filename",
    }
    table = _path_format_table(test_keymap)
    table = table[table.find("\n")+1:]

    assert table == output


def test_cycle_single_row():
    tt = DKISTQueryResponseTable.read(rootdir / "AGLKO-inv.ecsv")
    path_format_inventory(dict(tt[0]))
