import time

""" Use this module to measure the execution time for a method,
by putting @module.chronomethod before """

measuredMethods = {} # Dictionary of monitored methods
ENABLED = False # The module can be disabled

def chronomethod(method):
    global measuredMethods
    global ENABLED
    if ENABLED:
        # First  : nb of calls
        # Second : total execution time
        measuredMethods[method] = (0,0)

        def timed(*args,**kw):
            global measuredMethods

            ts = time.time()
            r = method(*args,**kw)
            te = time.time()

            c = measuredMethods[method]
            measuredMethods[method] = ( c[0]+1, c[1]+te-ts )

            return r

        return timed
    else:
        return method

def printMeasuredMethods():
    """ Print the execution time for all monitored method, and the number of calls """
    global measuredMethods
    global ENABLED
    if ENABLED:
        l = sorted(measuredMethods.items(), key = lambda i: i[1][1], reverse=True)
        print( (25*" ") + " --- Execution time per method --- " )
        for f,t in l:
            print( "{:65}".format(str(f)) + " : "
                    + "{:>4}".format(str(t[0])) + " calls, "
                    + str(t[1]) + "s" )
