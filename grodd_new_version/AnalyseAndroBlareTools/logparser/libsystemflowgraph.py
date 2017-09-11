import networkx as nx
import math
import sys
import string
import graphtodot as dot
import os.path

def load(filename):
    if ((filename is None) or (not os.path.isfile(filename))):
        print "Please provide a filename"
        return None
    else:
        res = nx.read_gpickle(filename)
        res.graph["filename"] = os.path.abspath(filename)
        return res 
            


# Reminder : In networkx point of view, nodes of the graph are 3-tuples which are made of a container type, a name and an id. They have "no attributes". Concerning edges they are 4-tuples (source, node, key, attributes). The third element permits to make a distinction between two parallel edges (edges connecting the same nodes) 

# Useful (or not) functions that return type, name and id of a container node without  bothering about their index in node
def get_type(node):
    return node[0]

def get_name(node):
    return node[1]

def get_id(node):
    return node[2]

# Useful (or not) functions that return source and destination of an edge
def get_src(edge):
    return edge[0]

def get_dst(edge):
    return edge[1]

# We assume an edge is always a 4-tuple which last member is the edge attributes
def get_attr(edge):
    return edge[3]

# Return the edges of the graph. A list of 4-tuple
def get_edges(flow_graph):
    return flow_graph.edges(data=True, keys=True)

def get_nodes(flow_graph):
    return flow_graph.nodes(data=True)

# Return outgoing edges of node in flow_graph
def get_out_edges(flow_graph, node):
    return flow_graph.out_edges([node], True, True)

def get_in_edges(flow_graph, node):
    """
    Return all in going edges of node in SFG flow_graph
    """
    return flow_graph.in_edges([node], True, True)

# Return the set of vertices from which information identified by info_id starts flowing at time t
def origins(flow_graph, info_id, t=0):
    final_res = []  
    for v1 in flow_graph.nodes():
#       print("Testing node " + str(v1) + "\n") 
        # Variable in which we store the first time info_id starts propagating from v1 at time t or later.
        first_flow_t = -1

        # Check if there is a flow of info_id from v1 starting at time t or later and find the first time it happens
        for out_edge in get_out_edges(flow_graph, v1) : #flow_graph.out_edges([v1], True, True):
            if (info_id in out_edge[3]['flow']):
                for tt in out_edge[3]['timestamp']:
                    if (tt >= t) :
                        if (not (first_flow_t == -1)):
                            first_flow_t = min(first_flow_t, tt)
                        else : 
                            first_flow_t = tt   
                    break
        if (first_flow_t == -1):
            # We did not find any flow involving info_id from v1 starting at t or later
#           print("No flow of" + str(info_id) + " " + str(v1))
            continue
        is_origin = True
        for in_edge in  get_in_edges(flow_graph, v1): #flow_graph.in_edges([v1], True, True):   
            if (not is_origin):
                break
            if (info_id in in_edge[3]['flow']):
                for tt in in_edge[3]['timestamp']:
                    if ((t <= tt) and (tt <= first_flow_t)):
                        # There is an incoming flow to v1 that happens after t and before first_flow_t. v1 is not an origin node of info_id at time t   
                        is_origin = False
                        break
        if (is_origin):
            final_res.append((v1, first_flow_t))    
    return final_res                    

# Extract from flow_graph a graph in which information identified by identifiers in id_set are only present 
def extract_flow_graph(flow_graph, id_set):
    res_graph = nx.MultiDiGraph()
    for edges in graph2.edges():
        a = 1 + 2
    return res_graph

# Compute neighbors/successors of a container that access to a piece of information identified by info_id starting after start_t
# By default start_t = 0 which means we want all successors of cont 
def successors(flow_graph, cont, info_id, start_t=0):
    res = {}
    for out_edge in flow_graph.out_edges([cont], True, True):
        if (info_id in out_edge[3]['flow']):
            for t in out_edge[3]['timestamp']:
                if (t > start_t):
                    if (res.has_key(out_edge[1])):
                        res[out_edge[1]] = math.min(res[out_edge[1]], t)
                    else:
                        res[out_edge[1]] = t
                    break   
    return res

