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
import threading
import Pyro.core, Pyro.naming

pyroThread = None
serviceList = {}

def register(pyroObj, serviceName, verbose = False):
    """
    Register the pyro object and its service name with the daemon.
    Also add the service to a dictionary of objects. This allows the
    PyroDaemonHolder to intelligently know when to start and stop the
    daemon thread.
    """
    global pyroThread
    
    if verbose: print "Registering %s with the Pyro server" % serviceName
    
    serviceList[serviceName] = pyroObj
    if pyroThread is None:
        
        if verbose: print "Pyro thread needs to be started"
        
        pyroThread = _PyroThread()
        pyroThread.start()
        
    uri = pyroThread.daemon.connect(pyroObj, serviceName)
    
    if verbose: print uri

def deregister(serviceName, verbose = False):
    """
    Deregister the named service by removing it from the list of
    managed services and also disconnect from the daemon.
    """
    if verbose: print "Deregistering %s from the Pyro server" % serviceName
    
    pyroThread.daemon.disconnect(serviceList[serviceName])
    del(serviceList[serviceName])
    if len(serviceList) == 0:       
        shutdown(verbose)

def shutdown(verbose = False):
    """This provides a hook so an application can deliberately shutdown the
    daemon thread."""
    global pyroThread
    
    if verbose: print "We no longer have any services. Shutting down pyro daemon."
    
    try:
        pyroThread.shutdown()
    except:
        pass
    pyroThread = None

class _PyroThread(threading.Thread):
    """
    This is a thread that runs the Pyro daemon. It is instantiated automatically
    from within PyroServiceExporter.
    """
    
    def __init__(self):
        """
        When this class is created, it also created a Pyro core daemon to manage.
        """
        threading.Thread.__init__(self)
        self.daemon = Pyro.core.Daemon()
    
    def run(self):
        """
        When this thread starts up, it initializes the Pyro server and then puts the
        daemon into listen mode so it can process remote requests.
        """
        self._running = True
        Pyro.core.initServer()
        self.daemon.requestLoop(condition = lambda:self._running)

    def shutdown(self):
        """
        This is a hook in order to signal the thread that its time to shutdown
        the Pyro daemon.
        """
        self._running = False

