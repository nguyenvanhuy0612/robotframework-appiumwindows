import os
import sys

dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if dir not in sys.path:
    sys.path.append(dir)
del dir

def get_version():
    from AppiumLibrary.version import VERSION
    return VERSION