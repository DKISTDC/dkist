from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

import astropy.units as u
from ndcube.mixins import NDCubePlotMixin
from sunpy.visualization import wcsaxes_compat
from gwcs.coordinate_frames import CelestialFrame, CompositeFrame
from sunpy.visualization.animator import ImageAnimator
from astropy.visualization.wcsaxes.transforms import CurvedTransform
from astropy.visualization.wcsaxes import WCSAxes

__all__ = ['DatasetPlotMixin']


class DatasetTransform(CurvedTransform):
    """
    Wrap a `dkist.dataset.Dataset` object up as a matplotlib compatible transform.
    """
    has_inverse = False

    # TODO: Add back support for inverse
    def __init__(self, dataset, invert=False):
        super().__init__()
        self.dataset = dataset
        self.invert = invert

    @property
    def coord_meta(self):
        """
        Generate a coord_meta for the two axes to be plotted.
        """
        inds = [i for i, b in enumerate(self.dataset.missing_axis[::-1]) if not b]

        frames = self.dataset.wcs.output_frame.frames if isinstance(self.dataset.wcs.output_frame,
                                                                    CompositeFrame) else (self.dataset.wcs.output_frame,)
        order_to_frames = {}
        for aframe in frames:
            for order in aframe.axes_order:
                order_to_frames[order] = aframe

        type_map = defaultdict(lambda: 'scalar')
        type_map['lat'] = 'latitude'
        type_map['lon'] = 'longitude'

        coord_meta = defaultdict(lambda: [])

        orders = sorted(tuple(order_to_frames.keys()))
        for order in orders:
            frame = order_to_frames[order]
            frame_ind = frame.axes_order.index(order)
            if order not in inds:
                continue
            if isinstance(frame, CelestialFrame):
                name = 'lon' if not frame_ind else 'lat'  # lon is always first
                wrap = getattr(frame.reference_frame, "_default_wrap_angle", None) if name == "lon" else None
                if wrap:
                    wrap = int(wrap.to_value(u.deg))
            else:
                name = frame.axes_names[frame_ind]
                wrap = None
            coord_meta['unit'].append(frame.unit[frame_ind])
            coord_meta['format_unit'].append(frame.unit[frame_ind])
            coord_meta['name'].append(name)
            coord_meta['wrap'].append(wrap)
            coord_meta['type'].append(type_map[name])

        return dict(coord_meta)

    def _as_mpl_axes(self):
        return WCSAxes, {'transform': self, 'coord_meta': self.coord_meta}

    @property
    def input_units(self):
        if self.invert:
            return self.dataset.wcs.output_frame.unit
        else:
            return self.dataset.wcs.input_frame.unit

    @property
    def output_units(self):
        if self.invert:
            return self.dataset.wcs.input_frame.unit
        else:
            return self.dataset.wcs.output_frame.unit

    @property
    def call(self):
        if self.invert:
            return self.dataset.wcs.invert
        else:
            return self.dataset.wcs

    def transform(self, input_coords):
        inds = [i for i, b in enumerate(self.dataset.missing_axis[::-1]) if not b]

        x = input_coords[:, 0] * self.input_units[0]
        y = input_coords[:, 1] * self.input_units[1]

        outs = self.call(x, y)
        x_out = outs[inds[0]]
        y_out = outs[inds[1]]

        x_out = x_out.to_value(self.output_units[inds[0]])
        y_out = y_out.to_value(self.output_units[inds[1]])

        return np.vstack((x_out, y_out)).T

    def inverted(self):
        pass


class DatasetPlotMixin(NDCubePlotMixin):  # pragma: no cover
    """
    Handle plotting operations for Dataset.
    """

    def _plot_3D_cube(self, plot_axis_indices=None, axes_coordinates=None,
                      axes_units=None, data_unit=None, **kwargs):
        raise NotImplementedError("Only two dimensional plots are supported")

    def _plot_2D_cube(self, axes=None, plot_axis_indices=None, axes_coordinates=None,
                      axes_units=None, data_unit=None, **kwargs):
        """
        Plots a 2D image onto the current
        axes. Keyword arguments are passed on to matplotlib.

        Parameters
        ----------
        axes: `astropy.visualization.wcsaxes.core.WCSAxes` or `None`:
            The axes to plot onto. If None the current axes will be used.

        image_axes: `list`.
            The first axis in WCS object will become the first axis of image_axes and
            second axis in WCS object will become the second axis of image_axes.
            Default: ['x', 'y']
        """
        if plot_axis_indices and plot_axis_indices != [-1, -2]:
            raise NotImplementedError("Can't do this yet")

        if axes is None:
            axes = wcsaxes_compat.gca_wcs(DatasetTransform(self))

        mpl_kwargs = {'origin': 'lower'}
        mpl_kwargs.update(kwargs)
        plot = axes.imshow(self.data, **mpl_kwargs)

        return plot
