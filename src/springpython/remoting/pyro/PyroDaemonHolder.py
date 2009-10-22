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
import Pyro.core, Pyro.naming

from socket import getaddrinfo, gethostbyname

pyro_threads = {}
serviceList = {}
logger = logging.getLogger("springpython.remoting.pyro.PyroDaemonHolder")

def resolve(host, port):
    canonhost = gethostbyname(host)
    canonport = getaddrinfo(host, port)[0][4][1]
    
    return canonhost, canonport

def register(pyro_obj, service_name, host, port):
    """
    Register the pyro object and its service name with the daemon.
    Also add the service to a dictionary of objects. This allows the
    PyroDaemonHolder to intelligently know when to start and stop the
    daemon thread.
    """
    logger.debug("Registering %s at %s:%s with the Pyro server" % (service_name, host, port))

    host, port = resolve(host, port)
    
    serviceList[(service_name, host, port)] = pyro_obj

    if (host, port) not in pyro_threads:
    
        logger.debug("Pyro thread needs to be started at %s:%s" % (host, port))
      
        pyro_threads[(host, port)] = _PyroThread(host, port)
        pyro_threads[(host, port)].start()
        
    pyro_threads[(host, port)].pyro_daemon.connect(pyro_obj, service_name)

def deregister(service_name, host, port):
    """
    Deregister the named service by removing it from the list of
    managed services and also disconnect from the daemon.
    """
    logger.debug("Deregistering %s at %s:%s with the Pyro server" % (service_name, host, port))

    host, port = resolve(host, port)
    
    pyro_threads[(host, port)].pyro_daemon.disconnect(serviceList[(service_name, host, port)])
    del(serviceList[(service_name, host, port)])

    def get_address((service_name, host, port)):
        return (host, port)

    if len([True for x in serviceList.keys() if get_address(x) == (host, port)]) == 0:
        logger.debug("Shutting down thread on %s:%s" % (host, port))
        shutdown(host, port)

def shutdown(daemon_host, daemon_port):
    """This provides a hook so an application can deliberately shutdown a
    daemon thread."""
    logger.debug("Shutting down pyro daemon at %s:%s" % (daemon_host, daemon_port))

    daemon_host, daemon_port = resolve(daemon_host, daemon_port)

    try:
        pyro_threads[(daemon_host, daemon_port)].shutdown()
        del(pyro_threads[(daemon_host, daemon_port)])
    except:
        logger.debug("Failed to shutdown %s:%s" % (daemon_host, daemon_port))

class _PyroThread(threading.Thread):
    """
    This is a thread that runs the Pyro daemon. It is instantiated automatically
    from within PyroServiceExporter.
    """
    
    def __init__(self, host, port):
        """
        When this class is created, it also created a Pyro core daemon to manage.
        """
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.logger = logging.getLogger("springpython.remoting.pyro.PyroDaemonHolder._PyroThread")

        self.pyro_daemon = Pyro.core.Daemon(host=host, port=port)
    
    def run(self):
        """
        When this thread starts up, it initializes the Pyro server and then puts the
        daemon into listen mode so it can process remote requests.
        """
        self._running = True
        self.logger.debug("Starting up Pyro server thread for %s:%s" % (self.host, self.port))
        Pyro.core.initServer()
        self.pyro_daemon.requestLoop(condition = lambda:self._running)

    def shutdown(self):
        """
        This is a hook in order to signal the thread that its time to shutdown
        the Pyro daemon.
        """
        self._running = False
        self.logger.debug("Signaling shutdown of Pyro server thread for %s:%s" % (self.host, self.port))


