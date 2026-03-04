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
# Using headers to select data for download

```{code-cell} python
---
:tags: [keep-inputs]
---
import matplotlib.pyplot as plt
from sunpy.net import Fido, attrs as a
import astropy.units as u

import dkist
import dkist.net
```

Let's find a dataset with the a high average value of $r_0$.
Obviously this is not what we would normally want but this will allow us to find and disregard the portions of the dataset where the seeing is bad and keep the portions where it is good.
First we'll search for all unembargoed VISP data.

```{code-cell} python
res = Fido.search(a.Instrument("VISP"), a.dkist.Embargoed(False))
```

Next, since we want to use a high average $r_0$, we can have Fido search for only results in a useful range.
We'll ignore datasets with anomalously high values and look at ones with a value that is high but realistic.

```{code-cell} python
res = Fido.search(a.Instrument("VISP"), a.dkist.Embargoed(False), a.dkist.FriedParameter(1*u.cm, 2*u.cm))
```

Then we'll sort them and inspect just the columns we're interested in, the product ID and the average $r_0$.

```{code-cell} ipython3
res["dkist"].sort("Average Fried Parameter", reverse=True)
res["dkist"].show("Product ID", "Average Fried Parameter")
```

Let's use the product `L1-DSLDE`.
We can download the ASDF for that product's latest dataset with Fido to inspect it in more detail.
Remember that this only downloads a single ASDF file with some more metadata about the dataset, not the actual science data.

```{code-cell} python
---
:tags: [remove-stderr]
---
asdf_file = Fido.fetch(res["dkist"][res["dkist"]["Product ID"] == "L1-DSLDE"], path="~/sunpy/data/{dataset_id}/")
ds = dkist.load_dataset(asdf_file)
```

Now that we have access to the FITS headers we can inspect the $r_0$ more closely, just as we did in the previous notebook.
We will only look at the values for Stokes I, and we can overplot the Out-Of-Bounds Shift value from the headers to see where the $r_0$ value is most reliable.

```{code-cell} python
fig, ax = plt.subplots()

r0line, = plt.plot(ds[0].headers["ATMOS_R0"], label="$r_0$")
ax.set_ylabel("$r_0$ ($m$)")
ax.set_ylim(0, 0.2)

ax2 = plt.twinx()
oobline, = ax2.plot(ds[0].headers["OOBSHIFT"], color="C1", label="OOB Shift")
ax2.set_ylabel("# subapertures out of bounds")
plt.legend(handles=[r0line, oobline])
```

Now let's slice down our dataset based on the first frame where $r_0$ is too high:

```{code-cell} python
# Select headers for only frames with bad r0
bad_headers = ds.headers[ds.headers["ATMOS_R0"] > 1]

# Make sure headers are sorted by date
bad_headers.sort("DATE-AVG")

# Look at the indices where r0 is bad so we can slice out a good section
bad_headers['DINDEX3']-1
```

```{code-cell} ipython3
# Slice out the largest section of good frames
sds = ds[0, 12:36, :, :]
```

We can now download only these files, remember you need globus-connect-personal running for this.
(Note that these plots will show if you work through the tutorial notebooks but not on the main Python tools documentation, as the data will not be available.)

```{code-cell} python
---
tags: [skip-execution]
---
sds.files.download(path="~/sunpy/data/{dataset_id}/")
```

Now let's plot the Stokes I data at the first wavelength:

```{code-cell} python
---
tags: [skip-execution]
---
ds[0, :, 0, :].plot(plot_axes=['x', 'y'], aspect="auto")
```

You will notice that a lot of it is missing.
This is because we have deliberately only downloaded those frames with an acceptably low $r_0$.
You may also notice though, that the `Dataset` object continues to function normally without the rest of the data.
When we try to access the data, if the file is missing then `Dataset` fills in the corresponding portions of the array with NaNs.

Since the seeing is bad for significant contiguous portions of the data, we may simply want to discount that part and look only at the useful data.
In this case we can use the sub-dataset we made earlier:

```{code-cell} python
---
tags: [skip-execution]
---
sds[:, 0, :].plot(plot_axes=['x', 'y'], aspect="auto")
```
Or of course we can make any arbitrary slice to look at whatever subset of the data we prefer.
