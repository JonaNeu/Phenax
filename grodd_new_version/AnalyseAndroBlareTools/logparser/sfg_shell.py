#!/usr/bin/env python

from IPython.frontend.terminal.embed import InteractiveShellEmbed
from IPython.config.loader import Config

import libsystemflowgraph as lsfg
import graphtodot as sfgdot
import networkx as nx

cfg = Config()
ipshell = InteractiveShellEmbed(config=cfg, banner1="An intercative shell for manipulating system flow graphs")
ipshell()
