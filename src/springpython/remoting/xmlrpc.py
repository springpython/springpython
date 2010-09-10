# -*- coding: utf-8 -*-

# stdlib
import httplib
import logging
import socket
import ssl

from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpclib import ServerProxy, Error, Transport

# PyOpenSSL
from OpenSSL import SSL

# Spring Python
from springpython.util import TRACE1

__all__ = ["VerificationException", "SSLXMLRPCServer", "SSLXMLRPCClient"]

class VerificationException(Exception):
    """ Raised when the verification of a certificate's fields fails.
    """

# ##############################################################################
# Server
# ##############################################################################

# A slightly modified version of the public-domain code from
# http://skvidal.fedorapeople.org/SecureXMLRPCServer.py
class SSLSocketWrapper(object):
    """ This whole class exists just to filter out a parameter
    passed in to the shutdown() method in SimpleXMLRPC.doPOST()
    """
    def __init__(self, conn):
        """ Connection is not yet a new-style class, so I'm making a proxy
        instead of subclassing."""
        self.__dict__["conn"] = conn

    def __getattr__(self,name):
        return getattr(self.__dict__["conn"], name)

    def __setattr__(self,name, value):
        setattr(self.__dict__["conn"], name, value)

    def shutdown(self, how=1):
        """ SimpleXMLRpcServer.doPOST calls shutdown(1), and Connection.shutdown()
        doesn't take an argument. So we just discard the argument.
        """
        self.__dict__["conn"].shutdown()

    def accept(self):
        """ This is the other part of the shutdown() workaround. Since servers
        create new sockets, we have to infect them with our magic.
        """
        c, a = self.__dict__["conn"].accept()
        return (SSLSocketWrapper(c), a)


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/", "/RPC2",)

    def setup(self):
        self.connection = self.request # for doPOST
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

class SSLXMLRPCServer(object, SimpleXMLRPCServer):
    def __init__(self, host=None, port=None, key_file=None, cert_file=None,
                 ca_certs=None, cipher_list="DEFAULT", ssl_method=SSL.TLSv1_METHOD,
                 ctx_options=SSL.OP_NO_SSLv2,
                 verify_options=SSL.VERIFY_NONE,
                 ssl_verify_depth=1, verify_fields=None):

        SimpleXMLRPCServer.__init__(self, (host, port), requestHandler=RequestHandler)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.register_functions()

        ctx = SSL.Context(ssl_method)
        ctx.set_options(ctx_options)

        ctx.use_privatekey_file(key_file)

        if cert_file:
            ctx.use_certificate_file(cert_file)

        if ca_certs:
            ctx.load_verify_locations(ca_certs)

        ctx.set_cipher_list(cipher_list)

        ctx.set_verify_depth(ssl_verify_depth)
        ctx.set_verify(verify_options, self.on_verify_peer)
        self.verify_fields = verify_fields

        self.socket = SSLSocketWrapper(SSL.Connection(ctx,
                        socket.socket(self.address_family, self.socket_type)))

        self.server_bind()
        self.server_activate()

    def on_verify_peer(self, conn, x509, error_number, error_depth, return_code):
        """ Verifies the other side's certificate. May be overridden in subclasses
        if the verification process needs to be customized.
        """

        if self.logger.isEnabledFor(TRACE1):
            self.logger.log(TRACE1, "on_verify_peer '%s', '%s', '%s', '%s'" % (
                error_number, error_depth, return_code))

        # error_depth = 0 means we're dealing with the client's certificate
        # and not that of a CA.
        if self.verify_fields and error_depth == 0:

            components = x509.get_subject().get_components()
            components = dict(components)

            if self.logger.isEnabledFor(TRACE1):
                self.logger.log(TRACE1, "components received '%s'" % components)

            for verify_field in self.verify_fields:

                expected_value = self.verify_fields[verify_field]
                cert_value = components.get(verify_field, None)

                if not cert_value:
                    msg = "Peer didn't send the '%s' field, fields received '%s'" % (
                        verify_field, components)
                    raise VerificationException(msg)

                if expected_value != cert_value:
                    msg = "Expected the field '%s' to have value '%s' instead of '%s'" % (
                        verify_field, expected_value, cert_value)
                    raise VerificationException(msg)

        return True

    def register_functions(self):
        raise NotImplementedError("Must be overridden by subclasses")

# ##############################################################################
# Client
# ##############################################################################


class CAValidatingHTTPSConnection(httplib.HTTPConnection):
    """ This class allows communication via SSL and takes the CAs into account.
    """

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 ca_certs=None, cert_reqs=None, strict=None, ssl_version=None,
                 timeout=None):
        httplib.HTTPConnection.__init__(self, host, port, strict, timeout)

        self.key_file = key_file
        self.cert_file = cert_file
        self.ca_certs = ca_certs
        self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version

    def connect(self):
        """ Connect to a host on a given (SSL) port.
        """

        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = self.wrap_socket(sock)

    def wrap_socket(self, sock):
        """ Gets a socket object and wraps it into an SSL-aware one. May be
        overridden in subclasses if the wrapping process needs to be customized.
        """
        return ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                    ca_certs=self.ca_certs, cert_reqs=self.cert_reqs,
                                    ssl_version=self.ssl_version)

class CAHTTPS(httplib.HTTP):
    _connection_class = CAValidatingHTTPSConnection

    def __init__(self, host=None, port=None, key_file=None, cert_file=None, ca_certs=None,
                 cert_reqs=None, strict=None, ssl_version=None, timeout=None):
        self._setup(self._connection_class(host, port, key_file, cert_file, ca_certs,
                                           cert_reqs, strict, ssl_version, timeout))

class SSLClientTransport(Transport):
    """ Handles an HTTPS transaction to an XML-RPC server.
    """
    def __init__(self, key_file=None, cert_file=None, ca_certs=None, cert_reqs=None,
                 ssl_version=None, timeout=None):
        self.key_file = key_file
        self.cert_file = cert_file
        self.ca_certs = ca_certs
        self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version
        self.timeout = timeout

        Transport.__init__(self)

    def make_connection(self, host):
        return CAHTTPS(host, key_file=self.key_file, cert_file=self.cert_file,
                       ca_certs=self.ca_certs, cert_reqs=self.cert_reqs,
                       ssl_version=self.ssl_version, timeout=self.timeout)

class SSLXMLRPCClient(ServerProxy):
    def __init__(self, uri=None, transport=None, encoding=None, verbose=0,
                 allow_none=0, use_datetime=0, key_file=None, cert_file=None,
                 ca_certs=None, cert_reqs=ssl.CERT_OPTIONAL, ssl_version=ssl.PROTOCOL_TLSv1,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):

        if not transport:
            transport=SSLClientTransport(key_file, cert_file, ca_certs, cert_reqs,
                                         ssl_version, timeout)

        ServerProxy.__init__(self, uri, transport, encoding, verbose,
                        allow_none, use_datetime)