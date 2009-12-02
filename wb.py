#!/usr/bin/env python
# Richard Darst, March 2009

import cgi
import cgitb ; cgitb.enable()
data = cgi.FieldStorage()
import os
import sys

# Relative URL to the sync gateway.
syncGateway_ = "mobwrite.syncGateway='q.py.mpy';\n"
#syncGateway_ = "mobwrite.syncGateway='q.py.cgi';\n"
# additional banner at the bottom.  It is HTML.  Edit to your desires.
pageNews_ = "(updated every minute, no js)"

def do_whiteboard(pageName):
    print "Content-Type: text/html"
    print
    textareaID = 'wb_' + os.path.basename(pageName)
    shortname = os.path.basename(pageName)
    staticLink = pageName+'.txt'
    #print textareaID
    page = file('wb.html.template').read()

    syncGateway = syncGateway_  # needs to be a local variable!
    pageNews = pageNews_
    page = page%locals()
    print page



if data.getfirst("new"):
    import random

    exactName = data.getfirst("exactname")
    if exactName:
        wbName = exactName
    else:
        prefix = data.getfirst("prefix")
        while True:
            wbName = hex(int(random.uniform(0, 16**6)))[2:]
            if prefix:
                wbName = prefix + "_" + wbName
            fileName = "data/wb_" + wbName + ".wb"
            if not os.access(fileName, os.F_OK):
                break
    urlName = wbName + ".wb"
    print "303 See Other:"
    print "Location:", urlName
    print "Content-Type: text/html"
    print
    print "Your new page is at", urlName
    sys.exit()


pageName = os.environ["REQUEST_URI"]
if pageName[-3:] == ".wb":
    pageName = pageName[:-3]
    do_whiteboard(pageName)
else:
    print "Content-Type: text/plain"
    print
    print dir(data)
    print data.file
    print os.path.basename(pageName)
    print "Greetings, Utahraptor."
