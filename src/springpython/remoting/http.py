# -*- coding: utf-8 -*-

# stdlib
import httplib
import socket
import ssl

class CAValidatingHTTPSConnection(httplib.HTTPConnection):
    """ This class allows communication via SSL/TLS and takes Certificate Authorities
    into account.
    """

    def __init__(self, host, port=None, keyfile=None, certfile=None,
                 ca_certs=None, cert_reqs=None, strict=None, ssl_version=None,
                 timeout=None):
        httplib.HTTPConnection.__init__(self, host, port, strict, timeout)

        self.keyfile = keyfile
        self.certfile = certfile
        self.ca_certs = ca_certs
        self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version

    def connect(self):
        """ Connect to a host on a given (SSL/TLS) port.
        """
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = self.wrap_socket(sock)

    def wrap_socket(self, sock):
        """ Gets a socket object and wraps it into an SSL/TLS-aware one. May be
        overridden in subclasses if the wrapping process needs to be customized.
        """
        return ssl.wrap_socket(sock, self.keyfile, self.certfile,
                                    ca_certs=self.ca_certs, cert_reqs=self.cert_reqs,
                                    ssl_version=self.ssl_version)

class CAValidatingHTTPS(httplib.HTTP):
    """ A subclass of httplib.HTTP which is aware of Certificate Authorities
    used in SSL/TLS transactions.
    """
    _connection_class = CAValidatingHTTPSConnection

    def __init__(self, host=None, port=None, strict=None, keyfile=None, certfile=None, ca_certs=None,
                 cert_reqs=None, ssl_version=None, timeout=None):
        self._setup(self._connection_class(host, port, keyfile, certfile, ca_certs,
                                           cert_reqs, strict, ssl_version, timeout))