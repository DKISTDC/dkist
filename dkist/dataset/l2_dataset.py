import copy
import textwrap

import asdf

from ndcube import NDCollection

from dkist import Dataset


class Inversion(NDCollection):
    @classmethod
    def from_test_asdf(cls, asdf_file, *args, **kwargs):
        with asdf.open(asdf_file) as f:
            quants = set(f.tree["inversion"]["quantities"].keys()).difference({"axes", "shape", "wcs"})
            newtree = copy.copy(f.tree)
            for quant in quants:
                raw = f.tree["inversion"]["quantities"][quant]
                fm = raw.pop("data")
                raw["meta"]["inventory"] = {}
                ds = Dataset(**raw, data=fm.dask_array)
                ds._file_manager = fm
                newtree["inversion"]["quantities"][quant] = ds
                # ds.plot(plot_axes=['y', 'x', None])
                # plt.show()

            for profile in ["original", "fit"]:
                for wav in f.tree["inversion"]["profiles"][profile].keys():
                    raw = f.tree["inversion"]["profiles"][profile][wav]
                    fm = raw.pop("data")
                    raw["meta"]["inventory"] = {}
                    shape = fm.dask_array.shape
                    raw["wcs"].array_shape = shape
                    ds = Dataset(**raw, data=fm.dask_array)
                    ds._file_manager = fm
                    newtree["inversion"]["profiles"][profile][wav] = ds
            f.close()

            newtree["inversion"]["quantities"].pop("axes")
            newtree["inversion"]["quantities"].pop("shape")
            newtree["inversion"]["quantities"].pop("wcs")

            newtree["inversion"]["profiles"].pop("axes")
            newtree["inversion"]["profiles"].pop("wcs")
            old_profiles = newtree["inversion"]["profiles"]
            profiles = {}
            for k, v in old_profiles["original"].items():
                profiles[k] = v
            for k, v in old_profiles["fit"].items():
                profiles[k+"_fit"] = v
            profiles = NDCollection(profiles.items(), aligned_axes=(0, 1, 3))

        return cls(newtree["inversion"]["quantities"].items(), aligned_axes="all", profiles=profiles)

    def __init__(self, *args, profiles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.profiles = profiles

    def __str__(self):
        quants_repr = "\n".join(super().__str__().split("\n")[2:])
        profiles_repr = "\n".join(self.profiles.__str__().split("\n")[2:])
        s = """\
        Inversion
        ~~~~~~~~~
        {}

        Profiles
        ~~~~~~~~
        {}
        """

        return textwrap.dedent(s).format(quants_repr, profiles_repr)
