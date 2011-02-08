#!/usr/bin/env python
# Richard Darst, March 2009

import os
import re
import sys

sys.path.insert(0, 'mobwrite/tools')
import mobwritelib
del sys.path[0]

# Relative URL to the sync gateway.
#syncGateway_ = "mobwrite.syncGateway='q.py.mpy';\n"
syncGateway_ = "mobwrite.syncGateway='q.py.cgi';\n"
syncServerGateway = 'telnet://localhost:30711'
# additional banner at the bottom.  It is HTML.  Edit to your desires.
pageNews_ = "(updated every minute, no js)"

class WhiteboardPage(object):
    template_wb = 'wb.html.template'

    def __init__(self, id):
        self.id = id
    def __getitem__(self, key):
        """Mapping (dictionary) interface"""
        # This is needed so that template % self will work
        return getattr(self, key)
    @property
    def mobID(self):
        """The mobwrite ID, which is the text area ID"""
        return 'wb_' + self.id
    @property
    def staticLink(self):
        """URL to link for for .txt copy"""
        return self.id + '.txt'
    syncGateway = syncGateway_
    pageNews = pageNews_
    encoding = "utf-8"
    @property
    def raw_text(self):
        """Raw text as retrieved by the server."""
        return mobwritelib.download(syncServerGateway,[self.mobID])[self.mobID]
    @property
    def raw_text2(self):
        """Raw text as retrieved from the filesystem"""
        return open(self._filename).read()
    @property
    def _filename(self):
        """Filename of storage on the filesystem"""
        return "data/wb_" + self.id + ".txt"
    def exists(self):
        """Return True if this whiteboard id already"""
        if os.access(self._filename, os.F_OK):
            return True
        return False

    # Render methods for various outputs.  $id.$ext -> ext_$ext()
    def ext_wb(self):
        """The editable whiteboard form"""
        header = "Content-Type: text/html; charset=%s\n\n"%self.encoding
        page = open(self.template_wb).read()
        page = page%self
        return header + page
    def ext_txt(self, wrap=False):
        """Raw text contained in this whiteboard, text/plain"""
        text = self.raw_text
        header = "Content-Type: text/plain; charset=%s\n\n"%self.encoding
        # Wrap text?
        if wrap:
            if isinstance(wrap, int): width = wrap
            else:                     width = 72
            newText = []
            import textwrap
            for line in text.split("\n"):
                newText.append(textwrap.fill(line, width=width))
            text = "\n".join(newText)
        return header + text.encode('utf-8')
    def ext_textile(self):
        """Render the whiteboard using textile."""
        header = "Content-Type: text/html; charset=%s\n\n"%self.encoding
        import textile
        text = self.raw_text
        text = text.encode('utf-8')
        text = textile.textile(text, sanitize=True, encoding='utf-8')
        return header + text
    def ext_rst(self):
        """Render the whiteboard using ReStructuredText"""
        header = "Content-Type: text/html; charset=%s\n\n"%self.encoding
        from docutils.core import publish_string
        text = self.raw_text
#        text = text.encode('utf-8', 'replace')
        text = publish_string(
            source=text,
            settings_overrides={'file_insertion_enabled': 0,
                                'raw_enabled': 0,
                                #'output_encoding':'utf-8',
                                },
            writer_name='html')
#        text = text.encode('utf-8', 'replace')
        return header + text
    def ext_rawtxt(self):
        header = "Content-Type: text/plain; charset=%s\n\n"%self.encoding
        text = self.raw_text
        text = text.encode('utf-8', 'replace')
        return header + text
    def ext_rawtxt2(self):
        header = "Content-Type: text/plain; charset=%s\n\n"%self.encoding
        text = self.raw_text2
        return header + text



def randompageRedirect(data):
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
            if not WhitboardPage(id=wbName).exists():
                break
    urlName = wbName + ".wb"
    response = ["303 See Other:",
                "Location: "+urlName,
                "Content-Type: text/html",
                "",
                "Your new page is at "+urlName,
                ]
    response = "\n".join(response)
    return response




import cgi
import cgitb ; cgitb.enable()
data = cgi.FieldStorage()

# If asking for a new page, do that redirect
if data.getfirst("new"):
    print randompageRedirect(data)
    sys.exit(0)

pageName = os.environ["REQUEST_URI"]
m = re.match("/([a-zA-z0-9._+=-]+)\.([a-zA-Z0-9]+)", pageName)

# Handle bad URLs
if not m:
    print "Content-Type: text/plain"
    print
    print dir(data)
    print data.file
    print os.path.basename(pageName)
    print "Greetings, Utahraptor."

id_ = m.group(1)
ext = m.group(2)
if hasattr(WhiteboardPage, 'ext_'+ext):
    wbp = WhiteboardPage(id_)
    print getattr(wbp, 'ext_'+ext)()
elif data.getfirst('markup') == "rst":
    print WhiteboardPage(id_).rst()
elif data.getfirst('markup'):
    print WhiteboardPage(id_).textile()
else:
    print 'x'
