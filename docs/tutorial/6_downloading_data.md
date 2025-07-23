---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

(dkist:tutorial:downloading-data)=
# Downloading Data

## Setting up and using Globus

We've seen how to search and download the ASDF metadata files with Fido.
However, the actual data files are distributed using [Globus](https://www.globus.org/data-transfer).
For this chapter you will need to be running Globus Connect Personal, so follow the installation instructions for your platform [here](https://www.globus.org/globus-connect-personal) if you haven't already.
During the setup, you will need to login to Globus.
For this you can use your login for your institution, or alternatively you can login with Google or ORCID.

Once Globus is installed and set up, you will need to run Globus Connect Personal (GCP) as described on the installation page.
You will need to do this every time you want to download data, either through the user tools or through the Globus web app.
When you start GCP You may also want to define the location or locations on your computer which you want Globus to have access to.
On Windows and Mac OS this option is in the "Access" tab of the configuration options.
On Linux you can do this using the `-restrict-paths` command line argument, or by editing the config file.
Globus will only be able to transfer files onto your machine in the specified paths.
Remember that you do need to have GCP running for any transfers to complete - so if you stop it then your data download will stop as well.

When starting transfers with the ``dkist`` package, you may be asked to login to Globus (or authorize the device).
This will pop open a web browser window where you can complete this flow.

Finally, a couple of things to note on terminology:

- **Endpoints** (also called **Collections** in the web app) are locations registered with Globus for data transfer.
Many institutions will have their own Globus endpoints, such as a computing cluster, that you may have access to.
DKIST has an endpoint called "DKIST Data Transfer", which is where DKIST data will be made available.
The user tools use this as the default remote endpoint, and define a local endpoint on your current machine.

- **Paths** Paths in Globus are broadly what you expect them to be.
However, note that the paths are as the Globus endpoint sees them, so might not be identical to how you refer to them on your local system.

## Dataset and downloading

```{note}
For this section we don't recommend that you run all the download commands as you work through this notebook unless you're willing to wait for them to complete, which may take some time.
```

First let's load the VISP dataset we were using before.
This time we'll download the ASDF using Fido rather than loading the sample data.
This is so that we can continue using a dataset we're familiar with but also go through the full process of downloading both the ASDF and data files.

```{code-cell} ipython3
:tags: [keep-inputs]

import dkist
import dkist.net
from sunpy.net import Fido, attrs as a

res = Fido.search(a.dkist.Dataset("BKPLX"))
f = Fido.fetch(res, path="~/sunpy/data/{instrument}/{dataset_id}/")
ds = dkist.load_dataset(f)
```

As we saw earlier, we can use the `files` attribute to access information about the number and names of files in the dataset even before downloading any.

```{code-cell} ipython3
print(ds.files)
print(ds.files.filenames)
```

The `files` attribute has a `download()` method that we will use for downloading the data.
In order to speed up this demonstration a bit, we will just download the first file.
To do this we can slice the dataset so that we're only accessing the portion of the data saved in the first file, paying attention to the chunking information in the `Dataset`:

```{code-cell} ipython3
ds
```

```{code-cell} ipython3
ds[0, 0].files
```

```{code-cell} ipython3
:tags: [skip-execution]

ds[0, 0].files.download()
```

```{code-cell} ipython3
ds[0, 0].plot()
```

The default download directory used by `download()` is in the same folder as the ASDF file we loaded, so in this case `~/sunpy/data/VISP/BKPLX`.
Since the `download()` method set up the transfer through globus, you can check on the status of your download in the activity tab of the web app as we saw earlier.

We can change the download location of the files using the `path` argument.
But remember that whatever path you specify must be accessible by Globus Connect Personal.

```{code-cell} ipython3
:tags: [skip-execution]

ds[0].files.download(path="~/somewhere/globus/can't/reach/")  # will hang for a while and then fail
```

The `path` keyword will replace placeholders in the path in the same way as we saw with `Fido.fetch()`.
Any key in the dataset inventory (`ds.meta['inventory']`) can be used for this.
So for example:

```{code-cell} ipython3
:tags: [skip-execution]

ds[0, 0].files.download(path="~/sunpy/data/{dataset_id}")
```

would save the file to `~/sunpy/data/BKPLX/VISP_2023_10_16T18_21_47_508_00630200_I_BKPLX_L1.fits`.
Downloading the files to a custom directory also sets the ``ds.files.basepath`` property so that the new files are loaded:

```{code-cell} ipython3
ds.files.basepath
```

If we know that we will want to download an entire dataset, this can be done in the same way but using the full dataset object.

```{code-cell} ipython3
:tags: [skip-execution]

ds.files.download()
```

Alternatively, the user tools offer another function which can also be used to download a full dataset.
The `transfer_complete_datasets()` function can take a Fido search results object and download an entire dataset:

```{code-cell} ipython3
:tags: [skip-execution]

results = Fido.search(a.Instrument("VISP"), a.Time("2023-10-16 18:00", "2023-10-16 19:00"))
dkist.net.transfer_complete_datasets(results["dkist"][0])
```

Notice that we have to specify `results["dkist"]` here, because `transfer_complete_datasets` only works for DKIST datasets, not any other kind of result that Fido might return.

We can also download many datasets at once.
For example if we have a proposal ID that we want to download all the data for we could run:

```{code-cell} ipython3
:tags: [skip-execution]

results = Fido.search(a.dkist.Proposal("pid_1_123"))
dkist.net.transfer_complete_datasets(results)
```

This will iterate over the results and download each dataset in turn, with a progress bar for each.

Of course, if this is a dataset you already know you will want to download all of - for example if it's your own observation - then you may not need to find it through Fido first.
Fortunately, `transfer_complete_datasets()`, also lets you specify which datasets to download, by passing one or more dataset IDs.

```{code-cell} ipython3
:tags: [skip-execution]

dkist.net.transfer_complete_datasets('BKPLX')
```

Both `transfer_complete_datasets()` and `ds.files.download()` also allow you to specify remote endpoints using the `destination_endpoint` keyword.

Normally both of these functions will block the terminal while the download is active.
If you want to download a lot of data this is probably not useful, so you can turn this functionality off by passing `wait=False`.
This will set up the transfer in Globus but then return from the function.
Of course, be cautious with this approach if the next step of your code depends on the data being present.
Setting `wait=False` will also skip the wait at the end of each dataset if downloading more than one, so all the transfers will be set up on Globus and then the function will return.
For example:

```{code-cell} ipython3
:tags: [skip-execution]

results = Fido.search(a.dkist.Proposal("pid_1_123"))
dkist.net.transfer_complete_datasets(results, wait=False, progress=False)
```
