"""
This module contains tools for slicing gwcs objects.
"""

from astropy.modeling import Model, Parameter
from astropy.modeling.models import Identity


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

    >>> myslicedgwcs = Slicer(mygwcs)[10, : , 0]
    """
    def __init__(self, gwcs, copy=False):
        if copy:
            gwcs = copy.deepcopy(gwcs)
        self.gwcs = gwcs
        self.naxis = wcsobj.forward_transform.n_inputs
        self.separable = separable.is_separable(self.gwcs.forward_transform)
        self._compare_frames_separable()

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

    def _compare_frames_separable(self):
        """
        Validate that the coupled (via frames) and separable (via the model)
        information matches.
        """
        coupled_axes = self._get_coupled_axes()
        for pair in coupled_axes:
            for ax in pair:
                if self.separable[ax]:
                    raise ValueError("Panic")

    def _get_axes_map(self, frames):
        """
        Map the number of the axes to its frame.
        """
        axes_map = {}
        for frame in frames:
            for ax in frame.axes_order:
                axes_map[ax] = frame

        return axes_map

    def _new_output_frame(self, axes):
        """
        remove the frames for all axes and return a new output frame
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

    def _sanitize(self, item):
        """
        Convert the item into a list of items. Which is the same length
        as the number of axes in the input frame.

        The output list will either contain a slice object for a range
        (if the slice.start is None then no operation is done on that axis)
        or an integer if the value of the axis is to be fixed.
        """
        if not isinstance(item, (tuple, list)): # We just have a single int
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

        return item

    def _list_to_compound(self, models):
        """
        Convert a list of models into a compound model using the ``&`` operator.
        """
        # Convert the list of models into a CompoundModel
        comp_m = models[0]
        for m in models[1:]:
            comp_m = comp_m & m
        return comp_m

    def __getitem__(self, item):
        """
        Once the item is sanitized, we fix the parameter if the item is an integer,
        shift if the start is set on the slice or
        do nothing to the axis otherwise.
        """
        item = self._sanitize(item)

        prepend = []
        append = []
        axes_to_drop = []

        # Iterate over all the axes and keep a list of models to append or
        # prepend to the transform, and a list of axes to remove from the wcs
        # completely.

        # We always add a model to prepend and append lists so that we maintain
        # consistency with the number of axes. If prepend or append is entirely
        # identity models, they are not used.
        for i, ax in enumerate(item):
            if isinstance(ax, int):
                if self.separable[i]:
                    axes_to_drop.append(i)
                else:
                    prepend.append(FixedParameter(ax*u.pix))
                    append.append(Identity(1))
            elif ax.start:
                prepend.append(Shift(ax.start*u.pix))
                append.append(Identity(1))
            else:
                prepend.append(Identity(1))
                append.append(Identity(1))

        model = self.gwcs.forward_transform
        for drop_ax in axes_to_drop:
            inp = model._tree.inputs[drop_ax]
            trees = remove_input_frame(model._tree, inp)
            model = re_model_trees(trees)

        if not all([isinstance(a, Identity) for a in prepend]):
            model = self._list_to_compound(prepend) | model

        if not all([isinstance(a, Identity) for a in append]):
            model = model | self._list_to_compound(append)

        new_in_frame = self.gwcs.input_frame
        new_out_frame = self.gwcs.output_frame
        if axes_to_drop:
            # new_in_frame = self._new_input_frame(axes_to_drop)
            new_out_frame = self._new_output_frame(axes_to_drop)

        # Update the gwcs
        self.gwcs._initialize_wcs(model, new_in_frame, new_out_frame)

        return self.gwcs
