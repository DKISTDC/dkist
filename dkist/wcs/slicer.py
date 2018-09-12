"""
This module contains tools for slicing gwcs objects.
"""
from copy import deepcopy

from astropy.modeling import Model, Parameter, separable
from astropy.modeling.models import Identity, Shift

import gwcs.coordinate_frames as cf

from dkist.utils.model_tools import remove_input_frame, re_model_trees


__all__ = ['GWCSSlicer', 'FixedParameter']


class FixedParameter(Model):
    """
    A Model that injects a parameter as an output.

    The inverse of this model does nothing (is the ``Identity`` model), as the
    parameter is only defined in the input direction.
    """
    value = Parameter()
    inputs = tuple()
    outputs = ('x',)

    @staticmethod
    def evaluate(value):
        return value[0]

    @property
    def inverse(self):
        return Identity(1)


class GWCSSlicer:
    """
    A class which will slice a gwcs object when its ``__getitem__`` method is called.

    Parameters
    ----------
    gwcs : `gwcs.wcs.WCS`
        A gwcs model to be sliced.

    copy : `bool`
        A flag to determine if the input gwcs should be copied.

    Examples
    --------

    >>> myslicedgwcs = Slicer(mygwcs)[10, : , 0]  # doctest: +SKIP
    """
    def __init__(self, gwcs, copy=False):
        if copy:
            gwcs = deepcopy(gwcs)
        self.gwcs = gwcs
        self.naxis = self.gwcs.forward_transform.n_inputs
        self.separable = self._build_separable_array()
        # self._compare_frames_separable()

    def _get_frames(self):
        """
        Return a list of frames which comprise the output frame.
        """
        if hasattr(self.gwcs.output_frame, "frames"):
            frames = self.gwcs.output_frame.frames
        else:
            frames = (self.gwcs.output_frame,)
        return frames

    def _get_coupled_axes(self):
        """
        Return the a list of axes number tuples which are coupled by sharing a frame.
        """
        frames = self._get_frames()

        coupled_axes = []
        for frame in frames:
            if len(frame.axes_order) > 1:
                coupled_axes.append(frame.axes_order)

        return coupled_axes

    def _build_separable_array(self):
        """
        Combine the information on seprability from the forward transform with
        copupling information from the output frames.
        """
        mseparable = separable.is_separable(self.gwcs.forward_transform)
        coupled = self._get_coupled_axes()
        mseparable[coupled] = False
        return mseparable

    def _get_axes_map(self, frames):
        """
        Map the number of the axes to its frame.
        """
        axes_map = {}
        for frame in frames:
            for ax in frame.axes_order:
                axes_map[ax] = frame

        return axes_map

    def _input_units(self):
        """
        Return a dict mapping input number to a "unit". If the model does not use units, return 1.
        """
        ft = self.gwcs.forward_transform
        return {inp: ft.input_units.get(ft.inputs[inp], 1) if ft.input_units else 1 for inp in range(ft.n_inputs)}

    def _new_output_frame(self, axes):
        """
        remove the frames for all axes and return a new output frame.

        This method assumes axes has already been sanitized for non-separable axes.
        """
        frames = self._get_frames()
        axes_map = self._get_axes_map(frames)

        frames = list(frames)
        for axis in axes:
            drop_frame = axes_map[axis]
            frames.remove(drop_frame)

        if len(frames) == 1:
            return frames[0]
        else:
            return cf.CompositeFrame(frames, name=self.gwcs.output_frame.name)

    def _new_input_frame(self, axes):
        """
        remove the given axes from the input frame.
        """
        iframe = self.gwcs.input_frame
        assert isinstance(iframe, cf.CoordinateFrame) and not isinstance(iframe, cf.CompositeFrame)
        assert iframe._reference_position is None and iframe._reference_frame is None

        mods = ("axes_type", "unit", "axes_names")
        copys = ("name",)

        attrs = {}
        for ax in axes:
            for m in mods:
                n = list(getattr(iframe, m))
                n.pop(ax)
                attrs[m] = tuple(n)

        for at in copys:
            attrs[at] = getattr(iframe, at)

        attrs["naxes"] = iframe.naxes - len(axes)

        attrs["axes_order"] = tuple(range(attrs["naxes"]))

        r = type(iframe)(**attrs)
        return r

    def _list_to_compound(self, models):
        """
        Convert a list of models into a compound model using the ``&`` operator.
        """
        # Convert the list of models into a CompoundModel
        comp_m = models[0]
        for m in models[1:]:
            comp_m = comp_m & m
        return comp_m

    def _sanitize(self, item):
        """
        Convert the item into a list of items. Which is the same length
        as the number of axes in the input frame.

        The output list will either contain a slice object for a range
        (if the slice.start is None then no operation is done on that axis)
        or an integer if the value of the axis is to be fixed.
        """
        if not isinstance(item, (tuple, list)):  # We just have a single int
            item = (item,)

        item = list(item)

        for i in range(self.naxis):
            if i < len(item):
                ax = item[i]
                if isinstance(ax, slice):
                    if ax.step:
                        raise ValueError("can not change step yet")
                elif not isinstance(ax, int):
                    raise ValueError("Only integer or range slices are accepted.")
            else:
                item.append(slice(None))

        # Reverse the slice to match the physical coordinates and not the pixel ones
        return item

    def __getitem__(self, item):
        """
        Once the item is sanitized, we fix the parameter if the item is an integer,
        shift if the start is set on the slice or
        do nothing to the axis otherwise.
        """
        item = self._sanitize(item)

        prepend = []
        axes_to_drop = []

        # Iterate over all the axes and keep a list of models prepend to the
        # transform, and a list of axes to remove from the wcs completely.

        # We always add a model to prepend list so that we maintain consistency
        # with the number of axes. If prepend is entirely identity models, it
        # is not used.
        input_units = self._input_units()
        for i, ax in enumerate(item):
            if isinstance(ax, int):
                if self.separable[i]:
                    axes_to_drop.append(i)
                else:
                    prepend.append(FixedParameter(ax*input_units[i]))
            elif ax.start:
                prepend.append(Shift(ax.start*input_units[i]))
            else:
                prepend.append(Identity(1))

        model = self.gwcs.forward_transform
        for drop_ax in axes_to_drop:
            inp = model._tree.inputs[drop_ax]
            trees = remove_input_frame(model._tree, inp)
            model = re_model_trees(trees)

        if not all([isinstance(a, Identity) for a in prepend]):
            model = self._list_to_compound(prepend) | model

        new_in_frame = self.gwcs.input_frame if self.gwcs.input_frame else "pixel frame"
        new_out_frame = self.gwcs.output_frame
        if axes_to_drop:
            new_in_frame = self._new_input_frame(axes_to_drop)
            new_out_frame = self._new_output_frame(axes_to_drop)

        # Update the gwcs
        self.gwcs._initialize_wcs(model, new_in_frame, new_out_frame)

        return self.gwcs
