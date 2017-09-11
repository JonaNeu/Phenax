import networkx as nx
import graphtodot as dot
import libsystemflowgraph as lsfg
import os
import os.path

def testintersection2():
        G1 = nx.MultiDiGraph()
        G1.add_edges_from([(("file", "/data/data/com.allen.mp", 1), ("process", "com.allen.mp", 2)), (("process", "sh", 3), ("file", "/data/local/toto", 4)) ])
        print "G1"
        print(str(G1.edges()))

        G2 = nx.MultiDiGraph()
        G2.add_edges_from([(("file", "/data/data/com.allen.mp", 1), ("process", "com.allen.mp", 2)), (("process", "sh", 3), ("file", "/data/local/toto", 4))])
        print "\n\nTest 1 : intersection egale a G1"
        print "G2"
        print(str(G2.edges()))
        print "Resultat"
        print(str(intersection2(G1, G2, [("com.allen.mp", "com.aijou")]).edges()))

        G3 = nx.MultiDiGraph()
        G3.add_edges_from([(("file", "/data/data/com.allen.mp", 1), ("process", "com.allen.mp", 2)), (("process", "shalom", 3), ("file", "/data/local/titi", 4))])
        print "\n\nTest 2 : intersection avec un sous-ensemble de edge en commun"
        print "G3"
        print(str(G3.edges()))
        print "Resultat"
        print(str(intersection2(G1, G3, [("com.allen.mp", "com.aijou")]).edges()))


        G4 = nx.MultiDiGraph()
        G4.add_edges_from([(("file", "/data/data/com.al", 1), ("process", "com.mp", 2))])
        print "\n\nTest 3 : intersection nulle deux ensembles distincts"
        print "G4"
        print(str(G4.edges()))
        print "Resultat"
        print(str(intersection2(G1, G4, [("com.allen.mp", "com.aijou")]).edges()))

        G5 = nx.MultiDiGraph()
        G5.add_edges_from([(("file", "/data/data/com.aijou", 3), ("process", "com.allen.mp", 5)), (("file", "/data/data/com.al", 1), ("process", "com.mp", 2))])
        print "\n\nTest 4 : intersection non-nulle. Un arc avec un noeud similaire"
        print "G5"
        print(str(G5.edges()))
        print "Resultat"
        print(str(intersection2(G1, G5, [("com.allen.mp", "com.aijou")]).edges()))

def test_mult_intersection():
    enleve="25b55588a296a58191fd2daa6de2aab3951eb99d.apk-99.gpickle","com.tutusw.fingerscanner"
    
        #file_list = [ "droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle", "28176bc34e54e087e90bbbaba0c846ec9182db17.apk-dimva2013-99.gpickle", "54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle"]
        #sim_name_list = ["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup", "com.tutusw.phonespeedup", "com.allen.mp"]

    file_list = [ "droidkungfu.apk-dimva2013-99.gpickle",  "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle"]
    sim_name_list = ["com.aijiaoyou.android.sipphone", "com.tutusw.phonespeedup"]
    graphs = [nx.read_gpickle("log/" + name) for name in file_list]
    index = 0
    res = lsfg.mult_intersection(graphs, sim_name_list)
    res2 = lsfg.minus(res, nx.read_gpickle("log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle"), [("com.aijiaoyou.android.sipphone", "mobi.thinkchange.fingerscannerlite")])

    file_list2 = ["log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/benin/com.rovio.angrybirds.ads.apk-99.gpickle","log/benin/com.mozilla.android.apps.firefox.apk-integrity.gpickle","log/benin/cellfish.ironman3wp-1.apk-99.gpickle","log/benin/com.g6677.android.ldentist-1.apk-99.gpickle","log/benin/com.industrymagic.crazyjump-1.apk-99.gpickle","log/benin/jackpal.androidterm-1.apk-99.gpickle"]
    graphs2 = [nx.read_gpickle(name) for name in file_list2]
    graphs2.insert(0,res)
    sim_name_list2 = ["com.aijiaoyou.android.sipphone", "mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*"]
    res3 = lsfg.mult_minus(graphs2,sim_name_list2)

    print("RES 3 : " + str(len(res3.nodes())) + " nodes et " + str(len(res3.edges())) + " edges")   

    conn_list = nx.connected_component_subgraphs(res3.to_undirected())
    print("premiere partie connexe : " + str(len(conn_list [0].nodes())) + " nodes et " + str(len(conn_list [0].edges())) + " edges")   
    print(str(conn_list [0].edges()))
    dot.save_dot_to_file(dot.build_dot_graph(res3), "res3.dot")
    dot.save_dot_to_file(dot.build_dot_graph(graphs2[-1]), "jackpal.dot")


