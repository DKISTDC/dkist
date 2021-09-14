import platform

from pkg_resources import get_distribution

from sunpy.extern.distro import linux_distribution
from sunpy.util.sysinfo import find_dependencies

__all__ = ['system_info']


def system_info():
    """
    Display information about your system for submitting bug reports.
    """
    base_reqs = get_distribution("dkist").requires()
    base_reqs = {base_req.name.lower() for base_req in base_reqs}

    missing_packages, installed_packages = find_dependencies(package="dkist")
    extra_prop = {"System": platform.system(),
                  "Arch": f"{platform.architecture()[0]}, ({platform.processor()})",
                  "Python": platform.python_version(),
                  "SunPy": get_distribution("dkist").version}
    sys_prop = {**installed_packages, **missing_packages, **extra_prop}

    print("==============================")
    print("DKIST Installation Information")
    print("==============================")
    print()
    print("General")
    print("#######")
    if sys_prop['System'] == "Linux":
        distro = " ".join(linux_distribution())
        print(f"OS: {distro} (Linux {platform.release()})")
    elif sys_prop['System'] == "Darwin":
        print(f"OS: Mac OS {platform.mac_ver()[0]}")
    elif sys_prop['System'] == "Windows":
        print(f"OS: Windows {platform.release()} {platform.version()}")
    else:
        print("Unknown OS")
    for sys_info in ['Arch', 'SunPy']:
        print('{} : {}'.format(sys_info, sys_prop[sys_info]))
    print()
    print("Required Dependices")
    print("###################")
    for req in base_reqs:
        print('{}: {}'.format(req, sys_prop[req]))
