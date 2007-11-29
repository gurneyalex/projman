# This file should be modified by the installer

GLADE="%GLADEFILE%"




if GLADE=="%GLADEFILE%":
    import sys
    import os.path as osp
    # custom configuration for running from the devel directory
    _main_module = sys.modules[__name__]
    _main_dir = osp.dirname( _main_module.__file__)
    _toplevel = osp.abspath(osp.join(_main_dir,".."))
    print "Running from %s" % _toplevel
    GLADE = osp.join(_toplevel, "data", "projedit.glade")
