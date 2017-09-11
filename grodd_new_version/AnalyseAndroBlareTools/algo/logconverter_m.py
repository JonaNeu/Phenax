#!/usr/bin/env python

import sys
import graphtodot
import argparse
import time
import ply.lex as lex
import networkx as nx
import ply.yacc as yacc
import math
import string
import libsystemflowgraph as lsfg
import re
import os.path
import os
from multiprocessing import Pool

# Define a list of couple (pattern, substitute) that can serve to format correctly a log entry 
regexp_list = [("> itag\[(-*[0-9 ]*)\]", "> {\\1}"), ("}select.*$", "}"), ("> \(null\)", "> {0}"), ("}failed.*$", "}"), ("}.+$", "}"), #("^.* > file /dev/cpuctl/tasks .*$", ""),
    ("re-initialized>", "re-initialized"), ("(process .*)\]", "\\1"), ("([^ >\\n\\t])\[", "\\1"), ("'", ""), (" #", "#"), ("Binder Thread", "BinderThread"), ("> process ([0-9])", "> process a\\1"), ("\] process ([0-9])", "\] process a\\1")]

# List of regexp that will serve to discard unwanted log entries
discard_filter = ["> file /proc/.*/oom_adj", "> {}$", "> file /sys/power/wake_", "/dev/cpuctl/bg_non_interactive/tasks", "\[BLARE\]", "^.* > file /dev/cpuctl/tasks .*$"]

argparser = argparse.ArgumentParser(description="Process blare log to build graphs", usage="logconverter-nx.py -i input [--cluster_system] --o_type <TYPE1> <TYPE2> -j N --id N")
argparser.add_argument('-i', help='Specify the input file to be parsed', action='store', required=False, dest='input')
argparser.add_argument('--cluster_system', help='Cluster threads running in system_server process', action='store_true', required=False, default=False)
argparser.add_argument('--thread_node', help='Specify if threads of the same process should be represented by different nodes or not', action='store_true', required=False, default=False)
argparser.add_argument('--o_type', help='Specify the file output type(s). Supported types are dot, gexf and pickle', required=False, nargs='+')
argparser.add_argument('--id', help='Specify an information identifier. The output graph will describe how the information flow', action='store', required=False, default=False, dest='info_id', type=int)
argparser.add_argument('--ntime', help='Replace each timestamp with an integer value t such as the timestamp of the previous flow was t-1 and the next one is t+1 ', action='store_true', required=False, default=False)
argparser.add_argument('-j', help='Define the number of jobs to use. It can be useful if we want to parse more than one Blare log', required=False, default=1, dest='job', type=int)
args = argparser.parse_args()


def clean_entry(line, sub_re=None, disc_re=None):
    """
    Return a new version of line that was stripped from any noise due to other kernel messages.
    line is a string that represent a log entry (a description of a flow).
    sub_re is a dictionnary which keys are regexp that should be replaced by the value corresponding to the keys
    disc_re is a list of discarding patterns. If line contains one of the pattern, clean_entry will return None to indicate that line should be ignored
    """
    res = line
    for pattern, repl in sub_re :
        res = re.sub(pattern, repl, res)
    for pattern in disc_re:
        if not (re.search(pattern, res) is None):
            return None 
    return res

def same_container(cont1, cont2):
    """
    Return True if cont1 and cont2 are the same containers.We assume that processes
    that share the same PID are the same container even if their name differ. We 
    assume that files that are located in the same directory and share the same
    inode are the same containers too even if their name differ. In reality
    this should not be limited to files in the same directory but located in the
    same partition.
    """
    partition_list = ["/data", "/system", "/mnt/sdcard", "/sdcard"] 
    if (cont1 == cont2):
        return True
    if (cont1[0] == cont2[0]):
        if (cont1[0] == 'process'):
            return cont1[2] == cont2[2]
        elif (cont1[0] == 'file') and (cont1[2] == cont2[2]):
            s1 = cont1[1].split("/")
            s2 = cont2[1].split("/")
            if len(s1) == len (s2):
                i = 0
                equal = True
                while equal and (i < (len(s1) - 2)):
                    if not (s1[i] == s2[i]):
                        equal = False
                    i += 1
                if equal:
                    return True
        elif (cont1[0] == 'socket') :
            return cont1[1] == cont2[1]
    return False

def cleansfg(sfg):
    """
    Remove nodes that do not have neighbors in sfg
    """
    to_be_removed = []
    for node in sfg.nodes() :
        if ((len(lsfg.get_out_edges(sfg, node)) == 0) and (len(lsfg.get_in_edges(sfg, node)) == 0)):
            to_be_removed.append(node)

    for elt in to_be_removed:
        sfg.remove_node(elt)


# Tokens
tokens = (
    'TIMESTAMP',
    'INTEGER',
    'STRING',
    #'LEVEL',
)

literals = ['[', ']', '-', '<', '>', '{', '}']

def t_TIMESTAMP(t):
    r'\d+\.\d+'
    t.value = (int) (math.pow(10, 6) * float(t.value)) 
    return t


def t_INTEGER(t):
    r'[+-]?\d+'
    t.value = int(t.value)
    return t