# Compute predecessors of a node cont from which information identified by info_id flow to cont before time last_t
# By default last_t = -1 which means we want all predecessors of cont
def predecessors(flow_graph, cont, info_id, last_t=-1):
    res = {}                                   
    for in_edge in get_in_edges(flow_graph, cont): #flow_graph.in_edges([cont], True, True):
        if (info_id in in_edge[3]['flow']):  
            for t in reversed(in_edge[3]['timestamp']):
                if ((last_t == -1) or (t < last_t)): 
                    if (res.has_key(in_edge[0])):
                        res[in_edge[0]] = max(res[in_edge[0]], t)
                    else:      
                        res[in_edge[0]] = t
                    break
    return res

COMPLETE = 0
EDGE_ONCE = 1
NODE_ONCE = 2
# Compute how a piece of information identified by info_id may have spread from a container cont starting at a time start_t in a flow graph flow_graph
# p_type indicates the type of path we are looking for.
# p_type = COMPLETE means that we consider we reach the end of a path at a given node n only when there is no more incoming edges of n, which corresponds to flow involving info_id, which has timestamps later than start_t (for now this is the only option supported -- need to think about the usefulness of the two remaining option values) 
# p_type = EDGE_ONCE means that we consider we reach the end of a path when all outgoing edges from the current node are edges we already visited
# p_type = NODE_ONCE means that we consider we reach the end of a path when all successors of the current node are nodes we already visited
# visited contains the elements of the path that have been visited for the current path we are building. It is useless for p_type == COMPLETE but may be useful for EDGE_ONCE and NODE_ONCE
# Return value is a tree which root is cont 
def paths_from(flow_graph, cont, info_id, start_t = 0, p_type=COMPLETE, visited=[]):
    #print("paths_from " + str(cont) + " after time: " + str(start_t))
    res = []
    succ_dict = successors(flow_graph, cont, info_id, start_t)
    for succ_node, t in succ_dict.iteritems():  
        tmp_res = paths_from(flow_graph, succ_node, info_id, t, p_type, visited)
        for paths in tmp_res:
            head_l = [(cont, start_t)]
            head_l.extend(tmp_res)
    #       print("Head-l : " + str(head_l))
            res.append(head_l)
            #res.append(([(cont, start_t)]).extend(tmp_res))
    #       print("Res intermediaire : " + str(res))
    if (res == []):
    #   print "Pas de successeurs"
        res.append([(cont, start_t)])
    #print("Res : " + str(res))
    return res
    

# Compute possible paths that a piece of information have followed to a container cont in a flow graph flow_graph
def paths_to(flow_graph, cont, info_id, last_t, p_type=COMPLETE, visited=[]):
    res = []
    pred_dict = predecessors(flow_graph, cont, info_id, last_t)
    for pred_key in pred_dict.keys():
        tmp_res = paths_to(flow_graph, pred_key, pred_dict[pred_key], p_type, visited)
        for paths in tmp_res:
            res.append([(cont, last_t)].join(tmp_res))
    if (res == []):
        res.append([])
    return res

# Computes maximum identifier set that each container accessed in a SFG 
def gen_policy_from(sfg):
    policies = {}   
    for e in get_edges(sfg):
        if policies.has_key(get_dst(e)):
            for info_id in e[3]['flow']:
                if not (info_id in policies[get_dst(e)]):  
                    policies[get_dst(e)].append(info_id)
        else :      
            policies[get_dst(e)] = list(e[3]['flow'])
    return policies

# Print policies
def print_policy(policies, out_name=None):
    empty_dic = {}
    out = None
    if out_name == None:
        out = sys.stdout
    else:
        out = open(out_name, 'w')
    for (node, tag) in policies.items():
        if (node[0] == 'file'):
            tag_str = str(sorted(tag)).replace("[", "{").replace("]", "}")
            out.write("setpolicy " + get_name(node) + " " + tag_str + "\n")

    for (node, tag) in policies.items():
        if (node[0] == 'process'):
            tag_str = str(sorted(tag)).replace("[", "{").replace("]", "}")
            out.write("setxpolicy " + get_name(node) + " " + tag_str + "\n")
    if sys.stdout != out:
        out.close()

