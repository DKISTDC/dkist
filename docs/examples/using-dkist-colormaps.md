---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.6
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Using DKIST colormaps

The Python tools define a small number of custom colormaps designed for use with DKIST data.

```{code-cell} ipython3
import matplotlib.pyplot as plt
# Register dkist colormaps
from dkist.visualization import colormaps
from astropy.io import fits
```

## With VISP data

```{code-cell} ipython3
fitsfiles = colormaps.colormap_test_fits["VISP"]
print(fitsfiles)
```
```{code-cell} ipython3
images = [fits.open(f)[0] for f in fitsfiles]
nims, nmaps = len(fitsfiles), len(colormaps.cmaps)
for cmap in colormaps.cmaps:
	fig, axes = plt.subplots(1, nims)
	axes = axes.flatten()
	for im, ax in zip(images, axes):
		vmin, vmax = np.nanpercentile(im.data, [1, 99])

		ax.imshow(im.data, cmap=cmap, vmin=vmin, vmax=vmax)#, aspect='auto')
		ax.set_title(cmap.name)
		ax.set_axis_off()

	plt.tight_layout()
	plt.show()
```

## With VBI data
