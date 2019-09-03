from asdf.types import CustomType

__all__ = ['DKISTType']


class DKISTType(CustomType):
    """
    Base class for asdf tags defined in the DKIST User Tools.
    """
    organization = 'dkist.nso.edu'
    standard = 'dkist'
    version = '1.0.0'

    _tags = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._tags.add(cls)