def sim_nodes(n1, n2, name1, name2):
    return (n1[0] == n2[0]) and ((n1[1] == n2[1]) or ((n1[0] == "file") and (n1[1].replace(name1, name2, 1) == n2[1])))

def intersection(sfg1, sfg2, sim_list):
    """
    Return the intersection of the system flow graphs sfg1 and sfg2.
    sim_list if a list of string pairs (str1, str2). Eeach pair means that str1 substrings present in sfg1 filenames corresponds to str2 sfg2 filenames 
    """
    copy = set(sfg2.edges())
    res = nx.MultiDiGraph()
    for e1 in sfg1.edges():
        toremove = None
        for e2 in copy:
            if sim_nodes(e1[0], e2[0], sim_list[0][0], sim_list[0][1]) and sim_nodes(e1[1], e2[1], sim_list[0][0], sim_list[0][1]):
                res.add_edge(e1[0], e1[1])
                toremove = e2
                break
        if not (toremove is None):
            copy.remove(toremove)
    return res

def mult_intersection(sfg_list, sim_name_list):
    """
    Return the intersection of graphs contained in sfg_list. sim_name_list
    contains list of similar strings. Each string at index i corresponds to
    the graph at index i of sfg_list
    """
    res = sfg_list[0]
    index = 1
    while index < len(sfg_list): 
        tmp_res = intersection(res, sfg_list[index], [(sim_name_list[0], sim_name_list[index])])
        res = tmp_res
        index += 1
    return res

def mult_minus(sfg_list, sim_name_list):
    """
    Return the complement of the first element of sfg_list with the union of the rest
    of the elements of the list
    """
    res = sfg_list[0]
    index = 1
    while index < len(sfg_list):
        tmp_res = minus(res, sfg_list[index], [(sim_name_list[0], sim_name_list[index])])
        res = tmp_res
        index += 1
    return res


#given sfg1 and sfg2 computes sfg1- sfg2 )
def minus(sfg1, sfg2, sim_list):
    res= nx.MultiDiGraph()
    copy = set(sfg2.edges())
    for e1 in sfg1.edges() :
        similar  = None
        for e2 in copy:
            if sim_nodes(e1[0], e2[0], sim_list[0][0], sim_list[0][1]) and sim_nodes(e1[1], e2[1], sim_list[0][0], sim_list[0][1]):
                similar = e2
                break
        if not (similar is None) :
            copy.remove(similar)
        else :
            res.add_edge(e1[0], e1[1])
    return res

def intersection_minus(sfg1, sfg2, sim_list):
    copy = set(sfg2.edges())
    inter = nx.MultiDiGraph()
    minus = nx.MultiDiGraph()
    for e1 in sfg1.edges():
        toremove = None
        exists_similar= False
        for e2 in copy:
            if sim_nodes(e1[0], e2[0], sim_list[0][0], sim_list[0][1]) and sim_nodes(e1[1], e2[1], sim_list[0][0], sim_list[0][1]):
                exists_similar = True
                toremove = e2
        
        if exists_similar and (not (toremove is None)):
            copy.remove(toremove)
            inter.add_edge(e1[0], e1[1])
        else:
            minus.add_edge(e1[0], e1[1])
    return (inter,minus)

def contains_double_nodes (sfg):
    res = False
    for n in sfg.nodes() :
        if sfg.nodes().count(n)>1 :
            res=True
            break
    return res

def contains_double_edges (sfg):
    res = False
    for n in sfg.edges() :
        if sfg.edges().count(n)>1 :
            res=True
            break
    return res


def is_included (sfg1,sfg2,sim_list):
    """
    Test if sfg1 is included in sfg2
    """
    inter=intersection (sfg1,sfg2,sim_list)
    return len(inter.edges())== len(sfg1.edges())