def testminus():
    G1 = nx.MultiDiGraph()
    G1.add_edges_from([(("file", "/data/data/com.allen.mp", 1), ("process", "com.allen.mp", 2)), (("process", "sh", 3), ("file", "/data/local/toto", 4)) ])
    print "G1"
    print(str(G1.edges()))

    G2 = nx.MultiDiGraph()
    G2.add_edges_from([(("file", "/data/data/com.allen.mp", 1), ("process", "com.allen.mp", 2)), (("process", "sh", 3), ("file", "/data/local/toto", 4))])
    print "\n\nTest 1 :minus egale a vide ?"
    print "G2"
    print(str(G2.edges()))
    print "Resultat"
    print(str(lsfg.minus(G1, G2, [("com.allen.mp", "com.aijou")]).edges()))
    G3 = nx.MultiDiGraph()
    G3.add_edges_from([(("file", "/data/data/com.allen.mp", 1), ("process", "com.allen.mp", 2)), (("process", "shalom", 3), ("file", "/data/local/titi", 4))])
    print "\n\nTest 2 : moins  avec un sous-ensemble de edge en commun devrait rester que le second arc (avec shalom)"
    print "G3"
    print(str(G3.edges()))
    print "Resultat"
    print(str(lsfg.minus(G1, G3, [("com.allen.mp", "com.aijou")]).edges()))


    G4 = nx.MultiDiGraph()
    G4.add_edges_from([(("file", "/data/data/com.al", 1), ("process", "com.mp", 2))])
    print "\n\nTest 3 : minus avec  deux ensembles distincts resultat devrait etre vide"
    print "G4"
    print(str(G4.edges()))
    print "Resultat"
    print(str(lsfg.minus(G1, G4, [("com.allen.mp", "com.aijou")]).edges()))

    G5 = nx.MultiDiGraph()
    G5.add_edges_from([(("file", "/data/data/com.aijou", 3), ("process", "com.allen.mp", 5)), (("file", "/data/data/com.al", 1), ("process", "com.mp", 2))])
    print "\n\nTest 4 : intersection non-nulle. Un arc avec un noeud similaire le res devrait avoir un seul arc avec com.al et com.mp"
    print "G5"
    print(str(G5.edges()))
    print "Resultat"
    print(str(lsfg.minus(G1, G5, [("com.allen.mp", "com.aijou")]).edges()))

def test_anonym():
    file_list = [ "droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle", "28176bc34e54e087e90bbbaba0c846ec9182db17.apk-dimva2013-99.gpickle", "54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle"]
    sim_name_list = ["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup", "com.tutusw.phonespeedup", "com.allen.mp"]
    graphs = [nx.read_gpickle("log/" + name) for name in file_list]
    for g in lsfg.anonymize_graphs(graphs,sim_name_list):
        print "*******"
        print(str(g.nodes()))

#test_anonym()
    

#G1 = nx.read_gpickle("log/54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle")
#G2= nx.read_gpickle("log/droidkungfu.apk-dimva2013-99.gpickle")
#G4= lsfg.intersection(G1,G2,[("com.allen.mp","com.aijiaoyou.android.sipphone")])
#
#G5 =lsfg.minus(G1,G4,[("com.allen.mp","com.aijiaoyou.android.sipphone")])
#
#print("******** VOICI LES NOEUDS DE G1 ************ ")
#print(str(G1.nodes()))
#print("******** VOICI LES NOEUDS DE G2 ************ ")
#print(str(G2.nodes()))
#
#
#print("******** VOICI LES NOEUDS DE G4 (avec renommage) ************ ")
#print(str(G4.nodes()))
#
#print("******** VOICI LES ARCS DE G4 (avec renommage) ************ ")
#print(str(G4.edges()))
#
#print("******** VOICI LES NOEUDS DE G5 (avec renommage) ************ ")
#print(str(G5.nodes()))
#print("******** VOICI LES  ARCS  DE G5 (avec renommage) ************ ")
#print(str(G5.edges()))
#
#print("******** test sur les ensembles de noeuds ) ************ ")
#
#print("G1")
#print(len(G1.nodes()))
#print("G2")
#print(len(G2.nodes()))
#print("G4 (G1 inter G2)")
#print(len(G4.nodes()))
#print("G5 soit G1- (G1 inter G2)")
#print(len(G5.nodes()))
#
#
#print("******** test sur les ensembles d'arcs ) ************ ")
#
#print("G1")
#print(len(G1.edges()))
#print("G2")
#print(len(G2.edges()))
#print("G4 (G1 inter G2)")
#print(len(G4.edges()))
#print("G5 soit G1- (G1 inter G2)")
#print(len(G5.edges()))
#
#print("G1 contiens des noeuds, des arcs en double ? ")
#print(lsfg.contains_double_nodes(G1))
#print(lsfg.contains_double_edges(G1))
#
#print("G4 contiens des noeuds, des arcs en double ? ")
#print(lsfg.contains_double_nodes(G4))
#print(lsfg.contains_double_edges(G4))
#
#print("G5 contiens des noeuds, des arcs en double ? ")
#print(lsfg.contains_double_nodes(G5))
#print(lsfg.contains_double_edges(G5))
#
#
#occ = [0, 0, 0, 0]
#for e in G1.edges():
#   #Occurennce dans G4 et G5 a la fois, uniquement dans G4, uniquement dans G5 , absent de G4 et G5
#   if G4.has_edge(e[0], e[1]):
#       if G5.has_edge(e[0], e[1]):
#           occ[0] += 1
#       else:
#           occ[1] += 1
#   elif G5.has_edge(e[0], e[1]):
#       occ[2] += 1
#   else:
#       occ[3] += 1 
#
#print(str(occ))

