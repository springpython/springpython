# -*- coding: utf-8 -*-
"""
   Copyright 2006-2011 SpringSource (http://springsource.com), All Rights Reserved

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.       
"""


# stdlib
import httplib
import socket
import ssl

class CAValidatingHTTPSConnection(httplib.HTTPConnection):
    """ This class allows communication via SSL/TLS and takes Certificate Authorities
    into account.
    """

    def __init__(self, host, port=None, ca_certs=None, keyfile=None, certfile=None,
                 cert_reqs=None, strict=None, ssl_version=None,
                 timeout=None):
        httplib.HTTPConnection.__init__(self, host, port, strict, timeout)

        self.ca_certs = ca_certs
        self.keyfile = keyfile
        self.certfile = certfile
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

    def __init__(self, host=None, port=None, strict=None, ca_certs=None, keyfile=None, certfile=None,
                 cert_reqs=None, ssl_version=None, timeout=None):
        self._setup(self._connection_class(host, port, ca_certs, keyfile, certfile,
                                           cert_reqs, strict, ssl_version, timeout))