def is_empty (sfg):
    return (len(sfg.edges())==0)

def anonymize_graphs(graphlist,sim_list):
    """
    Replace strings in sim_list that are part of filenames in each sfg of graphlist with 'blare-anonym'.
    Each string in sim_list at index i represents the string to be replaced in the graph at index i in graphlist. 
    """
    anonym_name = "blare-anonym"
    lres = []
    for index in range(len(graphlist)):
        g = nx.MultiDiGraph()
        for e in graphlist[index].edges():
            n0 = None
            if e[0][0] == "file" :
                n0 = ("file", str(e[0][1]).replace(sim_list[index], anonym_name, 1), e[0][2])
            else :
                n0 = e[0]

            n1 = None
            if e[1][0] == "file" :
                n1 = ("file", str(e[1][1]).replace(sim_list[index], anonym_name, 1), e[1][2])
            else :
                n1 = e[1]
                
            g.add_edge(n0, n1)
        lres.append(g)
    return lres

compteur_is_diff =0

def is_equal(sfg1,sfg2):
    """
    Test if two SFGs are equal. Return True if all edges of sfg1 are present
    in sfg2 and all edges of sfg2 are present in sfg1
    """
    return (len(minus(sfg1,sfg2,[("","")]).edges())==0) and (len(minus(sfg2,sfg1,[("","")]).edges())==0)

def is_equal_old (sfg1, sfg2) :
    edges2_copy=[element for element in sfg2.edges()]
    for a in sfg1.edges() :
        try:
            edges2_copy.remove(a)
        except ValueError:
            return False 
    return (len(edges2_copy) ==0 )

def exists_edges (f,sfg):
    for e in sfg.edges():
        if f(e) :
            return True
    return False


    
def verif_criteria (sfg,function_list) : 
    """
    Test if a sfg verifies a list of criteria specified in a list of boolean functions
    """
    for f in function_list :
        if not f(sfg) :
            return False
    return True

def gen_sign_list_from_sfg_list (lgraph,white_list,comp,function_list):
    """
    Compute the intersection of each possible couple of SFGs from lgraph.
    The return value is a dictionary which keys are SFGs that resulted from the intersecion.
    The value corresponding to each key is a couple. The first element of the couple is
    a couple of SFGs which intersection produce the key. The second element of the couple is
    a list of graphs present in lgraph that contains the key. 
    :param lgraph: a list of SFGs. Each element of lgraph are supposed to be anonymzed
    :type lgraph: list
    :param white_list: a list of SFGs of benign application
    :type white_list: list
    :param comp: what?
    :type comp: int
    :param function_list: list of functions that will serve to check either if the result of an intersection
        can be either considered as a signature or refined to get a signature   
    """
    lres=  {}
    sim_list=["" for element in lgraph]
    not_sign_list = []
    for i0 in range(len(lgraph)):
        gi0=lgraph[i0]
        is_sign_gi0=True
        for i1 in range(i0 + 1, len(lgraph)):
            #if i1 : #not (i0==i1) :
            gi1=lgraph[i1]
            white_list_copy=[element for element in white_list]
            sim_white_list_copy=["" for element in white_list]
            inter =intersection(gi0,gi1,[("","")])
            white_list_copy.insert(0,inter)
            sim_white_list_copy.insert(0,sim_list[i1])
            # Remove from inter all edges that can be present in graphs of benign apps
            inter=mult_minus(white_list_copy,sim_white_list_copy)
            if verif_criteria (inter,function_list) : # on verifiait que inter non vide
                not_sign_list.insert(0, gi0)
                not_sign_list.insert(0, gi1)
                is_sign_gi0= False
                inserted= None
                for k in lres.keys():
                    if is_equal (k, inter) :
                        inserted=k
                        break
                if not (inserted is None ):
                    lres.get(inserted)[0].insert(-1, (gi0,gi1))
                else :
                    ltemp=[gi0, gi1]
                    compteur=0
                    for i3 in range(len(lgraph)):
                        if not (i0 == i3) and not (i1 == i3) :
                            if is_included(inter,lgraph[i3],[(sim_list[i1],sim_list[i3])]):
                                ltemp.insert(-1,lgraph[i3])
                    lres[inter]=([(gi0,gi1)], ltemp)
        if (not (gi0 in not_sign_list)) and is_sign_gi0 and comp >= 1 :
            lres[gi0]=([(gi0,gi0)],[gi0])   
    return lres

