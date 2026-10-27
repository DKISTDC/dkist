Fix `~dkist.wcs.models.VaryingCelestialTransform` and `~dkist.wcs.models.Ravel` returning NaN at the far pixel edge of an even-length axis.
A lookup halfway between two table rows now always uses the later row.
