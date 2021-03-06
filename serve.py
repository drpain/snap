#!/usr/bin/env python
import SocketServer, SimpleHTTPServer, subprocess, os
from urlparse import urlparse, parse_qsl

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Start the SimpleHTTPServer up and look for actions, otherwise server the remote page
class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        GET = parse_qsl(urlparse(self.path)[4])
        if self.path.find("?") > 0:
            response = 200
            output = 0
            self.send_response(response)
            self.send_header('Content-type','text/html')
            self.send_header('Content-length', len(str(output)))
            self.end_headers()
            self.wfile.write(output)
            return

        else:
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self) #dir listing

def StartServer(PORT=5000):
    try:
        httpd = SocketServer.ThreadingTCPServer(('127.0.0.1', PORT),CustomHandler)
        print '\n\nStarting server on PORT:' + str(PORT) + ', use <Ctrl-C> to stop\n\n'
        httpd.serve_forever()
    except KeyboardInterrupt:
        print " pressed. Shutting down server, please wait..."
        httpd.shutdown()
        exit()