def equal_sfg_list (l1, l2):
    if len(l1) != len(l2) :
        return False
    else :
        l2copy= [element for element in l2]
        for g1 in l1:
            to_remove = None
            for g2 in l2copy :
                if is_equal (g1,g2) :
                    to_remove=g2
                    break
            if not(to_remove is None) :
                l2copy.remove(to_remove)
        return l2copy == []

def compute_sign(lgraph,white_list,criteria):
    """
    Returns a list of signature proposition for the SFGs in lgraph. The
    signature is a dictionnary which maps each key (a SFG) with a list
    of SFGs from lgraph that contain the key
    :param lgraph: list of SFGs that are meant to been classified
    :param white_list: list of SFGs of benign applications 
    :type white_list: list of SFGs of benign applciations
    :type lgraph: list of SFG of malicious applications
    """
    
    old_signs = {}
    for g in lgraph:
        old_signs[g] = [g]
    comp = -1
    
    #return compute_sign_aux(old_sign,white_list,0,criteria)
    while True :
        comp += 1
        tmp_signs = gen_sign_list_from_sfg_list(old_signs.keys(), white_list, comp, criteria)
        #print("Longeur old_sign: " + str(len(tmp_signs)) + "\n")
        if len(tmp_signs.keys()) == 0 :
            return old_signs
            
        new_signs = {}
        for key, value in tmp_signs.items():
            tmp_list = []
            for old_k in value[1] :
                for g in old_signs[old_k]:
                    if not (g in tmp_list) :
                        tmp_list.insert(0, g)
            new_signs[key] = tmp_list
        if (comp >= 1) and equal_sfg_list(old_signs.keys(), new_signs.keys()) :
            return new_signs
        old_signs = new_signs
    
