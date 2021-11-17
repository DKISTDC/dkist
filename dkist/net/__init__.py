"""
DKIST specific plugins for `sunpy.net` and download helpers.

.. warning::

   Classes in this module should not be used directly, they should be used
   through the `sunpy.net.Fido` and `sunpy.net.attrs.dkist` modules. The
   classes in this module will be automatically registered with sunpy upon
   importing this module with `import dkist.net`.

"""
from .client import DKISTDatasetClient
