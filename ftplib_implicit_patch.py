from ftplib import FTP_TLS, CRLF
import socket

try:
    import ssl
except ImportError:
    _SSLSocket = None
else:
    _SSLSocket = ssl.SSLSocket

class ImplicitFTP_TLS(FTP_TLS):
    def __init__(self,
               host='',
               user='',
               passwd='',
               acct='',
               keyfile=None,
               certfile=None,
               timeout=60):

        FTP_TLS.__init__(self,
                            host=host,
                            user=user,
                            passwd=passwd,
                            acct=acct,
                            keyfile=keyfile,
                            certfile=certfile,
                            timeout=timeout)

    def connect(self, host='', port=0, timeout=-999):
        """Connect to host.  Arguments are:
        - host: hostname to connect to (string, default previous host)
        - port: port to connect to (integer, default previous port)
        """
        if host != '':
            self.host = host
        if port > 0:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        try:
            self.sock = socket.create_connection((self.host, self.port), self.timeout)
            self.af = self.sock.family
            # add this line!!!
            self.sock = ssl.wrap_socket(self.sock,
                                        self.keyfile,
                                        self.certfile,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
            # add end
            self.file = self.sock.makefile('rb')
            self.welcome = self.getresp()
        except Exception as e:
            print(e)
        return self.welcome

    # Internal: return one line from the server, stripping CRLF.
    # Raise EOFError if the connection is closed
    def getline(self):
        line = self.file.readline(self.maxline + 1)

        #Convert to string if encoded
        try:
            line = line.decode('utf-8')
        except:
            pass

        if len(line) > self.maxline:
            raise Error("got more than %d bytes" % self.maxline)
        if self.debugging > 1:
            print('*get*', self.sanitize(line))
        if not line:
            raise EOFError
        if line[-2:] == CRLF:
            line = line[:-2]
        elif line[-1:] in CRLF:
            line = line[:-1]
        return line

    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
        """Store a file in binary mode.  A new port is created for you.

        Args:
          cmd: A STOR command.
          fp: A file-like object with a read(num_bytes) method.
          blocksize: The maximum data size to read from fp and send over
                     the connection at once.  [default: 8192]
          callback: An optional single parameter callable that is called on
                    each block of data after it is sent.  [default: None]
          rest: Passed to transfercmd().  [default: None]

        Returns:
          The response code.
        """
        self.voidcmd('TYPE I')
        with self.transfercmd(cmd, rest) as conn:
            while 1:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)
            # shutdown ssl layer
            if _SSLSocket is not None and isinstance(conn, _SSLSocket):
                #Avoid failure due to OSError
                try:
                    conn.unwrap()
                except OSError:
                    pass
        return self.voidresp()

    def storlines(self, cmd, fp, callback=None):
        """Store a file in line mode.  A new port is created for you.

        Args:
          cmd: A STOR command.
          fp: A file-like object with a readline() method.
          callback: An optional single parameter callable that is called on
                    each line after it is sent.  [default: None]

        Returns:
          The response code.
        """
        self.voidcmd('TYPE A')
        with self.transfercmd(cmd) as conn:
            while 1:
                buf = fp.readline(self.maxline + 1)
                if len(buf) > self.maxline:
                    raise Error("got more than %d bytes" % self.maxline)
                if not buf:
                    break
                if buf[-2:] != B_CRLF:
                    if buf[-1] in B_CRLF: buf = buf[:-1]
                    buf = buf + B_CRLF
                conn.sendall(buf)
                if callback:
                    callback(buf)
            # shutdown ssl layer
            if _SSLSocket is not None and isinstance(conn, _SSLSocket):
                #Avoid failure due to OSError
                try:
                    conn.unwrap()
                except OSError:
                    pass
        return self.voidresp()

    def retrbinary(self, cmd, callback, blocksize=8192, rest=None):
        """Retrieve data in binary mode.  A new port is created for you.

        Args:
          cmd: A RETR command.
          callback: A single parameter callable to be called on each
                    block of data read.
          blocksize: The maximum number of bytes to read from the
                     socket at one time.  [default: 8192]
          rest: Passed to transfercmd().  [default: None]

        Returns:
          The response code.
        """
        self.voidcmd('TYPE I')
        with self.transfercmd(cmd, rest) as conn:
            while 1:
                data = conn.recv(blocksize)
                if not data:
                    break
                callback(data)
            # shutdown ssl layer
            if _SSLSocket is not None and isinstance(conn, _SSLSocket):
                #Avoid failure due to OSError
                try:
                    conn.unwrap()
                except OSError:
                    pass
        return self.voidresp()

    def retrlines(self, cmd, callback = None):
        """Retrieve data in line mode.  A new port is created for you.

        Args:
          cmd: A RETR, LIST, or NLST command.
          callback: An optional single parameter callable that is called
                    for each line with the trailing CRLF stripped.
                    [default: print_line()]

        Returns:
          The response code.
        """
        if callback is None:
            callback = print_line
        resp = self.sendcmd('TYPE A')
        with self.transfercmd(cmd) as conn, \
                 conn.makefile('r', encoding=self.encoding) as fp:
            while 1:
                line = fp.readline(self.maxline + 1)
                if len(line) > self.maxline:
                    raise Error("got more than %d bytes" % self.maxline)
                if self.debugging > 2:
                    print('*retr*', repr(line))
                if not line:
                    break
                if line[-2:] == CRLF:
                    line = line[:-2]
                elif line[-1:] == '\n':
                    line = line[:-1]
                callback(line)
            # shutdown ssl layer
            if _SSLSocket is not None and isinstance(conn, _SSLSocket):
                #Avoid failure due to OSError
                try:
                    conn.unwrap()
                except OSError:
                    pass
        return self.voidresp()



if __name__ == '__main__':
    test()