#def gen_sign_list_from_sfg_list_AVEC3GRAPH (lgraph,white_list):
#   """
#   les arguments doivent etre anonymises
#   false commentary 
#   compute a dictionnary having sfg as key and where values are pair (l1,l2) l1=list of pair of index and l2= list of sfg  containing the  key
#   lgraph is a list of graph where the signature are computed
#   sim list is alist of name that have to be considered as similar for lgraph 
#   white_list is a list of benign sfg
#   sim_white_list is alist of name that have to be considered as similar for white_list
#   """
#   lres=  {}
#   sim_list=["" for element in lgraph]
#   for i0 in range(len(lgraph)):
#       gi0=lgraph[i0]
#       for i1 in range(len(lgraph)):
#           if not(i0==i1) :
#               gi1=lgraph[i1]
#               for i2 in range(len(lgraph)):
#                   if not(i2==i0) and not(i2==i1):
#                       gi2=lgraph[i2]
#                       white_list_copy=[element for element in white_list]
#                       sim_white_list_copy=["" for element in white_list]
#                       inter =intersection(intersection(gi0,gi1,[("","")]),gi2,[("","")])
#                       white_list_copy.insert(0,inter)
#                       sim_white_list_copy.insert(0,sim_list[i1] )
#                       inter=mult_minus(white_list_copy,sim_white_list_copy)
#                       if not(is_empty(inter)) :
#                           print("intersection between sfg "+str(i0)+" and sfg "+ str(i1)+" and sfg "+ str(i2))
#                           inserted= None
#                           for k in lres.keys():
#                               if is_equal (k, inter) :
#                                   inserted=k
#                                   break
#                       
#
#                           if not (inserted is None ):
#                               lres.get(inserted)[0].insert(-1, (i0,i1, i2))
#                           else : 
#                               ltemp=[]
#                               for i3 in range(len(lgraph)):
#                                   if not(i0==i3) and not(i1==i3) and not(i2==i3) :
#                                       if is_included(inter,lgraph[i3],[(sim_list[i1],sim_list[i3])]):
#                                           ltemp.insert(-1,lgraph[i3])
#
#                               lres[inter]=([(i0,i1,i2)],ltemp)
#   return lres
                    


    
#def gen_sign_list_from_sfg_list_SAUV (lgraph,white_list):
#   """
#   les arguments doivent etre anonymises
#   false commentary 
#   compute a dictionnary having sfg as key and where values are pair (l1,l2) l1=list of pair of index and l2= list of sfg  containing the  key
#   lgraph is a list of graph where the signature are computed
#   sim list is alist of name that have to be considered as similar for lgraph 
#   white_list is a list of benign sfg
#   sim_white_list is alist of name that have to be considered as similar for white_list
#   """
#   lres=  {}
#   sim_list=["" for element in lgraph]
#   for i1 in range(len(lgraph)):
#       gi1=lgraph[i1]
#       for i2 in range(len(lgraph)):
#           if not(i1==i2) :
#               gi2=lgraph[i2]
#               white_list_copy=[element for element in white_list]
#               sim_white_list_copy=["" for element in white_list]
#               inter =intersection(gi1,gi2,[("","")])
#               white_list_copy.insert(0,inter)
#               sim_white_list_copy.insert(0,sim_list[i1] )
#               inter=mult_minus(white_list_copy,sim_white_list_copy)
#               if not(is_empty(inter)) :
#                   print("intersection between sfg "+str(i1)+" and sfg "+ str(i2))
#                   inserted= None
#                   
#                   for k in lres.keys():
#                       if is_equal (k, inter) :
#                           inserted=k
#                           break
#                       
#
#                   if not (inserted is None ):
#                       lres.get(intersted)[0].insert(-1, (i1, i2))
#                   else : 
#                       ltemp=[]
#                       for i3 in range(len(lgraph)):
#                           if not(i1==i3) and not(i2==i3) :
#                               if is_included(inter,lgraph[i3],[(sim_list[i1],sim_list[i3])]):
#                                   ltemp.insert(-1,lgraph[i3])
#
#                       lres[inter]=([(i1,i2)],ltemp)
#   return lres
                    

def print_sign(sign, pref=""):
    """
    Export the signatures into files prefxed with the param pref.
    By default, pref is an empty string
    """
    print("we get "+str(len(sign.keys()))+" different signatures saved into files ")
    i=0
    for k in sign.keys():
        print("the signature saved into sign_"+str(i)+".dot")
        dot.save_dot_to_file(dot.build_dot_graph(k), ("sign_"+str(i)+".dot"))
        print("appears in "+(str(len(sign.get(k))))+" differents graphs.")
        i=i+1
    

def filter_edges (f,sfg):
    sfg_res=nx.MultiDiGraph()
    for e in sfg.edges():
        if f(e) :
            sfg_res.add_edge(e[0], e[1])
    return sfg_res


def edges_name_contains (e,s):
    return (e[0][1].find(s) != -1 or e[1][1].find(s) != -1  )

def equal_nodes(n0,n1):
    return n0[0] == n1[0] and n0[1] == n1[1] 

def is_an_edge_of (e,sfg):
    for e1 in sfg.edges():
        if equal_nodes(e[0],e1[0]) and equal_nodes(e[0],e1[0]):
            return True
    return False


def number_of_common_edges(sfg1,sfg2):
    res= 0
    for e in sfg1.edges():
        if is_an_edge_of(e, sfg2):
            res+=1
    return res

    
