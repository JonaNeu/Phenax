#coding: utf8

#This programm goal is to use a log directory and generate gpickles, graphs, jsons. In other words it transforms log file in the wanted format

#We mixed the use with algo.py in order to add properties to each graph so that they can be added in json files for further processing

#mainly for file and directory usage
import os
import glob

#for graph use
import networkx as nx
import matplotlib.pyplot as plt

#to use algo.py
import algo

#to serialize
import json
from networkx.readwrite import json_graph

#returns a list of the gpickle files in the named directory
def get_gpickle(directory):
    return glob.glob(directory+'/*.gpickle')

#returns a list of the log files in the named directory
def get_log(directory):
    return glob.glob(directory+'/*.log')

#returns a list of the json files in the named directory
def get_json(directory):
    return glob.glob(directory+'/*_graph.json')

#create a gpickle file associated to each log of the directory
#NOTE: this operation can be long for a well furnished directory
def log_to_gpickle(directory):
    logs = get_log(directory)
    for l in logs:
        os.system('./logToGpickle.sh '+l)

#return a graph with serialized nodes and edges
def serialize_graph(graph):
    s_graph = nx.MultiDiGraph()
    s_nodes = []
    s_edges = []
    for n in graph.nodes():
        s_nodes.append(json.dumps(n))
    for ((a,b,c),(d,e,f)) in graph.edges():
        s_edges.append((json.dumps((a,b,c)),json.dumps((d,e,f))))
    s_graph.add_nodes_from(s_nodes)
    s_graph.add_edges_from(s_edges)
    return s_graph

#take a serialized graph and return the real one
def deserialize_graph(s_graph):
    graph = nx.MultiDiGraph()
    nodes = []
    edges = []
    for n in s_graph.nodes():
        nodes.append(tuple(json.loads(n)))
    for (j,k) in s_graph.edges():
        edges.append((tuple(json.loads(j)),tuple(json.loads(k))))
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return graph

#returns a list of dictionnaries containing each a graph, his name and directory
def gpickle_to_graph(directory):
    graph_list = []
    logs = get_gpickle(directory)
    for l in logs:
        ls = l.split(directory)
        name = ls[1].split('.tmp.gpickle')
        graph = nx.MultiDiGraph()
        graph = nx.read_gpickle(l)
        graph_list.append({'graph': graph, 'directory': directory, 'name': name[0]})
    return graph_list

#draw a figure with a graph, saves it and clean the figure
def graph_to_image(graph_list):
    for g in graph_list:
        nx.draw_networkx(g['graph'])
        plt.draw()
        name = g['directory'] + g['name'] + '.png'
        plt.savefig(name,dpi=150)
        plt.clf()

#serialize a list of graphs in a json file for each graph
def graph_to_json(graph_list):
    for g in graph_list:
        graph = serialize_graph(g['graph'])
        graph = json_graph.node_link_data(graph)
        graph = json.dumps(graph)
        #marguerites = serialize_marguerites(g['marguerites'])
        #marguerites = json.dumps(marguerites)
        data = {}
        data['graph'] = graph
        data['directory'] = g['directory']
        data['name'] = g['name']
        #data['marguerites'] = marguerites
        filename = g['directory'] + g['name'] + '_graph.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

#deserialize all json files from a directory and return a graph_list
def json_to_graph(directory):
    graph_list = []
    jsons = get_json(directory)
    for filename in jsons:
        with open(filename, 'r') as f:
            data = json.load(f)
            graph = json.loads(data['graph'])
            graph = json_graph.node_link_graph(graph)
            graph = deserialize_graph(graph)
            #marguerites = json.loads(data['marguerites'])
            #marguerites = deserialize_marguerites(marguerites)
            directory = data['directory']
            name = data['name']
            #graph_list.append({'graph': graph, 'directory': directory, 'name': name, 'marguerites': marguerites})
            graph_list.append({'graph': graph, 'directory': directory, 'name': name})
    return graph_list

def print_graph_list(graph_list):
    for g in graph_list:
        print '\nPRINTING GRAPH: '
        print 'DIRECTORY: ', g['directory']
        print 'NAME: ', g['name']
        print 'GRAPH NODES: ', g['graph'].nodes()
        print 'GRAPH EDGES: ', g['graph'].edges()

#function only to test the others, each test separated by a blanc line
#can be used to see a typical use of each function
def test():
    #[WORKED] just in order the function test doesn't generate an IndentationError
    print 'test function'

    #[WORKED]
    #l = get_log('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #g = get_gpickle('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #print 'list of logs (',len(l),'):\n',l
    #print 'list of gpickles (',len(g),'):\n',g

    #[WORKED]
    #log_to_gpickle('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')

    #[WORKED]
    #graph_list, directory = gpickle_to_graph('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #graph_to_image(graph_list, directory)

    #[WORKED]
    #graph_list = gpickle_to_graph('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/simple_cond/')
    #graph_to_json(graph_list)

    #[WORKED]
    #graph_list = json_to_graph('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #print_graph_list(graph_list)

#test()
