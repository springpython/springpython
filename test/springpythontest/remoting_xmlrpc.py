# -*- coding: utf-8 -*-

"""
   Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved

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
import socket
import ssl
import threading
import time
import unittest

from SocketServer import StreamRequestHandler
from xmlrpclib import Transport

# Spring Python
from springpython.remoting.xmlrpc import SSLServer, SSLClient, RequestHandler, \
     SSLClientTransport, VerificationException

RESULT_OK = "All good"

server_key = "./support/pki/server-key.pem"
server_cert = "./support/pki/server-cert.pem"
client_key = "./support/pki/client-key.pem"
client_cert = "./support/pki/client-cert.pem"
ca_certs = "./support/pki/ca-chain.pem"

class MySSLServer(SSLServer):

    def test_server(self):
        return RESULT_OK

    def register_functions(self):
        self.register_function(self.shutdown)
        self.register_function(self.test_server)

class _DummyServer(SSLServer):
    pass

class _DummyRequest():
    def recv(self, *ignored_args, **ignored_kwargs):
        pass

class _MyClientTransport(object):
    def __init__(self, ca_certs=None, keyfile=None, certfile=None, cert_reqs=None,
                 ssl_version=None, timeout=None, strict=None):
        self.ca_certs = ca_certs
        self.keyfile = keyfile
        self.certfile = certfile
        self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version
        self.timeout = timeout
        self.strict = strict

class TestInitDefaultArguments(unittest.TestCase):
    def test_init_default_arguments(self):
        """ Tests various defaults various and those passed to __init__'s.
        """

        self.assertTrue(issubclass(VerificationException, Exception))
        self.assertEqual(RequestHandler.rpc_paths, ("/", "/RPC2"))
        self.assertEqual(SSLClientTransport.user_agent,
                         "SSL XML-RPC Client (by http://springpython.webfactional.com)")

        server1 = MySSLServer("127.0.0.1", 8001)

        self.assertEqual(server1.keyfile, None)
        self.assertEqual(server1.certfile, None)
        self.assertEqual(server1.ca_certs, None)
        self.assertEqual(server1.cert_reqs, ssl.CERT_NONE)
        self.assertEqual(server1.ssl_version, ssl.PROTOCOL_TLSv1)
        self.assertEqual(server1.do_handshake_on_connect, True)
        self.assertEqual(server1.suppress_ragged_eofs, True)
        self.assertEqual(server1.ciphers, None)
        self.assertEqual(server1.logRequests, True)
        self.assertEqual(server1.verify_fields, None)

        server_host = "127.0.0.1"
        server_port = 8002
        server_keyfile = "server_keyfile"
        server_certfile = "server_certfile"
        server_ca_certs = "server_ca_certs"
        server_cert_reqs = ssl.CERT_OPTIONAL
        server_ssl_version = ssl.PROTOCOL_SSLv3
        server_do_handshake_on_connect = False
        server_suppress_ragged_eofs = False
        server_ciphers = "ALL"
        server_log_requests = False
        server_verify_fields = {"commonName": "Foo", "organizationName":"Baz"}

        server2 = MySSLServer(server_host, server_port, server_keyfile,
                    server_certfile, server_ca_certs, server_cert_reqs,
                    server_ssl_version, server_do_handshake_on_connect,
                    server_suppress_ragged_eofs, server_ciphers, server_log_requests,
                    verify_fields=server_verify_fields)

        # inherited from SocketServer.BaseServer
        self.assertEqual(server2.server_address, (server_host, server_port))

        self.assertEqual(server2.keyfile, server_keyfile)
        self.assertEqual(server2.certfile, server_certfile)
        self.assertEqual(server2.ca_certs, server_ca_certs)
        self.assertEqual(server2.cert_reqs, server_cert_reqs)
        self.assertEqual(server2.ssl_version, server_ssl_version)
        self.assertEqual(server2.do_handshake_on_connect, server_do_handshake_on_connect)
        self.assertEqual(server2.suppress_ragged_eofs, server_suppress_ragged_eofs)
        self.assertEqual(server2.ciphers, server_ciphers)
        self.assertEqual(server2.logRequests, server_log_requests)
        self.assertEqual(sorted(server2.verify_fields), sorted(server_verify_fields))

        client_uri="https://127.0.0.1:8000/RPC2"
        client_ca_certs="client_ca_certs"
        client_keyfile="client_keyfile"
        client_certfile="client_certfile"
        client_cert_reqs=ssl.CERT_OPTIONAL
        client_ssl_version=ssl.PROTOCOL_SSLv23
        client_transport=_MyClientTransport
        client_encoding="utf-16"
        client_verbose=1
        client_allow_none=False
        client_use_datetime=False
        client_timeout=13
        client_strict=True

        client2 = SSLClient(client_uri, client_ca_certs, client_keyfile,
                           client_certfile, client_cert_reqs, client_ssl_version,
                           client_transport, client_encoding, client_verbose,
                           client_allow_none, client_use_datetime, client_timeout,
                           client_strict)

        self.assertEqual(client2._ServerProxy__host, "127.0.0.1:8000")
        self.assertEqual(client2._ServerProxy__transport.ca_certs, client_ca_certs)
        self.assertEqual(client2._ServerProxy__transport.keyfile, client_keyfile)
        self.assertEqual(client2._ServerProxy__transport.certfile, client_certfile)
        self.assertEqual(client2._ServerProxy__transport.cert_reqs, client_cert_reqs)
        self.assertEqual(client2._ServerProxy__transport.ssl_version, client_ssl_version)
        self.assertTrue(isinstance(client2._ServerProxy__transport, _MyClientTransport))
        self.assertEqual(client2._ServerProxy__encoding, client_encoding)
        self.assertEqual(client2._ServerProxy__verbose, client_verbose)
        self.assertEqual(client2._ServerProxy__allow_none, client_allow_none)
        self.assertEqual(client2._ServerProxy__transport.timeout, client_timeout)
        self.assertEqual(client2._ServerProxy__transport.strict, client_strict)

        self.assertRaises(NotImplementedError, _DummyServer, "127.0.0.1", 8003)

    def test_request_handler(self):
        request = _DummyRequest()
        rh = RequestHandler(request, None, None)
        rh.setup()
        self.assertTrue(rh.connection is request)
        self.assertTrue(isinstance(rh.rfile, socket._fileobject))
        self.assertTrue(isinstance(rh.wfile, socket._fileobject))
        self.assertTrue(rh.rfile._sock is request)
        self.assertEqual(rh.rfile.mode, "rb")
        self.assertEqual(rh.rfile.bufsize, socket._fileobject.default_bufsize)
        self.assertTrue(rh.wfile._sock is request)
        self.assertEqual(rh.wfile.mode, "wb")
        self.assertEqual(rh.wfile.bufsize, StreamRequestHandler.wbufsize)

    def test_import_all(self):
        _locals = {}
        _globals = {}

        exec "from springpython.remoting.xmlrpc import *" in _locals, _globals

        self.assertEqual(len(_globals), 3)
        self.assertEqual(sorted(_globals), ["SSLClient", "SSLServer", "VerificationException"])

class TestSSL(unittest.TestCase):

    class _ClientServerContextManager(object):
        def __init__(self, server_port, cert_reqs=ssl.CERT_NONE, verify_fields={}):
            self.server_port = server_port
            self.cert_reqs = cert_reqs
            self.verify_fields = verify_fields

        def __enter__(self):
            server = MySSLServer("127.0.0.1", self.server_port, server_key,
                                 server_cert, ca_certs, cert_reqs=self.cert_reqs,
                                 verify_fields=self.verify_fields)
            self.server_thread = self._start_server(server)
            time.sleep(0.5)

        def __exit__(self, *ignored_args):
            self.server_thread.server.shutdown()

        def _start_server(self, server):

            class _ServerController(threading.Thread):
                def __init__(self, server):
                    self.server = server
                    self.isDaemon = False
                    super(_ServerController, self).__init__()

                def run(self):
                    self.server.serve_forever()

            server_thread = _ServerController(server)
            server_thread.start()

            return server_thread


    def test_simple_ssl(self):
        """ Server uses its cert, client uses none.
        """
        server_port = 9001
        with TestSSL._ClientServerContextManager(server_port):
            client = SSLClient("https://localhost:%d/RPC2" % server_port, ca_certs)
            self.assertEqual(client.test_server(), RESULT_OK)

    def test_client_cert(self):
        """ Server & client use certs.
        """
        server_port = 9002
        with TestSSL._ClientServerContextManager(server_port, ssl.CERT_REQUIRED):
            client = SSLClient("https://localhost:%d/RPC2" % server_port, ca_certs,
                               client_key, client_cert)
            self.assertEqual(client.test_server(), RESULT_OK)

    def test_client_cert_verify_ok(self):
        """ Server & client use certs. Server succesfully validates client certificate's fields.
        """
        server_port = 9003
        verify_fields = {"commonName":"My Client", "countryName":"US",
                         "organizationalUnitName":"My Unit", "organizationName":"My Company",
                         "stateOrProvinceName":"My State"}

        with TestSSL._ClientServerContextManager(server_port, ssl.CERT_REQUIRED, verify_fields):
            client = SSLClient("https://localhost:%d/RPC2" % server_port, ca_certs,
                               client_key, client_cert)
            self.assertEqual(client.test_server(), RESULT_OK)

    def test_client_cert_verify_failure_missing_field(self):
        """ Server & client use certs. Server fails to validate client certificate's fields
        (a field is missing).
        """
        server_port = 9004
        verify_fields = {"commonName":"My Client", "countryName":"US",
                         "organizationalUnitName":"My Unit", "organizationName":"My Company",
                         "stateOrProvinceName":"My State", "FOO": "BAR"}

        with TestSSL._ClientServerContextManager(server_port, ssl.CERT_REQUIRED, verify_fields):
            client = SSLClient("https://localhost:%d/RPC2" % server_port, ca_certs,
                               client_key, client_cert)
            self.assertRaises(Exception, client.test_server)

    def test_client_cert_failure_field_incorrect_value(self):
        """ Server & client use certs. Server fails to validate client certificate's fields
        (all fields are in place, but commonName has an incorrect value).
        """
        server_port = 9005
        verify_fields = {"commonName":"Invalid"}
        with TestSSL._ClientServerContextManager(server_port, ssl.CERT_REQUIRED, verify_fields):
            client = SSLClient("https://localhost:%d/RPC2" % server_port, ca_certs,
                               client_key, client_cert)
            self.assertRaises(Exception, client.test_server)

    def test_client_cert_verify_failure_cert_optional_no_client_cert(self):
        """ Server optionally requires a client to send the certificate
        and validates its fields but client sends none.
        """
        server_port = 9006
        verify_fields = {"commonName":"My Client"}
        with TestSSL._ClientServerContextManager(server_port, ssl.CERT_OPTIONAL, verify_fields):
            client = SSLClient("https://localhost:%d/RPC2" % server_port, ca_certs)
            self.assertRaises(Exception, client.test_server)

    def test_cert_required_no_client_cert(self):
        """ Server requires a client to send the certificate but client sends none.
        """
        server_port = 9007
        with TestSSL._ClientServerContextManager(server_port, ssl.CERT_REQUIRED):
            client = SSLClient("https://localhost:%d/RPC2" % server_port, ca_certs)
            self.assertRaises(ssl.SSLError, client.test_server)

if __name__ == "__main__":
    unittest.main()