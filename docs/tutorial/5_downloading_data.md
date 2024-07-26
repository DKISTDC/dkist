---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

(dkist:tutorial:downloading-data)=
# Downloading Data

## Setting up and using Globus

We've seen how to search and download the ASDF metadata files with Fido.
However, the actual data files are distributed using [Globus](https://www.globus.org/data-transfer)
For the next portion of the workshop you will need to be running Globus Connect Personal, so follow the installation instructions for your platform [here](https://www.globus.org/globus-connect-personal) if you haven't already.
During the setup, you will need to login to Globus.
For this you can use your login for your institution, or alternatively you can login with Google or ORCID.

Once Globus is installed and set up, you will need to run Globus Connect Personal (GCP) as described on the installation page.
You will need to do this every time you want to download data, either through the user tools or through the Globus web app.
When you start GCP You may also want to define the location or locations on your computer which you want Globus to have access to.
On Linux you can do this using the `-restrict-paths` command line argument, or by editing the config file.
On Windows and Mac OS this option is in the "Access" tab of the configuration options.
Globus will only be able to transfer files onto your machine in the specified paths.

## Dataset and downloading

Now that we have Globus setup, let's see how to download data using it from Python.
For this section we don't recommend that you run the download commands as we go through the tutorial unless you're willing to wait for them to complete, which may take some time.
First let's load up another `Dataset`.

```{code-cell} ipython
import dkist
import dkist.net
from sunpy.net import Fido, attrs as a

res = Fido.search(a.dkist.Dataset('BKPLX'))
files = Fido.fetch(res, path="~/dkist_data/{instrument}_{dataset_id}")
ds = dkist.load_dataset(files)
```

As we saw earlier, we can use the `files` attribute to access information about the number and names of files in the dataset even before downloading any.

```{code-cell} ipython
print(ds.files)
print(ds.files.filenames)
```

The `files` attribute has a `download()` method that we will use for downloading the data.
In order to speed up this demonstration a bit, we will just download the first file.
To do this we can slice the dataset so that we're only accessing the portion of the data saved in the first file, paying attention to the chunking information in the `Dataset`:

```{code-cell} ipython
ds
```

```{code-cell} ipython3
:tags: [skip-execution]

ds[0, 0].files.download()
```

Since the `download()` method set up the transfer through globus, you can also check on the status of your transfer in the web app at [app.globus.org](https://app.globus.org).

We can change the download location of the files using the `path` argument.
But remember that whatever path you specify must be accessible by Globus Connect Personal.

```{code-cell} ipython3
:tags: [skip-execution]

ds[0, 0].files.download(path="~/not/really/a/path/")  # will hang for a while and then fail
```

The `path` keyword will replace placeholders in the path in the same way as we saw with `Fido.fetch()`.
So for example:

```{code-cell} ipython3
:tags: [skip-execution]

ds[0, 0].files.download(path="~/dkist_data/{instrument}_{dataset_id}")
```

would save the file to `~/dkist_data/BKPLX/VISP_2023_10_16T18_21_47_508_00630200_I_BKPLX_L1.fits`.

If we know that we will want to download an entire dataset, this can be done in the same way but using the full dataset object.

```{code-cell} ipython3
:tags: [skip-execution]

ds.files.download()
```

Alternatively, the user tools offer another function which can also be used to download a full dataset.
The `transfer_complete_datasets()` function can take a Fido search results object and download a full dataset:

```{code-cell} ipython3
:tags: [skip-execution]

results = Fido.search(a.Instrument("VBI"), a.Time("2022-06-03 17:00", "2022-06-03 18:00"))
dkist.net.transfer_complete_datasets(results["dkist"][0])
```

Notice that we have to specify `results["dkist"]` here, because `transfer_complete_datasets` only works for DKIST datasets, not any other kind of result that Fido might return.

We can also download many datasets at once:

```{code-cell} ipython3
:tags: [skip-execution]

dkist.net.transfer_complete_datasets(results["dkist"])
```

This will iterate over the results and download each dataset in turn, with a progress bar for each.

Of course, if this is a dataset you already know you will want to download all of - for example if it's your own observation - then you may not need to find it through Fido first.
Fortunately, `transfer_complete_datasets()`, also lets you specify a dataset or datasets for which to download all files, by passing the dataset IDs.

```{code-cell} ipython3
:tags: [skip-execution]

dkist.net.transfer_complete_datasets('BLKGA')
```

Both `transfer_complete_datasets()` and `ds.files.download()` also allow you to specify remote endpoints using the `destination_endpoint` keyword.

Normally both of these functions will block the terminal while the download is active.
If you want to download a lot of data this is probably not useful, so you can turn this functionality off by passing `wait=False`.
This will set up the transfer in Globus but then return from the function.
Of course, be cautious with this approach if the next step of your code depends on the data being present.
Setting `wait=False` will also skip the wait at the end of each dataset if downloading more than one, so all the transfers will be set up on Globus and then the function will return.

Finally, let's grab some data for the next tutorial, which will be on visualisation.
We are going to grab the whole Stokes I part of the VISP dataset we loaded in earlier.

```{code-cell} ipython3
:tags: [skip-execution]

ds[0].files.download(wait=False, progress=False)
```
