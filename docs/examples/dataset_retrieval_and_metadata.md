---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.2
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

(dkist:examples:dataset-retrieval-and-metadata)=
# Retrieving a Dataset and Inspecting Metadata

In this example we will search for a DKIST dataset by dataset ID, download its metadata ASDF file, and inspect some of the metadata stored in it.

```{code-cell} ipython3
from sunpy.net import Fido, attrs as a

import dkist
import dkist.net
```

Here we use the VISP dataset [ALQRZ](https://dkist.data.nso.edu/datasetview/ALQRZ).
To inspect a different dataset, edit only `DATASET_ID`.

```{code-cell} ipython3
DATASET_ID = "ALQRZ"
```

First we search for the dataset.
The `Status("any")` attribute means the search will return this dataset ID irrespective of its processing status.

```{code-cell} ipython3
search_results = Fido.search(a.dkist.Dataset(DATASET_ID), a.dkist.Status("any"))
search_results
```

The search result points to the metadata ASDF file.
We can fetch that file directly with `Fido.fetch`.

```{code-cell} ipython3
asdf_file = Fido.fetch(search_results)
asdf_file
```

Now we can load the ASDF file as a `dkist.Dataset`.
This describes the dataset and its file references without downloading all of the FITS files.

```{code-cell} ipython3
dataset = dkist.load_dataset(asdf_file)
dataset
```

The dataset inventory contains searchable metadata from the DKIST Data Center.
Here we display the entries related to data quality.

```{code-cell} ipython3
{
    key: value
    for key, value in dataset.meta["inventory"].items()
    if key.lower().startswith("quality")
}
```

Each calibrated dataset also has a quality report.
This method downloads the report PDF and returns a `parfive.Results` object with the local filename.

```{code-cell} ipython3
quality_report = dataset.files.quality_report()
quality_report
```

The ASDF file can also contain more detailed metadata about how the dataset was generated.
The following fields describe the input parameters, the observe and calibration frames, and the recipe configuration.

```{code-cell} ipython3
dataset.meta["parameters"]
```

```{code-cell} ipython3
dataset.meta["observation_input_frames"]
```

```{code-cell} ipython3
dataset.meta["calibration_input_frames"]
```

```{code-cell} ipython3
dataset.meta["recipe_run_config"]
```