#def stats_from_sign(sign,lgraph):
#   sfg_indice=0
#   res={}
#   for k in sign.keys():
#       print(" \n ***  \n Analyse de la signature: "+str(sfg_indice)+". \n ***  \n Cette signature compte "+str(len(k.edges()))+" arcs.")
#       graph_indice =0
#       complete=0
#       maxcommon =0
#       similar=0
#       res[k]=[]
#       for g in lgraph :
#           c=number_of_common_edges(k,g)
#           if c==len(k.edges()):
#               complete=complete+1
#               res.get(k).insert(-1,graph_indice)
#           if c >0 and c<len(k.edges()) and c > maxcommon:
#               maxcommon=c
#           if c >0 and c<len(k.edges()):
#               similar=similar+1
#               
#           print("on retrouve  "+str(c) +" arcs  sur "+str(len(k.edges()))+" de cette signature dans  le graph "+str(graph_indice))
#           graph_indice+=1
#       print(" \n"+str(len(lgraph)-similar-complete)+" graphs sur "+str(len(lgraph))+ " analyses ("+str(((len(lgraph)-similar-complete)*100.) /len(lgraph)) + "%) des lgraph analyses n'ont pas d'arcs en communs avec cette signature")
#       
#       print(str(similar)+" graphs sur "+str(len(lgraph))+ " analyses ("+str((similar*100.) /len(lgraph)) + "%) des lgraph analyses presentent entre 1 et "+str(maxcommon)+" des arcs de cette signature (sur "+str(len(k.edges()))+ "), c'est a dire font apparaitre "+str(maxcommon*100. / len(k.edges()))+"% de cette signature")
#
#       print(str(complete)+" graphs sur "+str(len(lgraph))+ " analyses,  soit "+str((complete*100.) /len(lgraph)) + "% des lgraph analyses presentent la totalite de la signature")
#       sfg_indice+=1
#   
#   return res

def construct_signature_table (sfglist):
    res={}
    print(len(sfglist))
    for g in sfglist:
        for e in g.edges() :
            if ((e[0][0],e[0][1]),(e[1][0],e[1][1])) in res.keys() :
                res.get(((e[0][0],e[0][1]),(e[1][0],e[1][1]))).extend([g])
            else:       
                res[((e[0][0],e[0][1]),(e[1][0],e[1][1]))]=[g]
            #print(str(res.get(((e[0][0],e[0][1]),(e[1][0],e[1][1])))))
    return res

def empty_automaton (sfg_list,seuil_list):
    i=0
    res ={}
    for g in sfg_list:
        print("seuil positionne =" +str(seuil_list[i]))
        res[g]=[0,seuil_list[i]]
        i+=1
    return res
        
# un automate est un dictionnaire dont les cles sont des sfg et les valeurs des [number_of_observed_event,seuil]
def progress (sfg_list, automaton):
    """
    For each SFG in sfg_list increase the corresponding observed events in automaton.
    If the threshold of an SFG have been reached a warning i raised.
    :param sfg_list: list of SFG
    :type sfg_list: list
    :param automaton: is a dictionary which keys are SFGs and which values are a tuple
    (number of observed events, threshold)
    :type automaton: dictionary
    """
    changed_l = []
    for g in sfg_list:
        #print(str(g))
        #print(automaton.get(g))
        automaton.get(g)[0] += 1
        #print(automaton.get(g))
        #l =automaton.get(g)
        #if l[0] >= l[1] :
        #   print(" WARNING !! \n This application presents "+str(l[0])+" i.e. more than "+str(l[1]*100./len(g.edges())) + " of similarity with signature " + g.name )
                  
def detection_one_step (elight, automaton, signature_table):
    """
    Increase number of events observed for each SFG that contain elight.
    elight is a SFG's edge. Its source and destination nodes are only
    made of a type and a name.
    automaton is a dictionary which keys are SFGs and which values are a tuple
        (number of observed events, threshold). The number of observed events are
    increased for each SFGs that contains an edge similar to elight. An edge is
    similar to elight if its origin and desination nodes share the same type and name 
    Return the list of graphs that matched elight
    """
    res = [] 
    if elight in signature_table.keys() :
        progress(signature_table.get(elight), automaton) 
        res = signature_table.get(elight)
        signature_table.pop(elight)
    return res

