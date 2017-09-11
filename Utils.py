from datetime import datetime

# Gray, Red, Green, Yellow, Blue, Magenta, Cyan, White, Crimson
colorIndex = [ "30", "31", "32", "33", "34", "35", "36", "37", "38" ]


def prettyPrint(msg, mode="info"):
    """ Pretty prints a colored message. "info": Green, "error": Red, "warning": Yellow, "info2": Blue, "output": Magenta, "debug": White """
    if mode == "info":
        color = "32" # Green
    elif mode == "error":
        color = "31" # Red
    elif mode == "warning":
        color = "33" # Yellow
    elif mode == "info2":
        color = "34" # Blue
    elif mode == "output":
        color = "35" # Magenta
    elif mode == "debug":
        color = "37" # White
    else:
        color = "32"
    msg = "[*] %s." % msg#, getTimestamp()
    #print("\033[1;%sm%s\n%s\033[1;m" % (color, msg, '-'*len(msg))) # Print dashes under the message
    print("\033[1;%sm%s\033[1;m" % (color, msg))

def getTimestamp(includeDate=True):
    if includeDate:
        return "[%s]"%str(datetime.now())
    else:
        return "[%s]"%str(datetime.now()).split(" ")[1]