#test_mult_intersection()



#test1=nx.MultiDiGraph()
#test1.add_edges_from([(('file', '/data/data/com.allen.mp/truc', 57644), ('process', 'sh', 1090)),( ('file', '/data/anr/traces.txt', 32782), ('process', 'sh', 1069))] )
#testvide=nx.MultiDiGraph()

#testmeme1=nx.MultiDiGraph()
#testmeme1.add_edges_from([(('file', '/data/data/com.allen.mp/truc', 57644), ('process', 'sh', 1090)),( ('file', '/data/anr/traces.txt', 32782), ('process', 'sh', 1069))] )

#testpasvideMAISdiff1=nx.MultiDiGraph()
#testpasvideMAISdiff1.add_edges_from([(('file', 'bidule', 57644), ('process', 'sh', 1090)),( ('file', '/data/anr/traces.txt', 32782), ('process', 'trututuresh', 1069))] )


#testUnearcEgal=nx.MultiDiGraph()
#testUnearcEgal.add_edges_from([(('file', '/data/data/com.allen.mp/truc', 57644), ('process', 'chouette', 1090)),( ('file', '/data/anr/traces.txt', 32782), ('process', 'sh', 1069))] )

#testsimilaire=nx.MultiDiGraph()
#testsimilaire.add_edges_from([(('file', '/data/data/toto/truc', 57644), ('process', 'sh', 1090)),( ('file', '/data/anr/traces.txt', 32782), ('process', 'sh', 1069))] )

#testvide=nx.MultiDiGraph()
#print("voici test1")
#print(test1.edges())

#print("devrait tre vide")
#print(str(lsfg.intersection(test1,testvide,[("bonjour","bonsoir")]).edges()))

#print("devrait  tre egal a test1")
#print(str(lsfg.intersection(test1,testmeme1,[("bonjour","bonsoir")]).edges()))

#print("devrait  tre vide")
#print(str(lsfg.intersection(test1,testpasvideMAISdiff1,[("bonjour","bonsoir")]).edges()))


#print("devrait  tre un seul arc egal au second de test1")
#print(str(lsfg.intersection(test1,testUnearcEgal,[("bonjour","bonsoir")]).edges()))

#print("dernier test")
# print(str(lsfg.intersection(test1,testsimilaire,[("com.allen.mp","toto")]).edges()))


