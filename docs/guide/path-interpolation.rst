.. _interpolation-keys:

Path interpolation keys
=======================

When downloading DKIST data with ``ds.files.download()``, the ``path=`` keyword argument can be used to specify the target folder for the download.
This path can include keys corresponding to metadata entries, and those values are then used to complete the download path.
For example, to download a dataset into its own folder named with the dataset ID, with separate subfolders for each instrument in the dataset, you could set ``path="~/data/dkist/{Dataset ID}/{Instrument}/"``.
This would take the values for the ``datasetID`` and ``instrumentName`` metadata keywords in the dataset and insert them into the path string.

Here is a full list of the metadata keywords available for this purpose and their corresponding path interpolation keys:

====================================== ==================================
Metadata keyword                       Path key
====================================== ==================================
``asdfObjectKey``                       ``asdf Filename``
``boundingBox``		                      ``Bounding Box``
``browseMovieObjectKey``		            ``Movie Filename``
``browseMovieUrl``		                  ``Preview URL``
``bucket``		                          ``Storage Bucket``
``contributingExperimentIds``           ``Experiment IDs``
``contributingProposalIds``		          ``Proposal IDs``
``createDate``		                      ``Creation Date``
``datasetId``               		        ``Dataset ID``
``datasetSize``		                      ``Dataset Size``
``embargoEndDate``		                  ``Embargo End Date``
``endTime``		                          ``End Time``
``experimentDescription``		            ``Experiment Description``
``exposureTime``		                    ``Exposure Time``
``filterWavelengths``		                ``Filter Wavelengths``
``frameCount``		                      ``Number of Frames``
``hasAllStokes``		                    ``Full Stokes``
``instrumentName``		                  ``Instrument``
``isDownloadable``		                  ``Downloadable``
``isEmbargoed``		                      ``Embargoed``
``observables``		                      ``Observables``
``originalFrameCount``		              ``Level 0 Frame count``
``primaryExperimentId``		              ``Primary Experiment ID``
``primaryProposalId``		                ``Primary Proposal ID``
``qualityAverageFriedParameter``        ``Average Fried Parameter``
``qualityAveragePolarimetricAccuracy``  ``Average Polarimetric Accuracy``
``recipeId``		                        ``Recipe ID``
``recipeInstanceId``                    ``Recipe Instance ID``
``recipeRunId``                         ``Recipe Run ID``
``startTime``                           ``Start Time``
``stokesParameters``                    ``Stokes Parameters``
``targetTypes``                         ``Target Types``
``updateDate``                          ``Last Updated``
``wavelengthMax``                       ``Wavelength Max``
``wavelengthMin``                       ``Wavelength Min``
``hasSpectralAxis``                     ``Has Spectral Axis``
``hasTemporalAxis``                     ``Has Temporal Axis``
``averageDatasetSpectralSampling``      ``Average Spectral Sampling``
``averageDatasetSpatialSampling``       ``Average Spatial Sampling``
``averageDatasetTemporalSampling``      ``Average Temporal Sampling``
``qualityReportObjectKey``              ``Quality Report Filename``
