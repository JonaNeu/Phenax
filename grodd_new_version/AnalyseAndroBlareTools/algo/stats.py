#coding: utf8

import os
import glob
import json
import algo
import logsConverter as lc
import marguerites as m
import matplotlib.pyplot as plt

############################################
# PART RELATED TO GET/SHOW CHARACTERISTICS #
############################################
#returns a list of the json files in the named directory
def get_json(directory):
    return glob.glob(directory+'stats/min_marg.json')

# verify if the directory stat is created
def verif_directory(directory):
    if os.path.isdir(directory+'stats') == False:
        os.system('mkdir '+directory+'stats')

# return a list of {number of nodes, name} from a directory with _graph.json files
def nodes_number(directory):
    number_list = []
    graph_list = lc.json_to_graph('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    for g in graph_list:
        number_list.append({'number': len(g['graph'].nodes()), 'name': g['name']})
    return number_list

# return a list of {number of edges, name} from a directory with _graph.json files
def edges_number(directory):
    number_list = []
    graph_list = lc.json_to_graph('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    for g in graph_list:
        number_list.append({'number': len(g['graph'].edges()), 'name': g['name']})
    return number_list

# return a list of {ratio between edges and nodes numbers, name} from directory with _graph.json files
def edges_over_nodes(directory):
    number_list = []
    graph_list = lc.json_to_graph('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    for g in graph_list:
        if len(g['graph'].nodes()) != 0:
            ratio = float(len(g['graph'].edges())) / float(len(g['graph'].nodes()))
            number_list.append({'number': ratio, 'name': g['name']})
    return number_list

# returns the average number for a list of dictionnaries containing a number attribute
def average_number(number_list):
    res = 0
    for d in number_list:
        res += d['number']
    res = float(res) / float(len(number_list))
    return res

# show a simple graphic
def simple_graphic(xName, xData):
    plt.plot(xData)
    plt.xlabel(xName)
    plt.show()

# show a double graphic
def double_graphic(xName, yName, xData, yData):
    plt.plot(xData, yData)
    plt.xlabel(xName)
    plt.ylabel(yName)
    plt.show()

# show an histogram
def histogram(xName, xData):
    n, bins, patches = plt.hist(xData, 50, normed=1, facecolor='b', alpha=0.5)
    plt.xlabel(xName)
    plt.ylabel('Probability')
    plt.grid(True)
    print 'values returned:'
    print 'n: ', n
    print 'bins: ', n
    print 'patches: ', patches
    plt.show()
###################################################
# END OF PART RELATED TO GET/SHOW CHARACTERISTICS #
###################################################

########################################################
# PART ON REDUCTION OF MARGUERITES FROM SEVERAL GRAPHS #
########################################################
# return the min_marg without the petals or the tails that aren't in mg
def reduct_marguerite(min_marg, mg):
    for p in min_marg['petals']:
        if p not in mg['petals']:
            min_marg['petals'].remove(p)
    for t in min_marg['tails']:
        if t not in mg['tails']:
            min_marg['tails'].remove(t)
    return min_marg

# take all marguerites from all json files and return a list of minimal marguerites
# uses an intermediate dictionnary which associate a heart to a dictionnary of petals and tails
def reduct_marguerites(directory):
    min_marg = {'directory': directory}
    marg_list = m.json_to_marguerites(directory)
    for mgs in marg_list:
        for mg in mgs['marguerites']:
            (a,b,c) = mg['heart']
            if b not in min_marg.keys():
                min_marg[b] = mg['heart']
                min_marg[mg['heart']] = mg
            else:
                min_marg[min_marg[b]] = reduct_marguerite(min_marg[min_marg[b]], mg)
    return min_marg

# return a serialized min_marg
def serialize_min_marg(min_marg):
    s_min_marg = {'directory': min_marg['directory']}
    for k in min_marg.keys():
        if type(k)==str:
            continue
        # the key is a tuple, it is to be serialized too
        s_k = json.dumps(k)
        min_marg[k] = m.format_marguerite(min_marg[k])
        # the function serialize_marguerites takes/returns a list
        aux = m.serialize_marguerites([min_marg[k]])
        s_min_marg[s_k] = json.dumps(aux[0])
    return s_min_marg

# return a min_marg
def deserialize_min_marg(s_min_marg):
    min_marg = {'directory': s_min_marg['directory']}
    keys = []
    # /!\ WARNING: the type unicode comes from the json file
    # we tried to format the same way every object but beware of modifying functions
    # /!\/!\/!\/!\
    for s_k in s_min_marg.keys():
        # if a '[' appear, it means a tuple have been dumped.
        # If len==1, s_k is representing a str
        if len(s_k.split('['))==1:
            keys.append(s_k.encode(encoding='utf8'))
        else:
            keys.append(s_k)
    for s_k in keys:
        if type(s_k)==str:
            min_marg[s_k] = s_min_marg[s_k]
            continue
        k = m.format_node(tuple(json.loads(s_k)))
        # the function serialize_marguerites takes/returns a list
        min_marg[k] = m.deserialize_marguerites([json.loads(s_min_marg[s_k])])[0]
        min_marg[k] = m.format_marguerite(min_marg[k])
    return min_marg

# in order to delete entries without petals in min_marg.json
# we suggest many specific functions like this one to see specific information
def reduce_min_marg_petals(min_marg):
    r_min_marg = {'directory': min_marg['directory']}
    for k in min_marg.keys():
        if type(k)==str:
            continue
        if len(min_marg[k]['petals']) != 0:
            r_min_marg[k] = min_marg[k]
    return r_min_marg
###############################################################
# END OF PART ON REDUCTION OF MARGUERITES FROM SEVERAL GRAPHS #
###############################################################

#########################################################
# ANALYSIS OF NODES OCCURENCE AROUND A MARGUERITE HEART #
#########################################################
# return petals_occ with added count of found nodes
def petals_occurence_around(marguerite, petals_occ):
    for p in marguerite['petals']:
        petals_occ['total'] += 1
        (a, p_name, c) = p
        if p_name in petals_occ.keys():
            petals_occ[p_name] += 1
        else:
            petals_occ[p_name] = 1
    return petals_occ

# return tails_occ with added count of found nodes
def tails_occurence_around(marguerite, tails_occ):
    for p in marguerite['tails']:
        tails_occ['total'] += 1
        (a, t_name, c) = p
        if t_name in tails_occ.keys():
            tails_occ[t_name] += 1
        else:
            tails_occ[t_name] = 1
    return tails_occ

# returns a dictionnary of name of nodes and occurencies counted
def node_occurence_around(name, directory):
    total = 0
    petals_occ = {'name': name, 'directory': directory, 'total': 0}
    tails_occ = {'name': name, 'directory': directory, 'total': 0}
    ms_list = m.json_to_marguerites(directory)
    for ms in ms_list:
        marguerites = ms['marguerites']
        for marguerite in marguerites:
            (a,m_name,c) = marguerite['heart']
            if m_name == name:
                #total += 1
                petals_occ = petals_occurence_around(marguerite, petals_occ)
                tails_occ = tails_occurence_around(marguerite, tails_occ)
    #petals_occ['total'] = total
    #tails_occ['total'] = total
    return (petals_occ, tails_occ)

# function in order to seperate general information from particular data
# used in 'if' conditions to only process particular data
def not_occ_data(_occ, k):
    a = (type(_occ[k]) == str)
    b = (k == 'total')
    return (a or b)

# return a occurence dictionnary without the value 1
# we consider not interessant those nodes even though they are a majority
# it allow the stats to be more precise for higher numbered nodes
def clean_occurence(_occ):
    for k in _occ.keys():
        if not_occ_data(_occ, k):
            continue
        if _occ[k] == 1:
            del _occ[k]
            _occ['total'] -= 1
    return _occ

# return the occurencies that are over a certain threshold
def threshold_occurencies(_occ, thresh):
    for k in _occ.keys():
        if not_occ_data(_occ, k):
            continue
        if _occ[k] < thresh:
            del _occ[k]
    return _occ

# returns a dictionnary with average value instead of global
def average_occ_dict(_occ):
    if _occ['total'] != 0:
        for k in _occ.keys():
            if not_occ_data(_occ, k):
                continue
            _occ[k] = (_occ[k]/float(_occ['total']))
    return _occ

# convert a occurencies dictionnary to data for plots
def occ_to_xData(_occ):
    xData = []
    if _occ['total'] != 0:
        for k in _occ.keys():
            if not_occ_data(_occ, k):
                continue
            xData.append(_occ[k]/float(_occ['total']))
    return xData
################################################################
# END OF ANALYSIS OF NODES OCCURENCE AROUND A MARGUERITE HEART #
################################################################

###############################
# SAVING AND PRINTING RESULTS #
###############################
# save the serialized min_marg into a 'stat/min_marg.json' file
def s_min_marg_to_json(s_min_marg):
    verif_directory(s_min_marg['directory'])
    filename = s_min_marg['directory']+'stats/min_marg.json'
    with open(filename, 'w') as f:
        json.dump(s_min_marg, f, indent=4)

# combine serialization of the min_marg and dumping into json.
def min_marg_to_json(min_marg):
    s_min_marg = serialize_min_marg(min_marg)
    s_min_marg_to_json(s_min_marg)

# return min_marg from json file
def json_to_min_marg(directory):
    filename = get_json(directory)[0]
    min_marg = {}
    with open(filename, 'r') as f:
        s_min_marg = json.load(f)
        min_marg = deserialize_min_marg(s_min_marg)
    return min_marg

# print a reducted marguerite list
def print_min_marg(min_marg):
    print '\nPRINTING THE REDUCTED MARGUERITES LIST FROM ', min_marg['directory'], ': '
    for k in min_marg.keys():
        if type(k)==str:
            continue
        print '\nminimal marguerite around heart ', k, ': '
        print repr(min_marg[k])
    print ''

# only print around a specific node characterized by his name
def print_min_marg_around_node(min_marg, name):
    for k in min_marg.keys():
        if type(k)==str:
            continue
        (a,b,c) = k
        if b == name:
            print '\nminimal marguerite around heart ', k, ': '
            print repr(min_marg[k])
######################################
# END OF SAVING AND PRINTING RESULTS #
######################################

def test():
    #[WORKED] in order test() doesn't generate an IndentationError when all commented
    print 'test function'

    #[WORKED] generate number of nodes for each json file
    #number_list = nodes_number('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #print number_list

    #[WORKED] generate number of edges for each json file
    #number_list = edges_number('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #print number_list

    #[WORKED] generate number of edges for each json file
    #number_list = edges_over_nodes('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #print number_list

    #[WORKED] calculate the average for the ratio edges over nodes
    #number_list = edges_over_nodes('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #average = average_number(number_list)
    #print average

    #[WORKED] try the simple_graphic
    #number_list = edges_number('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #number_list2 = edges_number('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #xData = []
    #xData2 = []
    #for c in number_list:
    #    xData.append(c['number'])
    #for c in number_list2:
    #    xData2.append(c['number'])
    #simple_graphic('edges', xData)

    #[WORKED] try the histogram
    #number_list = edges_over_nodes('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #xData = []
    #for c in number_list:
    #    xData.append(c['number'])
    #histogram('edges over nodes ratio', xData)

    #[WORKED] reducts marguerites to a dictionnary of minimal ones
    #mm = reduct_marguerites('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #print_min_marg(mm)
    #min_marg_to_json(mm)

    #[WORKED] retrieve min_marg information from a json file
    #min_marg = json_to_min_marg('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/simple_cond/')
    #print_min_marg(min_marg)

    #[WORKED] delete entries without petals
    #mm = json_to_min_marg('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #mm = reduce_min_marg_petals(mm)
    #print_min_marg(mm)
    #print_min_marg_around_node(mm, 'system_server')
    #min_marg_to_json(mm)

    #[WORKED] counting nodes occurencies around system_server
    #[WORKED] cleaning nodes occurencies
    #(p, t) = node_occurence_around('system_server', '/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #print 'petals occurencies:\n', p
    #print 'tails occurencies:\n', t
    #clean_occurence(p)
    #clean_occurence(t)
    #print 'cleaned_petals occurencies:\n', p
    #print 'cleaned_tails occurencies:\n', t

    #[WORKED] xData test
    #(p, t) = node_occurence_around('system_server', '/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #clean_occurence(p)
    #xData = occ_to_xData(p)
    #print 'xData: ', xData

    #[WORKED] Threshold 
    #(p, t) = node_occurence_around('system_server', '/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #clean_occurence(p)
    #clean_occurence(t)
    #average_occ_dict(p)
    #average_occ_dict(t)
    #print '\naverage occurencies dictionnary of tails:\n', t
    #print '\naverage occurencies dictionnary of petals:\n', p
    #threshold_occurencies(p, 0.1)
    #threshold_occurencies(t, 0.1)
    #print '\nTreshold at 0.1 for tails:\n', t
    #print '\nTreshold at 0.1 for petals:\n', p

test()