def test_gen_sign ():
    #file_list = [ "droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle", "28176bc34e54e087e90bbbaba0c846ec9182db17.apk-dimva2013-99.gpickle", "54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle"]
    #sim_name_list = ["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup", "com.tutusw.phonespeedup", "com.allen.mp"]

    #graphs = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"droid.gallery")),lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")),nx.read_gpickle("log/"+name))) for name in file_list],sim_name_list)


    #file_list2 = ["log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/benin/com.rovio.angrybirds.ads.apk-99.gpickle","log/benin/com.mozilla.android.apps.firefox.apk-integrity.gpickle","log/benin/cellfish.ironman3wp-1.apk-99.gpickle","log/benin/com.g6677.android.ldentist-1.apk-99.gpickle","log/benin/com.industrymagic.crazyjump-1.apk-99.gpickle","log/benin/jackpal.androidterm-1.apk-99.gpickle"]
    #sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*"]

    #graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2],sim_name_list2)
    #
    #sign = lsfg.compute_sign (graphs,graphs2,[lambda g: not(lsfg.is_empty(g))] )


    # print("2e test")
    # print("faire un test sur une liste de graph avec plus d'une signature") 
    # file_list = [ "droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle", "28176bc34e54e087e90bbbaba0c846ec9182db17.apk-dimva2013-99.gpickle", "54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle", "a8aaacd61dc517bf91a53ba59698c36cb171c49cfdcbea029cfa10484de60be8-dimva2013-99.gpickle", "22f2299b827c261528c10228963beeed781d7b8952e0476e9b68b0376eb82abd-dimva2013-99.gpickle"]
    # sim_name_list = ["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup", "com.tutusw.phonespeedup", "com.allen.mp", "com.tutusw.fingerscanner", "com.tutusw.fingerscanner"]
    
    # graphs = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"busybox")),
    #                         lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"acct/uid/0")),
    #                                   lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_serverMMM")),
    #                                             lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")),
    #                                                   nx.read_gpickle("log/"+name))))) for name in file_list],sim_name_list)
    
    # file_list2 = ["log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/benin/com.rovio.angrybirds.ads.apk-99.gpickle","log/benin/com.mozilla.android.apps.firefox.apk-integrity.gpickle","log/benin/cellfish.ironman3wp-1.apk-99.gpickle","log/benin/com.g6677.android.ldentist-1.apk-99.gpickle","log/benin/com.industrymagic.crazyjump-1.apk-99.gpickle","log/benin/jackpal.androidterm-1.apk-99.gpickle", "log/benin/stericson.busybox-1.apk-99.gpickle"]
        # sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*", "*"]

        # graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2],sim_name_list2)

    # sign = lsfg.compute_sign (graphs,graphs2,[lambda g: not(lsfg.is_empty(g))] ) #,lambda g: not(lsfg.exists_edges (lambda e: lsfg.edges_name_contains(e,"busybox"),g))] )
    # lsfg.print_sign(sign)

    # print("3e test")
    # print("cas ou deux graphs sont senses avoir la mm signature difference de droidkungfu") 
    # file_list = [ "a8aaacd61dc517bf91a53ba59698c36cb171c49cfdcbea029cfa10484de60be8-dimva2013-99.gpickle", "22f2299b827c261528c10228963beeed781d7b8952e0476e9b68b0376eb82abd-dimva2013-99.gpickle"]
    # sim_name_list = [ "com.tutusw.fingerscanner", "com.tutusw.fingerscanner"]
    # graphs = lsfg.anonymize_graphs([ lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"droid.gallery")),lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")), nx.read_gpickle("log/"+name))) for name in file_list],sim_name_list)
    # file_list2 = ["log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/benin/com.rovio.angrybirds.ads.apk-99.gpickle","log/benin/com.mozilla.android.apps.firefox.apk-integrity.gpickle","log/benin/cellfish.ironman3wp-1.apk-99.gpickle","log/benin/com.g6677.android.ldentist-1.apk-99.gpickle","log/benin/com.industrymagic.crazyjump-1.apk-99.gpickle","log/benin/jackpal.androidterm-1.apk-99.gpickle", "log/benin/stericson.busybox-1.apk-99.gpickle"]
        # sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*", "*"]

        # graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2],sim_name_list2)

        # sign = lsfg.compute_sign (graphs,graphs2)


    # graph_test= lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")), graphs[0] )
    # print("edges avant ")
    # print(graphs[0].edges())
    # print("edges apres ")
    # print(graph_test.edges())
    # # print("3e test")
    # print("test avec 2 graph infectes par une sous famille droidkungfu") 
    # file_list = [ "a8aaacd61dc517bf91a53ba59698c36cb171c49cfdcbea029cfa10484de60be8-dimva2013-99.gpickle", "22f2299b827c261528c10228963beeed781d7b8952e0476e9b68b0376eb82abd-dimva2013-99.gpickle"]
    # sim_name_list = [ "com.tutusw.fingerscanner", "com.tutusw.fingerscanner"]
    # graphs = lsfg.anonymize_graphs([nx.read_gpickle("log/"+name) for name in file_list],sim_name_list)
    # file_list2 = ["log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/benin/com.rovio.angrybirds.ads.apk-99.gpickle","log/benin/com.mozilla.android.apps.firefox.apk-integrity.gpickle","log/benin/cellfish.ironman3wp-1.apk-99.gpickle","log/benin/com.g6677.android.ldentist-1.apk-99.gpickle","log/benin/com.industrymagic.crazyjump-1.apk-99.gpickle","log/benin/jackpal.androidterm-1.apk-99.gpickle"]
        # sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*"]

        # graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2],sim_name_list2)

        # sign3 = lsfg.compute_sign (graphs,graphs2)
    
    # print("4e test : test avec des graphes de deux familles (DroidKungFu et jSMSHider")
    # # Liste des malwares DroidKungFu
    # file_list = [] # [ "Droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle", "28176bc34e54e087e90bbbaba0c846ec9182db17.apk-dimva2013-99.gpickle", "54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle"]
    # # Liste des malwares jSMSHider
    # file_list.extend(["7678174e22967accc4d6470579dfa8511c37e1c628d08c23b70df7e23703f769-integrity-99.gpickle", "1c29b3010a2e50bca0c5bb45963a74d135addfa206e29785c564fc0a61f1a183-integrity-99.gpickle", "147798e4306d06a6eea438ec994779677daf4c1c.apk-integrity-99.gpickle", "1f56be54a06d20b4f394f4023d9fd6a4c3c443d1.apk-integrity-99.gpickle"]) 
        # sim_name_list =  [] #["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup", "com.tutusw.phonespeedup", "com.allen.mp", "com.tutusw.fingerscanner", "com.tutusw.fingerscanner"]
    # sim_name_list.extend(["org.expressme.love.ui", "org.expressme.love.ui", "hider.AppInstall.nvanmoshiriji_V31_mumayi_aff08", "hider.AppInstall.nvanmoshiriji_V31_mumayi_aff08"])    
        # #graphs = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"sh")),lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_server")),lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")), nx.read_gpickle("log/"+name)))) for name in file_list],sim_name_list)
    # graphs = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"droid.gallery")),
    #                         lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"acct/uid/0MMM")),
    #                                   lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_serverMMMM")),
    #                                             lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")),
    #                                                   nx.read_gpickle("log/"+name))))) for name in file_list],sim_name_list)
    
        # file_list2 = ["log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/benin/com.rovio.angrybirds.ads.apk-99.gpickle","log/benin/com.mozilla.android.apps.firefox.apk-integrity.gpickle","log/benin/cellfish.ironman3wp-1.apk-99.gpickle","log/benin/com.g6677.android.ldentist-1.apk-99.gpickle","log/benin/com.industrymagic.crazyjump-1.apk-99.gpickle","log/benin/jackpal.androidterm-1.apk-99.gpickle", "log/benin/stericson.busybox-1.apk-99.gpickle"]
        # sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*", "*"]

        # graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2],sim_name_list2)

        
    # sign = lsfg.compute_sign (graphs,graphs2,[lambda g: not(lsfg.is_empty(g))] )
    # lsfg.print_sign(sign)


    #print("5e test : test avec des graphes de trois  familles: DroidKungFu 1 & 2 et jSMSHider")
    ## Liste des malwares DroidKungFu
    #file_list = [ "droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle", "28176bc34e54e087e90bbbaba0c846ec9182db17.apk-dimva2013-99.gpickle", "54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle"]
    ## Liste des malwares jSMSHider
    #file_list.extend(["7678174e22967accc4d6470579dfa8511c37e1c628d08c23b70df7e23703f769-integrity-99.gpickle", "1c29b3010a2e50bca0c5bb45963a74d135addfa206e29785c564fc0a61f1a183-integrity-99.gpickle", "147798e4306d06a6eea438ec994779677daf4c1c.apk-integrity-99.gpickle", "1f56be54a06d20b4f394f4023d9fd6a4c3c443d1.apk-integrity-99.gpickle"])
    ## malware droidkungfu 2
    #file_list.extend ([ "a8aaacd61dc517bf91a53ba59698c36cb171c49cfdcbea029cfa10484de60be8-dimva2013-99.gpickle", "22f2299b827c261528c10228963beeed781d7b8952e0476e9b68b0376eb82abd-dimva2013-99.gpickle"])


    #
        #sim_name_list =  ["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup", "com.tutusw.phonespeedup", "com.allen.mp"]
    #sim_name_list.extend(["org.expressme.love.ui", "org.expressme.love.ui", "hider.AppInstall.nvanmoshiriji_V31_mumayi_aff08", "hider.AppInstall.nvanmoshiriji_V31_mumayi_aff08"]) 
    #sim_name_list.extend( [ "com.tutusw.fingerscanner", "com.tutusw.fingerscanner"])
    #

        ##graphs = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"sh")),lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_server")),lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")), nx.read_gpickle("log/"+name)))) for name in file_list],sim_name_list)

    #graphs = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"droid.gallery")),
    #                         lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"acct/uid/")),
    #                                   lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_server")),
    #                                             lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")),
    #                                                   nx.read_gpickle("log/"+name))))) for name in file_list],sim_name_list)
    #graphscopy = [g for g in graphs]
    #
        #file_list2 = ["log/benin/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/benin/com.rovio.angrybirds.ads.apk-99.gpickle","log/benin/com.mozilla.android.apps.firefox.apk-integrity.gpickle","log/benin/cellfish.ironman3wp-1.apk-99.gpickle","log/benin/com.g6677.android.ldentist-1.apk-99.gpickle","log/benin/com.industrymagic.crazyjump-1.apk-99.gpickle","log/benin/jackpal.androidterm-1.apk-99.gpickle", "log/benin/stericson.busybox-1.apk-99.gpickle"]
        #sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*", "*"]

        #graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2],sim_name_list2)

        #
    #sign = lsfg.compute_sign (graphs,graphs2,[lambda g: not(lsfg.is_empty(g))] )
    #for sfg_key in sign.keys():
    #   sfg_tmp = lsfg.intersection(nx.read_gpickle("log/droidkungfu.apk-dimva2013-99.gpickle"), sfg_key, [("com.aijiaoyou.android.sipphone", "blare-anonym")])
    #   print ("Intersection du graphe avec graphe de taille " + str(len(sfg_key.edges())) + " arcs possede " + str(len(sfg_tmp.edges())) + " arcs") 
    ##lsfg.print_sign(sign)
        ##lsfg.stats_from_sign (sign,graphs)

    print "***"
    print "Test DroidKungFu1.1, DroidKungFu1.2, DroidKungFu2, jSMSHider,  BadNews"
    # DroidKungFu 1.1
    file_list = ["droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle", "28176bc34e54e087e90bbbaba0c846ec9182db17.apk-dimva2013-99.gpickle", "54f3c7f4a79184886e8a85a743f31743a0218ae9cc2be2a5e72c6ede33a4e66e-dimva2013-99.gpickle"]
    sim_name_list = ["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup", "com.tutusw.phonespeedup", "com.allen.mp"]
    # jSMSHider
    file_list.extend(["7678174e22967accc4d6470579dfa8511c37e1c628d08c23b70df7e23703f769-99.gpickle", "1c29b3010a2e50bca0c5bb45963a74d135addfa206e29785c564fc0a61f1a183-99.gpickle", "147798e4306d06a6eea438ec994779677daf4c1c.apk-99.gpickle", "1f56be54a06d20b4f394f4023d9fd6a4c3c443d1.apk-99.gpickle"])
    sim_name_list.extend(["org.expressme.love.ui", "org.expressme.love.ui", "hider.AppInstall.nvanmoshiriji_V31_mumayi_aff08", "hider.AppInstall.nvanmoshiriji_V31_mumayi_aff08"])
    # DroidKungFu 1.2
    file_list.extend(["a8aaacd61dc517bf91a53ba59698c36cb171c49cfdcbea029cfa10484de60be8-dimva2013-99.gpickle", "22f2299b827c261528c10228963beeed781d7b8952e0476e9b68b0376eb82abd-dimva2013-99.gpickle"])
    sim_name_list.extend([ "com.tutusw.fingerscanner", "com.tutusw.fingerscanner"])
    # DroidKungFu 2 only 3 of them. The others exhib other behaviours. We need to retest them
    file_list.extend(["35b223e521abc1cb6b8043f95c2a133c11ed8be4.apk-99.gpickle", "30c7121c1757cc7b2c31b5a9f9a9100f758c0c73.apk-99.gpickle", "27970cd6a9299ed0c34fcb265b372edb9ba772ac.apk-99.gpickle"])
    sim_name_list.extend(["com.allen.txthej", "com.allen.txtdbwshs", "com.alan.translate"])
    # Bad News
    file_list.extend(["../res/graphs/malware-others/badnews/good.digest.diety.apk-99.gpickle", "../res/graphs/malware-others/badnews/good.digest.horrors.apk-99.gpickle", "../res/graphs/malware-others/badnews/live.photo.bigbangtheory.apk-99.gpickle", "../res/graphs/malware-others/badnews/live.photo.savanna.apk-99.gpickle", "../res/graphs/malware-others/badnews/live.photo.sharonstone.apk-99.gpickle"]) 
    sim_name_list.extend(["good.digest.diety", "good.digest.horrors", "live.photo.bigbangtheory", "live.photo.savanna", "live.photo.sharonstone"])

    # List of SFGs of benign applications that we will use to filter edges.  
    file_list2 = ["log/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/com.rovio.angrybirds.ads.apk-99.gpickle","log/com.mozilla.android.apps.firefox.apk-integrity-99.gpickle","log/cellfish.ironman3wp-1.apk-99.gpickle","log/com.g6677.android.ldentist-1.apk-99.gpickle","log/com.industrymagic.crazyjump-1.apk-99.gpickle","log/jackpal.androidterm-1.apk-99.gpickle", "log/stericson.busybox-1.apk-99.gpickle"]
    sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*", "*"]
    #graphs = lsfg.anonymize_graphs([nx.read_gpickle(str("log/" + name)) for name in file_list], sim_name_list)
    graphs = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"droid.gallery")),
            lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"acct/uid/")),
            lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_server")),
            lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")),
            lsfg.load("log/"+name))))) for name in file_list],sim_name_list)
    graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2], sim_name_list2)
    for i in range(len(graphs)) :
        graphs[i].graph["filename"] = os.path.abspath(file_list[i])

    gg_sfg_list = []
    gg_fname_list = []
    gg_app_name_list = []
    for root, dnamelist, fnamelist in os.walk("/tmp/googlePlay/june2013"):
        for fname in fnamelist :
            if (not fname.endswith(".gpickle")):
                continue
            sfg = lsfg.load(os.path.join(root, fname))
            if ((sfg is None) or (len(lsfg.get_edges(sfg)) == 0) or (not sfg.graph.has_key("app_name"))):
                continue
            gg_sfg_list.append(sfg)
            gg_fname_list.append(sfg.graph["filename"])
            gg_app_name_list.append(sfg.graph["app_name"])

    # Max index to which we stop when picking graphs from which we choose SFG
    # from which signatures should be computed
    sep = len(gg_sfg_list) / 3
    
    # Uncomment these two lines and comment the third one if you want to add SFGs to white list
    extgraphs2 = graphs2 + lsfg.anonymize_graphs([gg_sfg_list[i] for i in range(sep)], 
            [gg_app_name_list[j] for j in range(sep)])
    #extgraphs2 = graphs2

    graphs1_1 = lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"droid.gallery")),
            lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"acct/uid/")),
            lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_server")),
            lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")),
            gg_sfg_list[i])))) for i in range(sep, sep * 2)], [gg_app_name_list[j] for j in range(sep, sep * 2)])

    for i in range(sep):
        graphs1_1[i].graph["filename"] = gg_fname_list[i + sep]

    extgraphs1 = graphs + graphs1_1

    sign = lsfg.compute_sign(extgraphs1,extgraphs2,[lambda g: not(lsfg.is_empty(g))])

    i = 0
    for k, v in sign.items() :
        print "Signature " + str(i)
        for g in v :
            print g.graph["filename"]
        i += 1      
    
    #for i in range(len(graphs)):
    #   l = []
    #   for key, val in sign.items() :
    #       if graphs[i] in val:
    #           l.insert(0, key)
    #   print("Graphe " + str(i) + " correspond a " + str(len(l)) + " signatures") 
    #   if (len(l) >= 2):
    #       dot.save_dot_to_file(dot.build_dot_graph(graphs[i]), "graph" + str(i) + ".dot")
    #       
    lsfg.print_sign(sign)
    
    #for sfg_key in sign.keys():
    #   print "\n\n"
    #   print "***"
    #   print "DroidKungFu 1"
    #   sfg_tmp = lsfg.intersection(nx.read_gpickle("log/droidkungfu.apk-dimva2013-99.gpickle"), sfg_key, [("com.aijiaoyou.android.sipphone", "blare-anonym")])
        #        print ("Intersection du graphe avec graphe de taille " + str(len(sfg_key.edges())) + " arcs possede " + str(len(sfg_tmp.edges())) + " arcs")
    #   
    #   print "***"
    #   print "jSMSHider"
    #   sfg_tmp = lsfg.intersection(nx.read_gpickle("log/7678174e22967accc4d6470579dfa8511c37e1c628d08c23b70df7e23703f769-integrity-99.gpickle"), sfg_key, [("org.expressme.love.ui", "blare-anonym")])
    #   print ("Intersection du graphe avec graphe de taille " + str(len(sfg_key.edges())) + " arcs possede " + str(len(sfg_tmp.edges())) + " arcs")

    #   print "***"
    #   print "DroidKungFu 1.2"
        #        sfg_tmp = lsfg.intersection(nx.read_gpickle("log/a8aaacd61dc517bf91a53ba59698c36cb171c49cfdcbea029cfa10484de60be8-dimva2013-99.gpickle"), sfg_key, [("com.tutusw.fingerscanner", "blare-anonym")])
        #        print ("Intersection du graphe avec graphe de taille " + str(len(sfg_key.edges())) + " arcs possede " + str(len(sfg_tmp.edges())) + " arcs")

    #   print "***"
    #   print "DroidKungFu 2"
    #   sfg_tmp = lsfg.intersection(nx.read_gpickle("log/35b223e521abc1cb6b8043f95c2a133c11ed8be4.apk-99.gpickle"), sfg_key, [("com.allen.txthej", "blare-anonym")])
        #        print ("Intersection du graphe avec graphe de taille " + str(len(sfg_key.edges())) + " arcs possede " + str(len(sfg_tmp.edges())) + " arcs")

    #   print "***"
    #   print "Bad News"
    #   sfg_tmp = lsfg.intersection(nx.read_gpickle("log/good.digest.diety.apk-99.gpickle"), sfg_key, [("good.digest.diety", "blare-anonym")])
    #   print ("Intersection du graphe avec graphe de taille " + str(len(sfg_key.edges())) + " arcs possede " + str(len(sfg_tmp.edges())) + " arcs")