#t_STRING = r'[^ \n<>()\[\]{}+]'
t_STRING = r'[a-zA-Z0-9/#.()$:@_-]+'
t_ignore = ' \n\t'

#def t_newline(t):
#   r'\n+'
#   t.lexer.lineno += len(t.value)

def t_error(t):
    print "Illegal character at line " + str(lineno) + " : *+  " +  t.value + " +*"
    t.lexer.skip(1)
    #quit()

def find_column(input,token):
    last_cr = input.rfind('\n',0,token.lexpos)
    if last_cr < 0:
        last_cr = 0
    column = (token.lexpos - last_cr) + 1
    return column



lexer = lex.lex(debug=0)

# Grammar of the alert-log that can be parsed
# ALERT : KERN_MSG_LEVEL '['timestamp']' '['MSG_TAG']' CONTAINER '>' CONTAINER > '{' FLOW '}'
#
# CONTAINER : string string C_ID        ;; first string is the container type and the second one is its name
#
# C_ID : integer
#
# FLOW : integer FLOW
#   | integer
# 
# A container is meant to be converted into a vertex and a flow into an edge

flow_graph = nx.MultiDiGraph()
new_node_id = 0


def p_alert(p):
    ''' alert : level '[' TIMESTAMP ']' '[' STRING ']' container '>' container '>' '{' flow '}' '''
    # Add code to link vertexes corresponding to the flow
    edge_flows = nx.get_edge_attributes(flow_graph, 'flow')
    current_flow = []
    if (args.info_id == False):
                current_flow = p[13]
    elif (args.info_id in p[13]):
        current_flow = [args.info_id]
    if (current_flow != []):
        flow_set = set(current_flow)
        for edge in flow_graph.edges(data=True, keys=True):
            if ((edge[0], edge[1]) == (p[8], p[10])) and (set(edge[3]['flow']) == flow_set):
                edge[3]['timestamp'].append(p[3])
                return
        flow_graph.add_edge(p[8], p[10], flow=current_flow, timestamp=[p[3]])
        
        # Check if p[8] is the apk that was analysed. If that is the case then give its name
        # as the value of the attribute app_name of the SFG
        if not (flow_graph.graph.has_key('app_name') and (flow_graph.graph['app_name'] != "")):
            if ((p[8][0] == "file") and (p[10][0] == "process") and p[8][1].startswith("/data/app/") 
                    and p[8][1].endswith("apk")):
                f_name = p[8][1].split("/")[3]
                if f_name.find(p[10][1]):
                    flow_graph.graph["app_name"] = f_name.replace("-1.apk", "").replace(".apk", "")



def p_level(p):
    ''' level : '<' INTEGER '>' '''
    p[0] = p[2]  

def p_container(p):
    'container : STRING container_name INTEGER' 
    #global new_node_id
    global args
    cont_name = p[2]
    if (args.thread_node == False):
        cont_name = p[2].split(":", 1)[0]   
        new_node = (p[1], cont_name, p[3])
        
    if (not flow_graph.has_node(new_node)):
        flow_graph.add_node(new_node)
        if (new_node[0] == 'process') or (new_node[0] == 'file'):
            # We assume that a PID is a unique identifier for all processes listed in the log.
            # So if two processes have the same PID we assume that they are the same process but
            # its name changed during its execution. It can happen
            former = None
            for n in flow_graph.nodes():
                if same_container(n, new_node):
                    former = n
                    break
            if not (former is None):
                for e in lsfg.get_out_edges(flow_graph, former):
                    flow_graph.add_edge(new_node, e[1], flow=e[3]['flow'], timestamp=e[3]['timestamp'])
                for e in lsfg.get_in_edges(flow_graph, former):
                    flow_graph.add_edge(e[0], new_node, flow=e[3]['flow'], timestamp=e[3]['timestamp'])
                flow_graph.remove_node(former)
    p[0] = new_node
    
def p_container_name(p):
    ''' container_name : STRING
            | container_name2'''
    p[0] = p[1]

def p_container_name2(p):
    'container_name2 : STRING container_name'
    p[0] = p[1] + p[2]  


def p_flow(p):
    'flow : flow INTEGER'
    p[1].append(p[2])
    p[0] = p[1]

def p_flow_single_lement(p):
    'flow : INTEGER'
    p[0] = [p[1]]

def p_error(p):
    print "Syntax error at line  " + str(lineno) + " : " + str(p)


def buildsfg(filename):
    """
    Build a SFG from logfile.
    The SFG will have an attribute app_name of which value is supposed to be the application that
    was analysed to produce the Blare log
    """
    global regexp_list
    global discard_filter
    global flow_graph
    global lineno
    lineno = 1
    parser = yacc.yacc(debug=False)
    flow_graph = nx.MultiDiGraph()
    logfile = open(filename)
    previous_line = ""
    for line in logfile:
        new_line = clean_entry(line, regexp_list, discard_filter)
        if (not (new_line is None)) and (new_line != previous_line) and (len(new_line) > 5) :
            parser.parse(new_line)
            previous_line = new_line
        lineno += 1
    cleansfg(flow_graph)
    return (flow_graph, filename)

(G, a) = buildsfg('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/simple_cond/log')
print "Les noeuds du graphe sont :"
print G.nodes()
print "Les arretes du graphe sont :"
print G.edges()
