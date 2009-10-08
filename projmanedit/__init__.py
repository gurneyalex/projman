# This file should be modified by the installer

GLADE="%GLADEFILE%"

import os

if not os.access(GLADE, os.R_OK):
    import sys
    import os.path as osp
    # custom configuration for running from the devel directory
    _main_module = sys.modules[__name__]
    _main_dir = osp.dirname( _main_module.__file__)
    _toplevel = osp.abspath(osp.join(_main_dir,".."))
    GLADE = osp.join(_toplevel, "data", "projedit.glade")
    if not os.access(GLADE, os.R_OK):
        raise RuntimeError("Can't open glade resources for projman-gui")
