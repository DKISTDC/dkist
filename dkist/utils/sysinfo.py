import platform
from importlib.metadata import version, distribution

import sunpy.extern.distro as distro
from sunpy.util.sysinfo import find_dependencies, get_keys_list, get_requirements

__all__ = ["system_info"]


def system_info():
    """
    Prints one's system info in an "attractive" fashion.
    """
    package_name = "dkist"
    requirements = get_requirements(package_name)
    base_reqs = get_keys_list(requirements["required"])
    missing_packages, installed_packages = find_dependencies(package=package_name)
    extra_prop = {"System": platform.system(),
                  "Arch": f"{platform.architecture()[0]}, ({platform.processor()})",
                  "Python": platform.python_version(),
                  package_name: version(package_name)}
    sys_prop = {**installed_packages, **missing_packages, **extra_prop}
    title_str = f"{package_name} Installation Information"
    print("=" * len(title_str))
    print(title_str)
    print("=" * len(title_str))
    print()
    print("General")
    print("#######")
    if sys_prop["System"] == "Linux":
        print(f"OS: {distro.name()} ({distro.version()}, Linux {platform.release()})")
    elif sys_prop["System"] == "Darwin":
        print(f"OS: Mac OS {platform.mac_ver()[0]}")
    elif sys_prop["System"] == "Windows":
        print(f"OS: Windows {platform.release()} {platform.version()}")
    else:
        print("Unknown OS")
    for sys_info in ["Arch", package_name]:
        print(f"{sys_info}: {sys_prop[sys_info]}")
    print(f"Installation path: {distribution(package_name)._path}")
    print()
    print("Required Dependencies")
    print("#####################")
    for req in base_reqs:
        print(f"{req}: {sys_prop[req]}")
