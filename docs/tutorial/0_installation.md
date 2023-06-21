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

This tutorial will take you through the basics of using the DKIST Python Tools.
To be able to follow along with the examples you will first need to install some software:

## Globus

To download DKIST data you need [Globus Connect Personal (GCP)](https://www.globus.org/globus-connect-personal), and a Globus account.

You will need to install GCP and have it running before you can download any data from DKIST.
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

If you know what you are doing and have Python installed without conda, make a clean virtual environment and run:

```{code-block} bash
pip install dkist jupyter
```
