#!/usr/bin/env python

import re
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
import os


# Load the signatures
sig_list = []
for dirname, dirnames, filenames in os.walk("res/graphs/signatures"):
    for f_name in filenames:
        sig_list.insert(0, str(os.path.join(dirname, f_name)))

signatures = []
for f_name in sig_list : 
    signatures.insert(0, lsfg.load(f_name))

# ajouter une etape pour "regarder" la base de signature

signature_table = None #lsfg.construct_signature_table(signatures)

automaton = None #lsfg.empty_automaton(signatures, [len(g.edges()) * 50. / 100 for g in signatures])

# Define a list of couple (pattern, substitute) that can serve to format correctly a log entry 
regexp_list = [("> itag\[(-*[0-9 ]*)\]", "> {\\1}"), ("}select.*$", "}"), ("> \(null\)", "> {0}"), ("}failed.*$", "}"), ("}.+$", "}"), #("^.* > file /dev/cpuctl/tasks .*$", ""),
        ("re-initialized>", "re-initialized"), ("(process .*)\]", "\\1"), ("([^ >\\n\\t])\[", "\\1"), ("'", ""), (" #", "#"), ("Binder Thread", "BinderThread"), ("> process ([0-9])", "> process a\\1"), ("\] process ([0-9])", "\] process a\\1")]

