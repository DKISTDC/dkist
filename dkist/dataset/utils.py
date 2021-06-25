"""
Helper functions for the Dataset class.
"""

import numpy as np

import gwcs

__all__ = ['dataset_info_str']


def dataset_info_str(ds):
    wcs = ds.wcs.low_level_wcs

    # Pixel dimensions table

    instr = ds.meta.get("instrument_name", "")
    if instr:
        instr += " "

    s = f"This {instr}Dataset has {wcs.pixel_n_dim} pixel and {wcs.world_n_dim} world dimensions\n\n"
    s += f"{ds.data}\n\n"

    array_shape = wcs.array_shape or (0,)
    pixel_shape = wcs.pixel_shape or (None,) * wcs.pixel_n_dim

    # Find largest between header size and value length
    if hasattr(wcs, "pixel_axes_names"):
        pixel_axis_names = wcs.pixel_axes_names
    elif isinstance(wcs, gwcs.WCS):
        pixel_axis_names = wcs.input_frame.axes_names
    else:
        pixel_axis_names = [''] * wcs.pixel_n_dim

    pixel_dim_width = max(9, len(str(wcs.pixel_n_dim)))
    pixel_nam_width = max(9, max(len(x) for x in pixel_axis_names))
    pixel_siz_width = max(9, len(str(max(array_shape))))

    s += (('{0:' + str(pixel_dim_width) + 's}').format('Pixel Dim') + '  ' +
            ('{0:' + str(pixel_nam_width) + 's}').format('Axis Name') + '  ' +
            ('{0:' + str(pixel_siz_width) + 's}').format('Data size') + '  ' +
            'Bounds\n')

    for ipix in range(ds.wcs.pixel_n_dim):
        s += (('{0:' + str(pixel_dim_width) + 'd}').format(ipix) + '  ' +
                ('{0:' + str(pixel_nam_width) + 's}').format(pixel_axis_names[::-1][ipix] or 'None') + '  ' +
                (" " * 5 + str(None) if pixel_shape[::-1][ipix] is None else
                ('{0:' + str(pixel_siz_width) + 'd}').format(pixel_shape[::-1][ipix])) + '  ' +
                '{:s}'.format(str(None if wcs.pixel_bounds is None else wcs.pixel_bounds[::-1][ipix]) + '\n'))
    s += '\n'

    # World dimensions table

    # Find largest between header size and value length
    world_dim_width = max(9, len(str(wcs.world_n_dim)))
    world_nam_width = max(9, max(len(x) if x is not None else 0 for x in wcs.world_axis_names))
    world_typ_width = max(13, max(len(x) if x is not None else 0 for x in wcs.world_axis_physical_types))

    s += (('{0:' + str(world_dim_width) + 's}').format('World Dim') + '  ' +
            ('{0:' + str(world_nam_width) + 's}').format('Axis Name') + '  ' +
            ('{0:' + str(world_typ_width) + 's}').format('Physical Type') + '  ' +
            'Units\n')

    for iwrl in range(wcs.world_n_dim):

        name = wcs.world_axis_names[::-1][iwrl] or 'None'
        typ = wcs.world_axis_physical_types[::-1][iwrl] or 'None'
        unit = wcs.world_axis_units[::-1][iwrl] or 'unknown'

        s += (('{0:' + str(world_dim_width) + 'd}').format(iwrl) + '  ' +
                ('{0:' + str(world_nam_width) + 's}').format(name) + '  ' +
                ('{0:' + str(world_typ_width) + 's}').format(typ) + '  ' +
                '{:s}'.format(unit + '\n'))

    s += '\n'

    # Axis correlation matrix

    pixel_dim_width = max(3, len(str(wcs.world_n_dim)))

    s += 'Correlation between pixel and world axes:\n\n'

    s += (' ' * world_dim_width + '  ' +
            ('{0:^' + str(wcs.pixel_n_dim * 5 - 2) + 's}').format('Pixel Dim') +
            '\n')

    s += (('{0:' + str(world_dim_width) + 's}').format('World Dim') +
            ''.join(['  ' + ('{0:' + str(pixel_dim_width) + 'd}').format(ipix)
                    for ipix in range(wcs.pixel_n_dim)]) +
            '\n')

    matrix = wcs.axis_correlation_matrix[::-1, ::-1]
    matrix_str = np.empty(matrix.shape, dtype='U3')
    matrix_str[matrix] = 'yes'
    matrix_str[~matrix] = 'no'

    for iwrl in range(wcs.world_n_dim):
        s += (('{0:' + str(world_dim_width) + 'd}').format(iwrl) +
                ''.join(['  ' + ('{0:>' + str(pixel_dim_width) + 's}').format(matrix_str[iwrl, ipix])
                        for ipix in range(wcs.pixel_n_dim)]) +
                '\n')

    # Make sure we get rid of the extra whitespace at the end of some lines
    return '\n'.join([l.rstrip() for l in s.splitlines()])
