import os
import sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if path not in sys.path:
    sys.path.append(path)
del path


def get_version():
    from AppiumLibrary.version import VERSION
    return VERSION
