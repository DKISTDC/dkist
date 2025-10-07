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
from dkist.Visualization import colormap_test_fits
# Register dkist colormaps
from dkist.Visualization import colormaps
```

```{code-cell} ipython3
from dkist.data.test import rootdir

colormap_test_fits = rootdir.glob("final_L1-*.fits")
```

## With VISP data

```{code-cell} ipython3
fitsfiles = colormap_test_fits["VISP"]
nims, nmaps = len(fitsfiles), len(colormaps.cmaps)
fig, axes = plt.subplots(nims, nmaps, figsize=(4*nmaps, 4*nims))
axes = axes.flatten()
a = 0
for f in fitsfiles:
	with fits.open(f) as hdus:
		im = hdus[0]
		vmin, vmax = np.nanpercentile(im.data, [1, 99])
		# for cmap_f in cmap_files:
		for cmap in mpl_cmaps:
			ax = axes[a]
			axc = ax.axis()
			# cmap = cmap_from_csv(cmap_f)
			print(f"Plotting {instrument} {f.name[6:-5]} in {cmap.name}")

			ax.imshow(im.data, cmap=cmap, vmin=vmin, vmax=vmax)#, aspect='auto')
			ax.set_title(cmap.name)
			ax.set_axis_off()

			a += 1
plt.tight_layout()
```

## With VBI data
