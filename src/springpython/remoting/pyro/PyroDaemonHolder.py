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

pyro_thread = None
serviceList = {}

def register(pyro_obj, service_name, verbose = False):
    """
    Register the pyro object and its service name with the daemon.
    Also add the service to a dictionary of objects. This allows the
    PyroDaemonHolder to intelligently know when to start and stop the
    daemon thread.
    """
    global pyro_thread
    
    if verbose: print "Registering %s with the Pyro server" % service_name
    
    serviceList[service_name] = pyro_obj
    if pyro_thread is None:
        
        if verbose: print "Pyro thread needs to be started"
        
        pyro_thread = _PyroThread()
        pyro_thread.start()
        
    uri = pyro_thread.daemon.connect(pyro_obj, service_name)
    
    if verbose: print uri

def deregister(service_name, verbose = False):
    """
    Deregister the named service by removing it from the list of
    managed services and also disconnect from the daemon.
    """
    if verbose: print "Deregistering %s from the Pyro server" % service_name
    
    pyro_thread.daemon.disconnect(serviceList[service_name])
    del(serviceList[service_name])
    if len(serviceList) == 0:       
        shutdown(verbose)

def shutdown(verbose = False):
    """This provides a hook so an application can deliberately shutdown the
    daemon thread."""
    global pyro_thread
    
    if verbose: print "We no longer have any services. Shutting down pyro daemon."
    
    try:
        pyro_thread.shutdown()
    except:
        pass
    pyro_thread = None

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

