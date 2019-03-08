from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

import astropy.units as u
from astropy.visualization.wcsaxes import WCSAxes
from astropy.visualization.wcsaxes.transforms import CurvedTransform
from gwcs.coordinate_frames import CelestialFrame, CompositeFrame
from ndcube.mixins import NDCubePlotMixin
from sunpy.visualization import wcsaxes_compat
from sunpy.visualization.animator import ImageAnimator, ImageAnimatorWCS

__all__ = ['ImageAnimatorDataset', 'DatasetPlotMixin']


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
        Generate a WCAxes coord_meta for the two axes to be plotted.
        """
        inds = [i for i, b in enumerate(self.dataset.missing_axis[::-1]) if not b]

        if len(inds) != 2:
            raise ValueError("Can only compute coord_meta for two axes")

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
                if wrap is not None:
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
        """
        Allow this class to be converted to a WCSAxes object by matplotlib.
        """
        return WCSAxes, {'transform': self, 'coord_meta': self.coord_meta}

    @property
    def input_units(self):
        if self.invert:  # pragma: no cover
            return self.dataset.wcs.output_frame.unit
        else:
            return self.dataset.wcs.input_frame.unit

    @property
    def output_units(self):
        if self.invert:  # pragma: no cover
            return self.dataset.wcs.input_frame.unit
        else:
            return self.dataset.wcs.output_frame.unit

    @property
    def call(self):
        if self.invert:  # pragma: no cover
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
        pass  # pragma: no cover


class DatasetPlotMixin(NDCubePlotMixin):
    """
    Handle plotting operations for Dataset.
    """

    def _as_mpl_axes(self):
        """
        Allow this class to be converted to a WCSAxes object by matplotlib.
        """
        return DatasetTransform(self)._as_mpl_axes()

    @property
    def _axis_labels(self):
        """
        Generate axes labels for a plot of this dataset.
        """
        components = [(self.world_axes_names[i],
                       self.axis_units[i]) for i, b in enumerate(self.missing_axis) if not b]
        return [f"{name} [{unit}]" for name, unit in components[::-1]]

    def _plot_3D_cube(self, plot_axis_indices=None, axes_coordinates=None,
                      axes_units=None, data_unit=None, **kwargs):
        if axes_units is None:
            axes_units = [None] * self.data.ndim

        # Generate plot
        return ImageAnimatorDataset(self, image_axes=plot_axis_indices,
                                    unit_x_axis=axes_units[plot_axis_indices[0]],
                                    unit_y_axis=axes_units[plot_axis_indices[1]],
                                    **kwargs)

    def _plot_2D_cube(self, axes=None, plot_axis_indices=None, axes_coordinates=None,
                      axes_units=None, data_unit=None, **kwargs):
        if plot_axis_indices and plot_axis_indices != [-1, -2]:
            raise NotImplementedError("Can't do this yet")

        if axes is None:
            axes = wcsaxes_compat.gca_wcs(DatasetTransform(self))

        coords = axes.coords

        for i, c in enumerate(coords):
            c.set_axislabel(self._axis_labels[i])

        if axes_units and len(axes_units) == 2:
            for i, c in enumerate(coords):
                c.set_format_unit(axes_units[i])

        mpl_kwargs = {'origin': 'lower'}
        mpl_kwargs.update(kwargs)
        plot = axes.imshow(self.data, **mpl_kwargs)

        return plot


class ImageAnimatorDataset(ImageAnimatorWCS):
    """
    Animates an N-Dimesional DKIST Dataset.
    """
    def __init__(self, dataset, image_axes=[-1, -2],
                 unit_x_axis=None, unit_y_axis=None, axis_ranges=None,
                 **kwargs):
        self.unit_x_axis = unit_x_axis
        self.unit_y_axis = unit_y_axis
        self.slices_wcsaxes = ("x", "y")
        self._dataset = dataset

        ImageAnimator.__init__(self, dataset.data, image_axes=image_axes,
                               axis_ranges=axis_ranges, **kwargs)

    @property
    def wcs(self):
        return self.dataset

    @property
    def dataset(self):
        """
        Return a sliced version of the dataset.
        """
        return self._dataset[self.frame_index]

    @property
    def _axis_labels(self):
        """
        Generate axes labels for a plot of this dataset.
        """
        components = [(self.dataset.world_axes_names[i],
                       self.dataset.axis_units[i]) for i, b in enumerate(self.dataset.missing_axis) if not b]
        if self.unit_y_axis:
            components[0] = (components[0][0], self.unit_y_axis)
        if self.unit_x_axis:
            components[1] = (components[1][0], self.unit_x_axis)
        return [f"{name} [{unit}]" for name, unit in components[::-1]]

    def _set_unit_in_axis(self, axes):
        if self.unit_x_axis is not None:
            axes.coords[0].set_format_unit(self.unit_x_axis)
            axes.coords[0].set_ticklabel(exclude_overlapping=True)
        if self.unit_y_axis is not None:
            axes.coords[1].set_format_unit(self.unit_y_axis)
            axes.coords[1].set_ticklabel(exclude_overlapping=True)

    def plot_start_image(self, ax):
        im = super().plot_start_image(ax)
        # If the axes are not very square we probably are not plotting the image
        if abs(1 - (self.data.shape[self.image_axes[0]] / self.data.shape[self.image_axes[1]])) > 0.1:
            ax.axis("auto")
        coords = ax.coords
        for i, c in enumerate(coords):
            c.set_axislabel(self._axis_labels[i])
        return im

    def update_plot(self, val, im, slider):
        """Updates plot based on slider/array dimension being iterated."""
        val = int(val)
        ax_ind = self.slider_axes[slider.slider_ind]
        ind = int(np.argmin(np.abs(self.axis_ranges[ax_ind] - val)))
        self.frame_slice[ax_ind] = ind
        if val != slider.cval:
            dstf = DatasetTransform(self.wcs)
            self.axes.reset_wcs(transform=dstf, coord_meta=dstf.coord_meta)
            self._set_unit_in_axis(self.axes)

            coords = self.axes.coords
            for i, c in enumerate(coords):
                c.set_axislabel(self._axis_labels[i])

            im.set_array(self.data[self.frame_index])
            slider.cval = val