#test_gen_sign()

def test_is_equal():
    g=nx.read_gpickle("log/droidkungfu.apk-dimva2013-99.gpickle")
    g2=nx.read_gpickle("log/droidkungfu.apk-dimva2013-99.gpickle")
    print("test de is_equal")
    print(lsfg.is_equal(g,g2))
    #test_is_equal()


def test_inter () :
    file_list = [ "droidkungfu.apk-dimva2013-99.gpickle", "sample2.apk-dimva2013-99.gpickle", "20595020c2033e4f7221b08e4ed6934f59a0d778.apk-dimva2013-99.gpickle"]
    sim_name_list = ["com.aijiaoyou.android.sipphone", "com.sansec", "com.tutusw.phonespeedup"]

    graphs = lsfg.anonymize_graphs([nx.read_gpickle("log/"+name) for name in file_list],sim_name_list)

    print(lsfg.is_equal (lsfg.mult_intersection([graphs[0], graphs[1],graphs[2]],["","",""]),lsfg.mult_intersection([graphs[1], graphs[2],graphs[0]],["","",""])))
    print(lsfg.is_equal (lsfg.mult_intersection([graphs[0], graphs[1],graphs[2]],["","",""]),lsfg.mult_intersection([graphs[2], graphs[0],graphs[1]],["","",""])))
    print(lsfg.is_equal (lsfg.mult_intersection([graphs[0], graphs[1],graphs[2]],["","",""]),lsfg.mult_intersection([graphs[0], graphs[2],graphs[1]],["","",""])))
    g0=graphs[0]
    g1=graphs[1]
    g2=graphs[2]
    
    g012=lsfg.mult_intersection([graphs[0], graphs[1],graphs[2]],["","",""])
    g012manuel=lsfg.intersection(lsfg.intersection(g0,g1,[("","")]),g2,[("","")] )
    g120manuel=lsfg.intersection(lsfg.intersection(g1,g2,[("","")]),g0,[("","")] )
    g210=lsfg.mult_intersection([graphs[2], graphs[1],graphs[0]],["","",""])
    print("le calcul des intersections donne deux mm graph ? g012 -g012manuel ")
    print(lsfg.is_equal (g012,g012manuel))
    print("le calcul des intersections donne deux mm graph ? g210 -g012manuel ")
    print(lsfg.is_equal (g210,g012manuel))
    print("le calcul des intersections donne deux mm graph ? g120manuel -g012manuel ")
    print(lsfg.is_equal (g120manuel,g012manuel))
    print("g120")
    print(g120manuel.edges())
    print("g012")
    print(g012manuel.edges())
    print("g120 -g012")
    print(lsfg.minus(g120manuel,g012manuel,[("","")]))
    print("g012 -g120")
    print(lsfg.minus(g012manuel,g120manuel,[("","")]))
    
    print("g012 a "+str(len(g012.edges()))+" arcs")
    print("g210 a "+str(len(g210.edges()))+" arcs")
    g0=graphs[0]
    g1=graphs[1]
    g2=graphs[2]
    for a in g012.edges() :
        try: print(g210.edges().index(a))
        except ValueError:
            print("a not found dans g210")
            print(a)
            print(g210.edges())
            print("a trouve dans g0 ?")
            print(g0.edges().index(a))
            print("a trouve dans g1 ?")
            print(g1.edges().index(a))
            print("a trouve dans g2 ?")
            print(g2.edges().index(a))
            break

