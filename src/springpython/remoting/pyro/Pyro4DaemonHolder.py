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
import logging
import threading
import time
import Pyro4

from socket import getaddrinfo, gethostbyname

pyro_threads = {}
serviceList = {}
logger = logging.getLogger("springpython.remoting.pyro.Pyro4DaemonHolder")

def resolve(host, port):
    canonhost = gethostbyname(host)
    canonport = getaddrinfo(host, port)[0][4][1]
    
    return canonhost, canonport

def register(pyro_obj, service_name, host, port):
    """
    Register the Pyro4 object and its service name with the daemon.
    Also add the service to a dictionary of objects. This allows the
    PyroDaemonHolder to intelligently know when to start and stop the
    daemon thread.
    """
    logger.debug("Registering %s at %s:%s with the Pyro4 server" % (service_name, host, port))

    host, port = resolve(host, port)
    
    serviceList[(service_name, host, port)] = pyro_obj

    if (host, port) not in pyro_threads:
    
        logger.debug("Pyro4 thread needs to be started at %s:%s" % (host, port))
      
        pyro_threads[(host, port)] = _Pyro4Thread(host, port)
        pyro_threads[(host, port)].start()
        
    if not hasattr(pyro_obj, "_pyroId"):
        uri = pyro_threads[(host, port)].pyro_daemon.register(pyro_obj, service_name)

def deregister(service_name, host, port):
    """
    Deregister the named service by removing it from the list of
    managed services and also disconnect from the daemon.
    """
    logger.debug("Deregistering %s at %s:%s with the Pyro4 server" % (service_name, host, port))

    host, port = resolve(host, port)

    if (host, port) in pyro_threads:    
        pyro_threads[(host, port)].pyro_daemon.unregister(serviceList[(service_name, host, port)])
        del(serviceList[(service_name, host, port)])

        def get_address((service_name, host, port)):
            return (host, port)

        if len([True for x in serviceList.keys() if get_address(x) == (host, port)]) == 0:
            shutdown(host, port)

def shutdown(daemon_host, daemon_port):
    """This provides a hook so an application can deliberately shutdown a
    daemon thread."""
    logger.debug("Shutting down Pyro4 daemon at %s:%s" % (daemon_host, daemon_port))

    daemon_host, daemon_port = resolve(daemon_host, daemon_port)

    try:
        pyro_threads[(daemon_host, daemon_port)].shutdown()
        time.sleep(1.0)
        del(pyro_threads[(daemon_host, daemon_port)])
    except Exception, e:
        logger.debug("Failed to shutdown %s:%s => %s" % (daemon_host, daemon_port, e))

class _Pyro4Thread(threading.Thread):
    """
    This is a thread that runs the Pyro4 daemon. It is instantiated automatically
    from within Pyro4ServiceExporter.
    """
    
    def __init__(self, host, port):
        """
        When this class is created, it also created a Pyro4 core daemon to manage.
        """
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.logger = logging.getLogger("springpython.remoting.pyro.Pyro4DaemonHolder._Pyro4Thread")

        self.logger.debug("Creating Pyro4 daemon")
        self.pyro_daemon = Pyro4.Daemon(host=host, port=port)
    
    def run(self):
        """
        When this thread starts up, it initializes the Pyro4 server and then puts the
        daemon into listen mode so it can process remote requests.
        """
        self.logger.debug("Starting up Pyro4 server thread for %s:%s" % (self.host, self.port))
        self.pyro_daemon.requestLoop()

    def shutdown(self):
        """
        This is a hook in order to signal the thread that its time to shutdown
        the Pyro4 daemon.
        """
        self.logger.debug("Signaling shutdown of Pyro4 server thread for %s:%s" % (self.host, self.port))
        class ShutdownThread(threading.Thread):
            def __init__(self, pyro_daemon):
                threading.Thread.__init__(self)
                self.pyro_daemon = pyro_daemon
                self.logger = logging.getLogger("springpython.remoting.pyro.Pyro4DaemonHolder.ShutdownThread")
            def run(self):
                self.logger.debug("Sending shutdown signal...")
                self.pyro_daemon.shutdown()

        ShutdownThread(self.pyro_daemon).start()


