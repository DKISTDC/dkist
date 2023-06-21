---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.5
---

# Installation and Setup

This workshop is a code-along style workshop.
For this to work we will need some software installed on your laptops:


## Globus

To download DKIST data you need [Globus Connect Personal (GCP)](https://www.globus.org/globus-connect-personal), and a Globus account.

Please install GCP and have it ready to use during the workshop.
The [DKIST Help Desk](https://nso.atlassian.net/servicedesk/customer/portal/3/article/247694160) has some pages to help with this.

## Python

If you don't already have a Python installation then we recommend installing Python with [miniforge](https://github.com/conda-forge/miniforge/#miniforge).
If you already have Python and either `conda` or `pip` working you can skip the next section.

### Installing miniforge

First, download the installer for your system and architecture from the links below:
::::{grid} 3
:::{grid-item-card}  Linux

[x86-64](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh)

[aarch64](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh)

[ppc64le](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-ppc64le.sh)

:::
:::{grid-item-card}  Windows
:link: https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe
[x86-64](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe)
:::
:::{grid-item-card}  Mac

[x86-64](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh)

[arm64 (Apple Silicon)](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh)
:::
::::

Then select your platform to install miniforge:

::::{tab-set}

:::{tab-item} Linux & Mac
Run the script downloaded above, with `bash <filename>`.
The following should work:

```{code-block} console
bash Miniforge3-$(uname)-$(uname -m).sh
```

Once the installer has completed, close and reopen your terminal.
:::

:::{tab-item} Windows
Double click the executable file downloaded from the links above.

Once the installer has completed you should have a new "miniforge Prompt" entry in your start menu.
:::

::::

In a new terminal (miniforge Prompt on Windows) run `conda list` to test that the install has worked.

### Installing `dkist` with conda

Follow this section if you have just installed miniforge, or if you have conda installed from miniconda or anaconda.

Open a new terminal (miniforge Prompt or anaconda prompt on Windows) and run:

```{code-block} bash
conda create -n dkist-workshop
conda activate dkist-workshop
```

to create a new environment for this workshop.
Then run:

```{code-block} bash
conda install -c conda-forge dkist jupyter
```

### Installing `dkist` with pip

If you know what you are doing and have Python installed without conda, please make a clean virtual environment and run:

```{code-block} bash
pip install dkist jupyter
```

## Getting the Workshop Materials

The next step is to get the [Jupyter Notebooks](https://jupyter-notebook.readthedocs.io/en/latest/) we will be using for the workshop.
We have published these notebooks in the [DKISTDC/NSO-Python-Workshop](https://github.com/DKISTDC/NSO-Python-Workshop) GitHub repository.
To get them you need to have [git](https://git-scm.com/) installed.

::::{tab-set}

:::{tab-item} Install git and download
If you don't have git already, then you can install it with conda.
First make sure you are in the correct conda environment:

```{code-block} console
conda activate dkist-workshop
```

then install git:
```{code-block} console
conda install git
```

Next, ensure you are in the parent directory to where you want to download the notebooks, for example:

```{code-block} console
cd ~
```

then download the git repository:

```{code-block} console
git clone https://github.com/DKISTDC/NSO-Python-Workshop.git
```

This should have made a directory called `NSO-Python-Workshop`

:::

:::{tab-item} I already have git

Ensure you are in the correct directory and run:

```{code-block} console
git clone https://github.com/DKISTDC/NSO-Python-Workshop.git
```
:::

:::{tab-item} I give up, git hates me
You can download a zip file [here](https://github.com/DKISTDC/NSO-Python-Workshop/archive/refs/heads/main.zip) but you won't be able to fetch any updates or the final versions of the notebooks.
:::
::::

## Running Juypter Notebook

The last step to get you up and running is to start the Jupyter Notebook server.

Firstly, make sure you are in the `NSO-Python-Workshop` directory, for example:

```{code-block} console
cd ~/NSO-Python-Workshop
```

then run:

```{code-block} console
jupyter notebook
```

This should pop open a web page in your browser which will give you an interactive Python session, which looks something like this:

![](./notebook.png)

click on the `index.ipynb` file to load it and get started.
