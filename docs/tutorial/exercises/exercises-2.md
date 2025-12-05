---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

+++ {"editable": true, "slideshow": {"slide_type": "slide"}}

# Exercise 1

+++ {"editable": true, "slideshow": {"slide_type": ""}}

Take the Cryo-NIRSP CI sample data and download the first 50 frames and save an animation (mp4) of these frames.

**Tips**

1. To download more frames of the sample data, you should set the path in the call to `ds.files.download` to download to a different directory.
2. `Dataset.plot` will return a [`mpl-animators.ArrayAnimatorWCS`](https://docs.sunpy.org/projects/mpl-animators/en/stable/api/mpl_animators.ArrayAnimatorWCS.html) object when the dataset is >2D. This object has a `get_animation` method which returns a [`FuncAnimation`](https://matplotlib.org/stable/api/_as_gen/matplotlib.animation.FuncAnimation.html).

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm

import dkist
from dkist.data.sample import CRYO_L1_TJKGC, CRYO_L1_MSCGD
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ci = dkist.load_dataset(CRYO_L1_MSCGD) # Load the context imager (CI) sample dataset
#ci[:50].files.download("~/dkist_data/CRYO_L1_MSCGD")
```

## Stage 2

```{code-cell} ipython3
---
editable: true
jupyter:
  outputs_hidden: true
slideshow:
  slide_type: skip
---
fig = plt.figure()
vmin, vmax = np.nanpercentile(ci[0].data, [1,99])
norm = PowerNorm(0.3, vmin=vmin, vmax=vmax)
ax = ci[:50].plot(norm=norm)
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
ani = ax.get_animation()
```

```{code-cell} ipython3
ani
```

```{code-cell} ipython3
---
editable: true
jupyter:
  outputs_hidden: true
slideshow:
  slide_type: skip
---
ani.save("animation.mp4")
```

```{code-cell} ipython3
---
editable: true
slideshow:
  slide_type: skip
---
from IPython.display import Video

Video("animation.mp4", embed=True)
```
