#coding: utf8

#This file purpose is to add the concept of marguerites to the information collected in a graph

import logsConverter as lc
import algo
import json
import glob

#returns a list of the json files in the named directory
def get_json(directory):
    return glob.glob(directory+'/*_marguerites.json')

# return a node with the right encoded attributes (converted in utf8)
def format_node(node):
    (a,b,c) = node
    a = a.encode(encoding='utf8')
    b = b.encode(encoding='utf8')
    return (a,b,c)

# return a marguerite with the right encoded attributes (converted in utf8)
def format_marguerite(marguerite):
    (h,ts,ps) = (marguerite['heart'], marguerite['tails'], marguerite['petals'])
    (f_h, f_ts, f_ps) = (format_node(h), [], [])
    for t in ts:
        f_ts.append(format_node(t))
    for p in ps:
        f_ps.append(format_node(p))
    return {'heart': f_h, 'tails': f_ts, 'petals': f_ps}

#return a serialized list of marguerites
#a marguerite has a node-tuple as heart, and two node-tuple lists as tails and petals
def serialize_marguerites(marguerites):
    s_marguerites = []
    for marguerite in marguerites:
        s_heart = json.dumps(marguerite['heart'])
        s_tails = []
        s_petals = []
        for t in marguerite['tails']:
            s_tails.append(json.dumps(t))
        for p in marguerite['petals']:
            s_petals.append(json.dumps(p))
        s_marguerites.append({'heart': s_heart, 'tails': s_tails, 'petals': s_petals})
    return s_marguerites

#take a serialized list of marguerite and return the real one
def deserialize_marguerites(s_marguerites):
    marguerites = []
    for s_marguerite in s_marguerites:
        heart = tuple(json.loads(s_marguerite['heart']))
        tails = []
        petals = []
        for t in s_marguerite['tails']:
            tails.append(tuple(json.loads(t)))
        for p in s_marguerite['petals']:
            petals.append(tuple(json.loads(p)))
        marguerites.append(format_marguerite({'heart': heart, 'tails': tails, 'petals': petals}))
    return marguerites

#take a graph_list, generate and serialize a list of marguerites in a json file for each
def marguerites_to_json(graph_list):
    for g in graph_list:
        m_list = algo.marguerites(g['graph'])
        s_marguerites = serialize_marguerites(m_list)
        s_marguerites = json.dumps(s_marguerites)
        data = {}
        data['marguerites'] = s_marguerites
        data['directory'] = g['directory']
        data['name'] = g['name']
        filename = g['directory'] + g['name'] + '_marguerites.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

#deserialize all json files from a directory and return a list of the marguerites list
#each can be matched with its graph by comparing the 'name' and 'directory' attributes
def json_to_marguerites(directory):
    marguerites_list = []
    jsons = get_json(directory)
    for filename in jsons:
        with open(filename, 'r') as f:
            data = json.load(f)
            marguerites = json.loads(data['marguerites'])
            marguerites = deserialize_marguerites(marguerites)
            marguerites_list.append({'marguerites': marguerites, 'directory': data['directory'], 'name': data['name']})
    return marguerites_list

# print a marguerite
def print_marguerite(marguerite):
    print '\nPRINTING THE MARGUERITE'
    print 'HEART: ', marguerite['heart']
    print 'PETALS: ', marguerite['petals']
    print 'TAILS: ', marguerite['tails']
    print ''

#Function in order to test the API
def test():
    #[WORKED] just in order the function test doesn't generate an IndentationError
    print 'test function'

    #[WORKED] generate _marguerite.json files
    #graph_list = lc.json_to_graph('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/log/')
    #marguerites_to_json(graph_list)

    #[WORKED] retrieve information from json_file and print it
    #marguerites_list = json_to_marguerites('/home/tr4ckt3r/Documents/Projet3A/BlareLogs/simple_cond/')
    #for marguerites in marguerites_list:
    #    print '\npour le graphe ', marguerites['name']
    #    for m in marguerites['marguerites']:
    #        algo.print_marguerite(m)

#test()
