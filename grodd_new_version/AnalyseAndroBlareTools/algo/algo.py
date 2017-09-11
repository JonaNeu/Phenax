#coding: utf8

# This file contains algorithms around the marguerite structure. Its definition, some side functions to generate/characterize it and some others to print or modify it.

# If other structures are defined, all algorithms should be implemented here to be then used as an API in other files (like the marguerite.py which use algo.py to generate a json file)

import os
import networkx as nx
import matplotlib.pyplot as plt

#Find the depth of the graph starting with a node "starting_node"
def graph_depth(graph,starting_node):
	depth=0
	for destination in F.nodes():
		for path in nx.all_simple_paths(graph, starting_node, destination):
			if(len(path)-1>depth):
				depth=len(path)-1
	return depth

#take a graph and returns the list of nodes where there is a marguerite (daisy)
#a marguerite is a node which is connected with several (more than 2) non-connected nodes
def marguerites(G):
    print 'Generating marguerites. This can take some minutes.'
    res = []
    #for each node we make a list of the connected nodes
    for (a,b,c) in G.nodes():
        add = True
        tails = []
        petals = []
        heart = (a,b,c)
        succ = successors(a,b,c,G)
        pred = predecessors(a,b,c,G)
        #/!\ WARNING
        #the function allows not to have several times the same node as a tail or a petal
        #do not suppress/comment it unless you change the use of remove() (only suppress the first found)
        succ = list_cleaner(succ)
        pred = list_cleaner(pred)
        #/!\ WARNING
        # a tail is wether only a predecessor of the current node or both predecessor and successor connected with another node
        for (d,e,f) in pred:
            if (d,e,f) not in succ:
                tails.append((d,e,f))
        for (d,e,f) in succ:
            if ((d,e,f) in pred) and is_connected(a,b,c,d,e,f,G):
                tails.append((d,e,f))
        # if not a tail, we can check if the rest is a list of petal
        for t in tails:
            if t in succ:
                succ.remove(t)
        for (d,e,f) in succ:
            if is_connected(a,b,c,d,e,f,G):
                add = False
                break
            else :
                petals.append((d,e,f))
        if add:
            res.append({'petals': petals, 'tails': tails, 'heart': heart})
    return res

#make a list of the successors
def successors(a,b,c,G):
    res = []
    for ((d,e,f),(i,j,k)) in G.edges():
        if f==c:
            res.append((i,j,k))
    return res

#make a list of the predecessors
def predecessors(a,b,c,G):
    res = []
    for ((d,e,f),(i,j,k)) in G.edges():
        if k==c:
            res.append((d,e,f))
    return res

def is_connected(a,b,c,d,e,f,G):
    res = False
    succ = successors(d,e,f,G)
    for (p,q,r) in succ:
        if r != c:
            res = True
            break
    return res

#get marguerite of a specific node
def get_marguerite(a,b,c,G):
    tails=[]
    petals=[]
    heart=(a,b,c)
    pred=predecessors(a,b,c,G)
    succ=successors(a,b,c,G)
    for (d,e,f) in pred:
        if (d,e,f) not in succ:
            tails.append((d,e,f))
    for (d,e,f) in succ:
        petals.append((d,e,f))
    return {'petals': petals, 'tails': tails, 'heart': heart}

#get a list of marguerite for a list of nodes
def get_marguerites(L,G):
    res = []
    for (a,b,c) in L:
        res.append(get_marguerite(a,b,c,G))
    return res

#clean a list of nodes by their PID so that there's only one occurence
def list_cleaner(L):
    for (a,b,c) in L:
        i=L.index((a,b,c))+1
        for (d,e,f) in L[i:]:
            if f==c:
                L.remove((d,e,f))
    return L

#returns a new graph without the marguerite m
def remove_marguerite(m,G):
    res=nx.MultiDiGraph(G)
    R=m['tails']
    R.extend(m['petals'])
    R.append(m['heart'])
    for (a,b,c) in R:
        res.remove_node((a,b,c))
    return res

# print the marguerite
def print_marguerite(M):
    print '\nThe shape of the marguerite is:'
    print 'heart : ', M['heart']
    print 'tails : ', M['tails']
    print 'petals : ', M['petals']

# print some information about the graph
def print_graph(G):
    print '\nPrinting the NetworkX graph:'
    print 'NODES:'
    print G.nodes()
    print "EDGES:"
    print G.edges()
    

# Function in order to test the API
def test():
    #[WORKED] Generate and print a NetworkX graph from a gpickle file
    G=nx.read_gpickle('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/simple_cond/log_simpleCond.tmp.gpickle')
    print_graph(G)

    # add a node (a,b,c) to the list N wether it already exist or not
    def verif_liste(N,a,b,c):
        for i,j,k in N:
            if k==c :
                return
        N.append((a,b,c))

    # retrieve the list cleaned from doubles nodes
    # the typical case seen is 'system_evr' or 'sytem_evr' printed instead of 'system_server'. This comes from kernel writings that bugs the log generator.
    N=[]
    for a,b,c in G.nodes():
        verif_liste(N,a,b,c)

    # same for the edges. These are modified depending on the new nodes list.
    A=[]
    for ((a,b,c),(d,e,f)) in G.edges():
        for i,j,k in N:
            if c==k:
                (a,b,c)=(i,j,k)
            if f==k:
                (d,e,f)=(i,j,k)
        A.append(((a,b,c),(d,e,f)))

    # Creation of a graph from those cleaned lists
    F=nx.MultiDiGraph()
    F.add_nodes_from(N)
    F.add_edges_from(A)

    # Creation of a graph in order to see a marguerite
    T=nx.MultiDiGraph()
    noeuds = [('foo','foo',1),('foo','foo',2),('foo','foo',3),('foo','foo',4),('foo','foo',5),('foo','foo',6)]
    arretes = [(('foo','foo',1),('foo','foo',2)),(('foo','foo',2),('foo','foo',3)),(('foo','foo',2),('foo','foo',4)),(('foo','foo',2),('foo','foo',5)),(('foo','foo',2),('foo','foo',6)),(('foo','foo',2),('foo','foo',6))]
    T.add_nodes_from(noeuds)
    T.add_edges_from(arretes)

    # Generation of a marguerite list and print it
    liste_marguerite = marguerites(F)
    print 'la liste des marguerites est :'
    print_marguerites(liste_marguerite)

    # Testing to remove a marguerite from a graph
    R=remove_marguerite(liste_marguerite[2], F)
    print_graph(T)
    print 'On retire une marguerite...'
    R=remove_marguerite(liste_marguerite[2], F)
    print_graph(R)

    """
    #Creation des labels
    #labels=nx.draw_networkx_labels(F,pos=nx.spring_layout(F))
    
    #Sauvegarde des graphes
    nx.draw_networkx(T)
    #print labels
    #nx.draw(G,pos=nx.spring_layout(G))
    plt.draw()
    plt.savefig('graphe.png',dpi=150)

    #Nettoyer le schéma
    plt.clf()

    nx.write_gpickle(F, '/home/tr4ckt3r/Documents/Projet3A/BlareLogs/simple_cond/log_cleaned.tmp.gpickle')
    nx.draw_networkx(F)
    #print labels
    #nx.draw(F,pos=nx.spring_layout(F))
    plt.draw()
    plt.savefig('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/simple_cond/graphe_cleaned.png',dpi=150)
    """

#test()
