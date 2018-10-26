import os
import sys
import platform

mpath = os.path.dirname(os.path.realpath(__file__))
if not any(mpath in v for v in sys.path):
    # set module loading path for binary blobs
    if platform.system() == 'Windows':
        sys.path.insert(0, os.path.join(mpath, 'win64'))

    if platform.system() == 'Linux':
        sys.path.insert(0, os.path.join(mpath, 'linux'))

from qf_module import *