# List of regexp that will serve to discard unwanted log entries
discard_filter = ["> file /proc/.*/oom_adj", "> {}$", "> file /sys/power/wake_", "/dev/cpuctl/bg_non_interactive/tasks", "\[BLARE\]", "^.* > file /dev/cpuctl/tasks .*$"]

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
    that share the same PID are the same container even if their name differ.We
    assume that files that are located in the same partition and share the same
    inode are the same containers too even if their name differ
    """
    partition_list = ["/data", "/system", "/mnt/sdcard", "/sdcard"] 
    if (cont1 == cont2):
        return True
    if (cont1[0] == cont2[0]):
        if (cont1[0] == 'process'):
            return cont1[2] == cont2[2]
        elif (cont1[0] == 'file') and (cont1[2] == cont2[2]):
            for prefix in partition_list:
                if cont1[1].startswith(prefix) and cont2[1].startswith(prefix):
                    return True
        elif  (cont1[0] == 'socket') :
            return cont1[1] == cont2[1]
    return False

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

to_be_anonym = ""

def p_alert(p):
    ''' alert : level '[' TIMESTAMP ']' '[' STRING ']' container '>' container '>' '{' flow '}' '''
    global to_be_anonym
    if (to_be_anonym == "") and (p[8][0] == "file") and (p[10][0] == "process") and (p[8][1].startswith("/data/app/")) : 
        f_name = p[8][1].split("/")[3]
        if f_name.find(p[10][1]):
            to_be_anonym = f_name.replace("-1.apk", "").replace(".apk", "")
            print "Anonym : " + to_be_anonym
    res = None
    if (to_be_anonym == "") : 
        res = lsfg.detection_one_step(((p[8][0], p[8][1]), (p[10][0], p[10][1])), automaton, signature_table)
    else : 
        res = lsfg.detection_one_step(((p[8][0], p[8][1].replace(to_be_anonym, "blare-anonym")), (p[10][0], p[10][1])), automaton, signature_table)
    if not ((res == []) or (res == None)) :
        for g in res : 
            l = automaton.get(g)
            if (l[0] >= l[1]) : 
                print "Warning : " + str(l[0]) + "/" + str(len(lsfg.get_edges(g))) + " similarities detected with " + g.name 

def p_level(p):
    ''' level : '<' INTEGER '>' '''
    p[0] = p[2]  

def p_container(p):
    'container : STRING container_name INTEGER' 
    global args
    cont_name = p[2]
    if (args.thread_node == False):
        cont_name = p[2].split(":", 1)[0]   
        if not (args.a is None):
            for sub in args.a :
                cont_name = cont_name.replace(sub, "blare-anonym")
    new_node = (p[1], cont_name, p[3])
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

def print_reports(l, save) :
    """
    Print reports listed in l to the standard output
    """
    f = None
    if save :
        f = open("report.txt", "w")
    for report in l:
        tmp = ""
        tmp += "Log file : " + str(report["filename"]) + "\n"
        tmp += "Analysis duration : " + str(report["duration"]) + "\n"
        tmp += "Log size : " + str(report["lineno"]) + " lines" + "\n"
        tmp += "Detection result :\n"
        sim_total = 0
        for k, v in report["detection"].items() : 
            sim_total += v[0]
            tmp += (k.name + " " + str(v[0]) + "/" + str(len(lsfg.get_edges(k))) + " similarities\n")
        tmp += "Total of found similarities : " + str(sim_total) + "\n"
        if f is None : 
            print tmp
        else : 
            f.write(tmp)
    if not (f is None) : 
        f.flush()
        f.close()

def print_csv_report(l, fname):
    f = open(fname, "w")
    report = l[0]
    f.write("Filename, Analysis duration, Size")
    sig_l = []
    for k, v in report["detection"].items() :
        f.write("," + k.name)
        sig_l.insert(-1, k)
    f.write("\n")
    for report in l :
        tmp = ""
        tmp += str(report["filename"]) + ","
        tmp += str(report["duration"]) + ","
        tmp += str(report["lineno"])
        for g in sig_l : 
            tmp += "," + str(report["detection"][g][0])
        tmp += "\n"
        f.write(tmp)
    f.flush()
    f.close()

# Parser for program args
argparser = argparse.ArgumentParser(description="Process blare log output to build graphs", usage="logconverter-nx.py -i input [--cluster_system], [-a <NAME1> <NAME2>")
argparser.add_argument('-i', help='Specify the input file to be parsed', action='store', required=False, default=False, dest='input')
argparser.add_argument('--cluster_system', help='Cluster threads running in system_server process', action='store_true', required=False, default=False)
argparser.add_argument('--thread_node', help='Specify if threads of the same process should be represented by different nodes or not', action='store_true', required=False, default=False)
argparser.add_argument('--id', help='Specify an information identifier. The output graph will describe how the information flow', action='store', required=False, default=False, dest='info_id', type=int)
argparser.add_argument('-a', help="Specify a list of strings in containers'name in Blare log that should be considered as equal to blare-anonym in containers'name of graphs in the database", action='store', required=False, default=None, nargs='+')
argparser.add_argument('--i_dir', help="A directory from which input files should be read", action='store', required=False, default=False, dest="i_dir", nargs='+')
argparser.add_argument('-s', help="Save the result of the analysis / detection to a file report", action='store_true', required=False)
argparser.add_argument('-o', help="Specify where to store the report. If the filename ends with .csv, the report will be stored in a CSV format", action="store", default=None, dest="o", required=False)
args = argparser.parse_args()


# Build the log parser
#parser = yacc.yacc()
#start_t = time.clock()

lineno = 1
file_list = []
logfile = None
if (args.input == False) and (args.i_dir == False) :
    file_list.insert(0, "stdin")
elif not (args.input == False) :
    file_list.insert(0, args.input)
elif not (args.i_dir == False) :
    for dirname in args.i_dir :
        for root, d_names, f_names in  os.walk(dirname) : 
            for f_name in f_names :
                if f_name.endswith("log.txt") :  
                    file_list.insert(0, str(os.path.join(root, f_name)))
else : 
    print "Input error" 
    quit()
    
report_list = []
for f_name in file_list :
    print "Starting analysis of " + f_name + " for detection"
    cur_report = {}
    cur_report["filename"] = f_name
    signature_table = lsfg.construct_signature_table(signatures)
    automaton = lsfg.empty_automaton(signatures, [len(g.edges()) * 20. / 100 for g in signatures])
    lineno = 1
    to_be_anonym = ""
    parser = yacc.yacc()
    start_t = time.clock()
    if (f_name == "stdin") :
        logfile = sys.stdin
    else :
        logfile = open(f_name)
    previous_line = ""
    for line in logfile :
            new_line = clean_entry(line, regexp_list, discard_filter)
            if (not (new_line is None)) and (new_line != previous_line) and (len(new_line) > 5) :
                    parser.parse(new_line)
                    previous_line = new_line
            lineno += 1
    cur_report["detection"] = automaton
    cur_report["duration"] = time.clock() - start_t
    cur_report["lineno"] = lineno
    report_list.insert(0, cur_report)

if not (args.o is None) :
    print_csv_report(report_list, args.o)
else :
    print_reports(report_list, args.s) 
