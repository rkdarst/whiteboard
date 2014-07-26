#!/usr/bin/env python
# Richard Darst, March 2009

import os
import re
import sys

sys.path.insert(0, 'mobwrite/tools')
import mobwritelib
del sys.path[0]


class WhiteboardPage(object):
    encoding = "utf-8"
    template_wb = 'wb.html.template'
    template_options = 'options.html.template'
    # Relative URL to the sync gateway.
    syncGateway = "mobwrite.syncGateway='q.py.mpy';\n"
    #syncGateway = "mobwrite.syncGateway='q.py.cgi';\n"
    syncServerGateway = 'telnet://localhost:30712'
    # additional banner at the bottom.  It is HTML.  Edit to your desires.
    pageNews = ""

    def __init__(self, id, options=None):
        self.id = id
        self.options = options
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
    @property
    def textarea_style(self):
        style = "height:95%"
        if hasattr(self, 'options') and self.options.getfirst('cols'):
            try:
                cols = int(self.options.getfirst('cols'))
                return 'style="height: 95%%" cols="%d"'%cols
            except ValueError:
                pass
        return 'style="width: 100%; height:95%"'
    @property
    def raw_text(self):
        """Raw text as retrieved by the server."""
        return mobwritelib.download(self.syncServerGateway,[self.mobID])[self.mobID]
    @property
    def raw_text2(self):
        """Raw text as retrieved from the filesystem"""
        return open(self._filename).read()
    @property
    def _filename(self):
        """Filename of storage on the filesystem"""
        return "data/wb_" + self.id + ".txt"
    @property
    def wordcounts(self):
        data = self.raw_text
        chars = len(data)
        words = len(data.split())
        lines = len(data.split("\n"))
        return "%d %d %d"%(chars, words, lines)
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
    def ext_opts(self):
        """Controllable whiteboard options"""
        header = "Content-Type: text/html; charset=%s\n\n"%self.encoding
        page = open(self.template_options).read()
        page = page%self
        return header + page
    def ext_txt(self):
        """Raw text contained in this whiteboard, text/plain"""
        text = self.raw_text
        header = "Content-Type: text/plain; charset=%s\n\n"%self.encoding
        # Wrap text?
        if hasattr(self, 'options') and self.options.getfirst('wrap'):
            wrap = self.options.getfirst('wrap')
            try:
                width = int(wrap)
            except ValueError:
                width = 72
            newText = []
            import textwrap
            for line in text.split("\n"):
                newText.append(textwrap.fill(line, width=width))
            text = "\n".join(newText)
        return header + text.encode('utf-8')
    ext_txt2 = ext_txt
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
    def ext_md(self):
        header = "Content-Type: text/html; charset=%s\n\n"%self.encoding
        import markdown
        text = self.raw_text
        #text = self.raw_text2
        #text = text.decode('utf-8', 'replace')
        html = markdown.markdown(text, safe_mode="escape")
        html = html.encode('utf-8', 'replace')
        return header + html
    def ext_rawtxt(self):
        header = "Content-Type: text/plain; charset=%s\n\n"%self.encoding
        text = self.raw_text
        text = text.encode('utf-8', 'replace')
        return header + text
    def ext_rawtxt2(self):
        header = "Content-Type: text/plain; charset=%s\n\n"%self.encoding
        text = self.raw_text2
#        text = text.encode('utf-8', 'replace')
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
            if not WhiteboardPage(id=wbName).exists():
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
m = re.match("^.*/([a-zA-z0-9._+=-]+)\.([a-zA-Z0-9]+)", pageName)

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
    wbp = WhiteboardPage(id_, options=data)
    print getattr(wbp, 'ext_'+ext)()
elif data.getfirst('markup') == "rst":
    print WhiteboardPage(id_, options=data).rst()
elif data.getfirst('markup'):
    print WhiteboardPage(id_, options=data).textile()
else:
    print 'x'
