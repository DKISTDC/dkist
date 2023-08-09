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
# Astropy and SunPy - A Quick Primer

Before we progress to searching for DKIST data we need to cover some functionality of the [SunPy](https://sunpy.org) and [Astropy](https://astropy.org) packages.
These two packages, amongst a few others, are the core components of the DKIST tools.
In this session we shall only quickly cover the functionality of SunPy and Astropy we need for the rest of the workshop.
There are many other parts of these packages which are useful when working with DKIST data, which you should explore.
As we covered in the introduction, Python is a modular language; Astropy provides fundamental functionality for a lot of different types of astronomy.
In this section we shall cover the following parts of Astropy:

* Units
* World Coordinate Systems
* Coordinates

## Units

Astropy provides a subpackage {obj}`astropy.units` which provides tools for associating physical units with numbers and arrays.
This lets you do mathematical operations on these arrays while propagating the units.

To get started we import `astropy.units` because we are going to be using this a lot, we import it as `u`.
```{code-cell} python
import astropy.units as u
```

Now we can access various units as such:
```{code-cell} python
u.m
```

```{code-cell} python
u.kg
```

We can now attach a unit to a number:
```{code-cell} python
length = 10 * u.m
length
```

We can also compose multiple quantities (a number with a unit):

```{code-cell} python

speed = length / (30 * u.min)
speed
```

Using the `.to()` method on a `u.Quantity` object lets you convert a quantity to a different unit.

```{code-cell} python
speed.to(u.km/u.h)
```

### Equivalencies

Some conversions are not done by a conversion factor as between miles and kilometers – for example converting between wavelength and frequency:

```{code-cell} python
---
tags: [raises-exception]
---
(656.281 * u.nm).to(u.Hz)  # Fails because they are not compatible
```

However we can make use of a spectral *equivalency* to indicate the link between the units:

```{code-cell} python
(656.281 * u.nm).to(u.Hz, equivalencies=u.spectral())
```

### Constants

The `astropy.constants` sub-package provides a set of physical constants which are compatible with the units/quantities framework:

```{code-cell} python
from astropy.constants import M_sun, c
```
```{code-cell} python
E = 3 * M_sun * c ** 2
E.to(u.J)
```

## Coordinates

The Astropy coordinates submodule {obj}`astropy.coordinates` provides classes to represent physical coordinates with all their associated metadata, and transform them between different coordinate systems.
Currently, {obj}`astropy.coordinates` supports:

* Spatial coordinates via {obj}`astropy.coordinates.SkyCoord`
* Spectral coordinates via {obj}`astropy.coordinates.SpectralCoord`
* Stokes profiles via {obj}`astropy.coordinates.StokesCoord` (coming soon)

### Spatial Coordinates

SunPy provides extensions to the Astropy coordinate system to represent common solar physics frames.
So to use the sunpy coordinates we have to first import {obj}`sunpy.coordinates` which registers them with astropy.

```{code-cell} python
import sunpy.coordinates
from astropy.coordinates import SkyCoord
```

We can now create a `SkyCoord` object representing a point on the Sun:

```{code-cell} python
SkyCoord(10*u.arcsec, 20*u.arcsec, frame="helioprojective")
```

This is the most minimal version of this coordinate frame, however, it isn't very useful as we haven't provided enough information to be able to transform it to other frames.
This is because helioprojective is an observer centred coordinate frame, so we need to know where in inertial space the observer is.
One way of doing this is to say the observer is on Earth at a specific time:

```{code-cell} python
hpc1 = SkyCoord(10*u.arcsec, 20*u.arcsec, frame="helioprojective",
                obstime="2023-05-21T04:00:00", observer="earth")
hpc1
```

This coordinate can now be converted to other frames, such as heliographic coordinates:

```{code-cell} python
hpc1.transform_to("heliographic_stonyhurst")
```

There are few things to notice about the difference between these two `SkyCoord` objects:

1. The default representation of the latitude and longitude is now in degrees as is conventional.
1. The heliographic frame is three dimensional (it has a radius), when the input frame was not. This is because the distance from the observer was calculated using the `rsun` attribute.
1. The `obstime` and `rsun` attributes are still present, but the `observer` attribute isn't. This is because heliographic coordinates are not observer dependent.
1. The `obstime` attribute is still important to transform to other frames, as the heliographic frame needs to know the location of Earth.

### Spectral Coordinates

{obj}`astropy.coordinates.SpectralCoord` is a `Quantity` like object which also holds information about the observer and target coordinates and relative velocities.

```{note}
Use of `SpectralCoord` with solar data is still experimental so not all features may work, or be accurate.
```

```{code-cell} python
from astropy.coordinates import SpectralCoord
from sunpy.coordinates import get_earth
```

`SpectralCoord` does not automatically make the HPC coordinate 3D, but wants the distance, so we do it explicitally:

```{code-cell} python
hpc2 = hpc1.make_3d()
```

Now we can construct our spectral coordinate with both a target and an observer
```{code-cell} python
spc = SpectralCoord(586.3 * u.nm, target=hpc2, observer=get_earth(time=hpc2.obstime))
spc
```

We can show the full details of the spectral coord (working around a bug in astropy):
```{code-cell} python
print(repr(spc))
```

## World Coordinate System

One of the other core components of the ecosystem provided by Astropy is the {obj}`astropy.wcs` package which provides tools for mapping pixel to world coordinates and world to pixel.
When loading a FITS file with complete (and standard compliant) WCS metadata we can create an `astropy.wcs.WCS` object.
For the this example we will use some sunpy sample data from AIA.

```{code-cell} python
import sunpy.coordinates
```

To read this FITS file we will use {obj}`astropy.io.fits` (you can also use `sunpy` for this).

```{code-cell} python
from astropy.io import fits

hdu_list = fits.open("../data/VISP_2022_10_24T19_47_33_218_00630205_I_BEOGN_L1.fits")
```

We can now access the header of the second HDU:
```{code-cell} python
hdu_list[1].header
```

Using this header we can create a `astropy.wcs.WCS` object:
```{code-cell} python
from astropy.wcs import WCS

wcs = WCS(hdu_list[1].header)
wcs
```

This WCS object allows us to convert between pixel and world coordinates, for example:

```{code-cell} python
wcs.pixel_to_world(1024, 400, 1)
```

This call returns a {obj}`astropy.coordinates.SkyCoord` object (which needs sunpy to be imported), we will come onto this more later.

We can also convert between pixel and plain numbers:

```{code-cell} python
wcs.pixel_to_world_values(1024, 400, 1)
```

The units for these values are given by:

```{code-cell} python
wcs.world_axis_units
```


The WCS also has information about what the world axes represent:

```{code-cell} python
wcs.world_axis_physical_types
```

We can also inspect the correlation between the world axes and pixel axes:

```{code-cell} python
wcs.axis_correlation_matrix
```

This correlation matrix has the world dimensions as rows, and the pixel dimensions as columns.
As we have a 2D image here, with two pixel and two world axes where both are coupled together.
This means that to calculate either latitude or longitude you need both pixel coordinates.
