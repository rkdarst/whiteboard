import BaseHTTPServer
import CGIHTTPServer
#server = 

import CGIHTTPServer
for name in dir(CGIHTTPServer):
    globals()[name] = getattr(CGIHTTPServer, name)

import re

class server(CGIHTTPServer.CGIHTTPRequestHandler, object):

    def rewrite_url(self):
        self.oldpath = self.path
        self.path = re.sub(r'^/test$',
                           r'/test.sh',                    self.path)
        self.path = re.sub(r'^/[a-zA-Z0-9._+=-]+\.wb$',
                           r'/wb.py.cgi',                  self.path)
        self.path = re.sub(r'^/([a-zA-Z0-9._+=-]+)\.txt$',
                           r'/data/wb_\1.txt',             self.path)
        self.path = re.sub(r'^/sync$',
                           r'/q.py.cgi',                   self.path)
        print self.path, self.oldpath
        
    def do_POST(self):
        self.rewrite_url()
        super(server, self).do_POST()

    def do_GET(self):
        self.rewrite_url()
        super(server, self).do_GET()


    # The only thing added below is:
    # env['REQUEST_URI'] = self.oldpath
    def run_cgi(self):
        """Execute a CGI script."""
        path = self.path
        dir, rest = self.cgi_info

        i = path.find('/', len(dir) + 1)
        while i >= 0:
            nextdir = path[:i]
            nextrest = path[i+1:]

            scriptdir = self.translate_path(nextdir)
            if os.path.isdir(scriptdir):
                dir, rest = nextdir, nextrest
                i = path.find('/', len(dir) + 1)
            else:
                break

        # find an explicit query string, if present.
        i = rest.rfind('?')
        if i >= 0:
            rest, query = rest[:i], rest[i+1:]
        else:
            query = ''

        # dissect the part after the directory name into a script name &
        # a possible additional path, to be stored in PATH_INFO.
        i = rest.find('/')
        if i >= 0:
            script, rest = rest[:i], rest[i:]
        else:
            script, rest = rest, ''

        scriptname = dir + '/' + script
        scriptfile = self.translate_path(scriptname)
        if not os.path.exists(scriptfile):
            self.send_error(404, "No such CGI script (%r)" % scriptname)
            return
        if not os.path.isfile(scriptfile):
            self.send_error(403, "CGI script is not a plain file (%r)" %
                            scriptname)
            return
        ispy = self.is_python(scriptname)
        if not ispy:
            if not (self.have_fork or self.have_popen2 or self.have_popen3):
                self.send_error(403, "CGI script is not a Python script (%r)" %
                                scriptname)
                return
            if not self.is_executable(scriptfile):
                self.send_error(403, "CGI script is not executable (%r)" %
                                scriptname)
                return

        # Reference: http://hoohoo.ncsa.uiuc.edu/cgi/env.html
        # XXX Much of the following could be prepared ahead of time!
        env = {}
        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        uqrest = urllib.unquote(rest)
        env['REQUEST_URI'] = self.oldpath
        env['PATH_INFO'] = uqrest
        env['PATH_TRANSLATED'] = self.translate_path(uqrest)
        env['SCRIPT_NAME'] = scriptname
        if query:
            env['QUERY_STRING'] = query
        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]
        authorization = self.headers.getheader("authorization")
        if authorization:
            authorization = authorization.split()
            if len(authorization) == 2:
                import base64, binascii
                env['AUTH_TYPE'] = authorization[0]
                if authorization[0].lower() == "basic":
                    try:
                        authorization = base64.decodestring(authorization[1])
                    except binascii.Error:
                        pass
                    else:
                        authorization = authorization.split(':')
                        if len(authorization) == 2:
                            env['REMOTE_USER'] = authorization[0]
        # XXX REMOTE_IDENT
        if self.headers.typeheader is None:
            env['CONTENT_TYPE'] = self.headers.type
        else:
            env['CONTENT_TYPE'] = self.headers.typeheader
        length = self.headers.getheader('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        accept = []
        for line in self.headers.getallmatchingheaders('accept'):
            if line[:1] in "\t\n\r ":
                accept.append(line.strip())
            else:
                accept = accept + line[7:].split(',')
        env['HTTP_ACCEPT'] = ','.join(accept)
        ua = self.headers.getheader('user-agent')
        if ua:
            env['HTTP_USER_AGENT'] = ua
        co = filter(None, self.headers.getheaders('cookie'))
        if co:
            env['HTTP_COOKIE'] = ', '.join(co)
        # XXX Other HTTP_* headers
        # Since we're setting the env in the parent, provide empty
        # values to override previously set values
        for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH',
                  'HTTP_USER_AGENT', 'HTTP_COOKIE'):
            env.setdefault(k, "")
        os.environ.update(env)

        self.send_response(200, "Script output follows")

        decoded_query = query.replace('+', ' ')

        if self.have_fork:
            # Unix -- fork as we should
            args = [script]
            if '=' not in decoded_query:
                args.append(decoded_query)
            nobody = nobody_uid()
            self.wfile.flush() # Always flush before forking
            pid = os.fork()
            if pid != 0:
                # Parent
                pid, sts = os.waitpid(pid, 0)
                # throw away additional data [see bug #427345]
                while select.select([self.rfile], [], [], 0)[0]:
                    if not self.rfile.read(1):
                        break
                if sts:
                    self.log_error("CGI script exit status %#x", sts)
                return
            # Child
            try:
                try:
                    os.setuid(nobody)
                except os.error:
                    pass
                os.dup2(self.rfile.fileno(), 0)
                os.dup2(self.wfile.fileno(), 1)
                os.execve(scriptfile, args, os.environ)
            except:
                self.server.handle_error(self.request, self.client_address)
                os._exit(127)

        elif self.have_popen2 or self.have_popen3:
            # Windows -- use popen2 or popen3 to create a subprocess
            import shutil
            if self.have_popen3:
                popenx = os.popen3
            else:
                popenx = os.popen2
            cmdline = scriptfile
            if self.is_python(scriptfile):
                interp = sys.executable
                if interp.lower().endswith("w.exe"):
                    # On Windows, use python.exe, not pythonw.exe
                    interp = interp[:-5] + interp[-4:]
                cmdline = "%s -u %s" % (interp, cmdline)
            if '=' not in query and '"' not in query:
                cmdline = '%s "%s"' % (cmdline, query)
            self.log_message("command: %s", cmdline)
            try:
                nbytes = int(length)
            except (TypeError, ValueError):
                nbytes = 0
            files = popenx(cmdline, 'b')
            fi = files[0]
            fo = files[1]
            if self.have_popen3:
                fe = files[2]
            if self.command.lower() == "post" and nbytes > 0:
                data = self.rfile.read(nbytes)
                fi.write(data)
            # throw away additional data [see bug #427345]
            while select.select([self.rfile._sock], [], [], 0)[0]:
                if not self.rfile._sock.recv(1):
                    break
            fi.close()
            shutil.copyfileobj(fo, self.wfile)
            if self.have_popen3:
                errors = fe.read()
                fe.close()
                if errors:
                    self.log_error('%s', errors)
            sts = fo.close()
            if sts:
                self.log_error("CGI script exit status %#x", sts)
            else:
                self.log_message("CGI script exited OK")

        else:
            # Other O.S. -- execute script in this process
            save_argv = sys.argv
            save_stdin = sys.stdin
            save_stdout = sys.stdout
            save_stderr = sys.stderr
            try:
                save_cwd = os.getcwd()
                try:
                    sys.argv = [scriptfile]
                    if '=' not in decoded_query:
                        sys.argv.append(decoded_query)
                    sys.stdout = self.wfile
                    sys.stdin = self.rfile
                    execfile(scriptfile, {"__name__": "__main__"})
                finally:
                    sys.argv = save_argv
                    sys.stdin = save_stdin
                    sys.stdout = save_stdout
                    sys.stderr = save_stderr
                    os.chdir(save_cwd)
            except SystemExit, sts:
                self.log_error("CGI script exit status %s", str(sts))
            else:
                self.log_message("CGI script exited OK")




server.cgi_directories = ['/test.sh', '/wb.py.cgi', '/q.py.cgi']
#print server.cgi_directories
#for k,v in server.extensions_map.items():
#    print k, v
server.extensions_map[''] = 'text/plain'
server.extensions_map['.sh'] = 'text/plain'
server.extensions_map['.py'] = 'text/plain'

httpd = BaseHTTPServer.HTTPServer(('',8000),
                          server)
httpd.serve_forever()
