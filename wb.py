#!/usr/bin/env python
# Richard Darst, March 2009

import cgi
import cgitb ; cgitb.enable()
data = cgi.FieldStorage()
import os
import re
import sys

#syncGateway_ = ""
syncGateway_ = "mobwrite.syncGateway='http://wb2.zgib.net:16546/q.py.mpy';\n"
# additional banner at the bottom.  Can use html codes.
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

def do_statictext(pageName):
#    text = open("data/wb_%s.txt"%pageName).read()
    text = mobwritelib.download(syncServerGateway, ['wb_'+pageName])['wb_'+pageName]
    if data.getfirst('wrap'):
        print "Content-Type: text/plain"
        print
        width = 72
        try:
            width = int(data.getfirst('wrap'))
        except ValueError:
            pass
        newText = []
        import textwrap
        for line in text.split("\n"):
            newText.append(textwrap.fill(line, width=width))
        text = "\n".join(newText)
        print text
    elif data.getfirst('markup'):
        print "Content-Type: text/html"
        print
        import textile
        print type(text)
        text = text.encode('utf-8')
        text = textile.textile(text, sanitize=True)
        print text
    else:
        print "Content-Type: text/plain"
        print
        print text


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
m_txt = re.match("/([a-zA-z0-9._+=-]+)\.txt", pageName)
if pageName[-3:] == ".wb":
    pageName = pageName[:-3]
    do_whiteboard(pageName)
elif m_txt:
    pageName = m_txt.group(1)
    do_statictext(pageName)
else:
    print "Content-Type: text/plain"
    print
    print dir(data)
    print data.file
    print os.path.basename(pageName)
    print "Greetings, Utahraptor."
