def eventlet_patcher():
    # Ref: https://github.com/eventlet/eventlet/pull/467
    # Ref: https://github.com/eventlet/eventlet/issues/468
    from eventlet.wsgi import HttpProtocol

    def new_get_environ(self):
        env = self.server.get_environ()
        env['REQUEST_METHOD'] = self.command
        env['SCRIPT_NAME'] = ''

        pq = self.path.split('?', 1)
        env['RAW_PATH_INFO'] = pq[0]
        import urllib
        # Patch start
        env['PATH_INFO'] = urllib.parse.unquote(pq[0]).encode().decode('latin-1')
        # Patch end
        if len(pq) > 1:
            env['QUERY_STRING'] = pq[1]

        ct = self.headers.get('content-type')
        if ct is None:
            try:
                ct = self.headers.type
            except AttributeError:
                ct = self.headers.get_content_type()
        env['CONTENT_TYPE'] = ct

        length = self.headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        env['SERVER_PROTOCOL'] = 'HTTP/1.0'

        from eventlet.wsgi import addr_to_host_port
        sockname = self.request.getsockname()
        server_addr = addr_to_host_port(sockname)
        env['SERVER_NAME'] = server_addr[0]
        env['SERVER_PORT'] = str(server_addr[1])

        client_addr = addr_to_host_port(self.client_address)
        env['REMOTE_ADDR'] = client_addr[0]
        env['REMOTE_PORT'] = str(client_addr[1])
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'

        try:
            headers = self.headers.headers
        except AttributeError:
            headers = self.headers._headers
        else:
            headers = [h.split(':', 1) for h in headers]

        env['headers_raw'] = headers_raw = tuple((k, v.strip()) for k, v in headers)
        for k, v in headers_raw:
            k = k.replace('-', '_').upper()
            if k in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                # These do not get the HTTP_ prefix and were handled above
                continue
            envk = 'HTTP_' + k
            if envk in env:
                env[envk] += ',' + v
            else:
                env[envk] = v

        if env.get('HTTP_EXPECT') == '100-continue':
            wfile = self.wfile
            wfile_line = b'HTTP/1.1 100 Continue\r\n'
        else:
            wfile = None
            wfile_line = None
        chunked = env.get('HTTP_TRANSFER_ENCODING', '').lower() == 'chunked'
        from eventlet.wsgi import Input
        env['wsgi.input'] = env['eventlet.input'] = Input(
            self.rfile, length, self.connection, wfile=wfile, wfile_line=wfile_line,
            chunked_input=chunked)
        env['eventlet.posthooks'] = []

        return env

    HttpProtocol.get_environ = new_get_environ