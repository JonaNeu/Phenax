#!/usr/bin/env python

import pydot
import networkx as nx
import libsystemflowgraph as sys_fg
import copy

def build_dot_graph(flow_graph, cluster_system=False):
	dot_graph = pydot.Dot(graph_type='digraph')
	dot_subgraph = pydot.Cluster(graph_name='system_server')
	node_dic = {}
	for node in flow_graph.nodes():
		node_shape = ""
		if (node[0] == "process"):
		#if (nx.get_node_attributes(flow_graph, 'ctype')[node] == "process"):
			node_shape = "ellipse"	
		elif node[0] == "socket": #(nx.get_node_attributes(flow_graph, 'ctype')[node] == "socket") :
			node_shape = "hexagon"
		else :
			node_shape = "box"
		node_label = str(node[2]) + " -  " +  copy.copy(node[1]).replace(":", "/")
		#node_label = nx.get_node_attributes(flow_graph, 'cname')[node].replace(":", "/")
		dot_node = pydot.Node(node_label, shape=node_shape)	
		node_dic[node] = dot_node
		if (("system_server" in  node_label) and cluster_system):
			dot_subgraph.add_node(dot_node)
		else :
			dot_graph.add_node(dot_node)
	dot_graph.add_subgraph(dot_subgraph)
	for edge in flow_graph.edges(keys=True, data=True):
		dot_edge = pydot.Edge(node_dic[edge[0]], node_dic[edge[1]])
		edge_label = ""
		if (sys_fg.get_attr(edge).has_key('timtestamp')):
			s = len(sys_fg.get_attr(edge)['timestamp'])
			edge_label = (str(sys_fg.get_attr(edge)['flow']) + " - " + str(s) + " - " + str(sys_fg.get_attr(edge)['timestamp'][0]) + " - " + str(sys_fg.get_attr(edge)['timestamp'][s - 1]))
		else:
			edge_label = "*"
		dot_edge.obj_dict['attributes']['label'] = edge_label
		dot_graph.add_edge(dot_edge)
	return dot_graph

def save_dot_to_file(dot_graph, path):
	dot_graph.write(path, format='dot')
