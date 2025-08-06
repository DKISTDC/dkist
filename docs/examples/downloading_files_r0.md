---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.5
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---
# Downloading Data Based on Seeing

```{code-cell} python
import matplotlib.pyplot as plt
from sunpy.net import Fido, attrs as a

import dkist
import dkist.net
```

Let's find a dataset with the highest average value of r0 (this is bad?).
First we'll search for all unembargoed VISP data.

```{code-cell} python
res = Fido.search(a.Instrument("VISP"), a.dkist.Embargoed(False))
```

Next, since we want to use the highest average $r_0$, we can have Fido sort the results and output just the useful columns.

```{code-cell} python
res['dkist'].sort("Average Fried Parameter", reverse=True)
res['dkist'].show("Dataset ID", "Start Time", "Average Fried Parameter", "Primary Proposal ID")
```

We'll ignore the datasets with anomalously high values and look at the next one with a value that is high but realistic.
This gives us the dataset `AXVXL`.
We can download the dataset ASDF with Fido to inspect it in more detail.
Remember that this only downloads a single ASDF file with some more metadata about the dataset, not the actual science data.

```{code-cell} python
:tags: [remove-stderr]
asdf_files = Fido.fetch(res['dkist'][3], path="~/sunpy/data/{dataset_id}/")
ds = dkist.load_dataset(asdf_files[0])
```

Now that we have access to the FITS headers we can inspect the $r_0$ more closely, just as we did in the previous notebook.
Remember that `DINDEX4` is the Stokes index, so we can plot the $r_0$ for just Stokes I like so:
```{code-cell} python
plt.plot(ds.headers[ds.headers["DINDEX4"] == 1]["ATMOS_R0"])
```

Now let's slice down our dataset based on the first frame where $r_0$ is high:

```{code-cell} python
# Select headers for only frames with bad r0
bad_headers = ds.headers[ds.headers["ATMOS_R0"] > 1]

# Make sure headers are sorted by date
bad_headers.sort("DATE-AVG")

# Slice up to the index of the first bad frame
sds = ds[0, :bad_headers[0]["DINDEX3"]-1, :, :]
```

We can now download only these files, remember you need globus-connect-personal running for this.
```{code-cell} python
---
tags: [skip-execution]
---
sds.files.download(path="~/sunpy/data/{dataset_id}/")
```

Now let's plot the Stokes I data at some wavelength:

```{code-cell} python
---
tags: [skip-execution]
---
ds[0, :, 466, :].plot(plot_axes=['x', 'y'], aspect="auto")
```

You will notice that a lot of it is missing.
This is because we have deliberately only downloaded those frames with an acceptably low $r_0$.
You may also notice though, that the `Dataset` object continues to function normally without the rest of the data.
When we try to access the data, if the file is missing then `Dataset` fills in the corresponding portions of the array with NaNs.

Since the seeing is bad for a significant contiguous portion of the data, we may simply want to discount that part and look only at the useful data.
In this case we can use the sub-dataset we made earlier:

```{code-cell} python
---
tags: [skip-execution]
---
sds[:, 466, :].plot(plot_axes=['x', 'y'], aspect="auto")
```
Or of course we can make any arbitrary slice to look at whatever subset of the data we prefer.
