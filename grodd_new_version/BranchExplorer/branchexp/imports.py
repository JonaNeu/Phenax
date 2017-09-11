# pylint: disable=unused-import

from branchexp.utils.utils import quit


# External packages, available on PyPI or their repository

try:
    import networkx
except ImportError:
    quit("Can't import NetworkX, is it installed correctly?")

try:
    import pygraphviz
except ImportError:
    quit( "Can't import PyGraphviz. You have to install it from Github at "
          + "https://github.com/pygraphviz/pygraphviz" )

try:
    import uiautomator
except ImportError:
    quit("Can't import UIautomator, is it installed correctly?")


# Internal packages, available in a directory of the MalwareTrigger repository

try:
    import manifest_parser
except ImportError:
    quit("Can't import ManifestParser, install it from our repository.")

try:
    import acfg_tools
except ImportError:
    quit("Can't import ACFG tools, install them from our repository.")
