class DKISTWarning(Warning):
    """
    The base warning class from which all dkist warnings should inherit.
    """

class DKISTUserWarning(UserWarning, DKISTWarning):
    """
    The primary warning class for dkist.

    Use this if you do not need a specific type of warning.
    """

class DKISTDeprecationWarning(DeprecationWarning, DKISTWarning):
    """
    A warning class to use when functionality will be changed or removed in a future version.
    """