# Test pour Raid 2014
def cleansfg():
    file_list2 = ["log/mobi.thinkchange.fingerscannerlite-1.apk-99.gpickle", "log/com.rovio.angrybirds.ads.apk-99.gpickle","log/com.mozilla.android.apps.firefox.apk-integrity-99.gpickle","log/cellfish.ironman3wp-1.apk-99.gpickle","log/com.g6677.android.ldentist-1.apk-99.gpickle","log/com.industrymagic.crazyjump-1.apk-99.gpickle","log/jackpal.androidterm-1.apk-99.gpickle", "log/stericson.busybox-1.apk-99.gpickle"]
    sim_name_list2 = ["mobi.thinkchange.fingerscannerlite", "com.rovio.angrybirdsspace.ads", "tp5x.WGt12", "cellfish.ironman3wp", "com.g6677.android.ldentist","com.industrymagic.crazyjump","*", "*"]
    graphs2 = lsfg.anonymize_graphs([nx.read_gpickle(name) for name in file_list2], sim_name_list2)
    # 2 x DroidKungFu 1, 1 x DroidKungFu 1.2, 2 x jSMSHider, 2 x BadNews, 2 x DroidKungFu2
    file_list = ["droidkungfu.apk-dimva2013-99.gpickle",  "sample2.apk-dimva2013-99.gpickle", "a8aaacd61dc517bf91a53ba59698c36cb171c49cfdcbea029cfa10484de60be8-dimva2013-99.gpickle", "7678174e22967accc4d6470579dfa8511c37e1c628d08c23b70df7e23703f769-99.gpickle", "1c29b3010a2e50bca0c5bb45963a74d135addfa206e29785c564fc0a61f1a183-99.gpickle", "/good.digest.diety.apk-99.gpickle", "live.photo.savanna.apk-99.gpickle", "35b223e521abc1cb6b8043f95c2a133c11ed8be4.apk-99.gpickle", "30c7121c1757cc7b2c31b5a9f9a9100f758c0c73.apk-99.gpickle",]
    sim_name_list = ["com.aijiaoyou.android.sipphone", "com.sansec",  "com.tutusw.fingerscanner", "org.expressme.love.ui", "org.expressme.love.ui", "good.digest.diety", "live.photo.savanna", "com.allen.txthej", "com.allen.txtdbwshs"]
    graphs =  lsfg.anonymize_graphs([lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"droid.gallery")), lsfg.filter_edges(lambda e :not(lsfg.edges_name_contains(e,"acct/uid/")), lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"system_server")), lsfg.filter_edges(lambda e :not( lsfg.edges_name_contains(e,"ufou.android.su")), lsfg.load("log/"+name))))) for name in file_list],sim_name_list)
    res = []
    for i in range(len(graphs)):
        res.append(lsfg.mult_minus(([graphs[i]] + graphs2) , ([sim_name_list[i]] + sim_name_list2)))
    i = 0
    for elt in res:
        print("Save filtered graph " + str(i) + "\n")
        dot.save_dot_to_file(dot.build_dot_graph(elt), ("filtered_sfg"+str(i)+".dot"))
        i += 1

cleansfg()






