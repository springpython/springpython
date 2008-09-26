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
import new
import Pyro.core
import springpython
from springpython.remoting.pyro import PyroDaemonHolder

class PyroServiceExporter(object):
    """
    This class will expose an object using Pyro. It requires that a daemon thread
    be up and running in order to receive requests and allow dispatching to the exposed
    object.
    """
    def __init__(self):
        self.__dict__["service"] = None
        self.__dict__["service_name"] = None
        self.__dict__["_pyro_thread"] = None
        
    def __del__(self):
        """
        When the service exporter goes out of scope and is garbage collected, the
        service must be deregistered.
        """
        try:
            PyroDaemonHolder.deregister(self.service_name)
        except:
            pass
        
    def __setattr__(self, name, value):
        """
        Because this is being used by dependency injection from an IoC container,
        we cannot depend on the __init__ method setting everything up. Instead, we
        need to wait until the service and serviceInterface is set, and then
        register the service.
        """
        if name == "service" or name == "service_name":
            self.__dict__[name] = value
        else:
            object.__setattr__(self, name, value)
        if self.service is not None and self.service_name is not None and self._pyro_thread is None:
            pyro_obj = Pyro.core.ObjBase()
            pyro_obj.delegateTo(self.service)        
            PyroDaemonHolder.register(pyro_obj, self.service_name)
            
class PyroProxyFactory(object):
    """
    This is wrapper around a Pyro client proxy. The idea is to inject this object with a 
    Pyro service_url, which in turn generates a Pyro client proxy. After that, any
    method calls or attribute accessses will be forwarded to the Pyro client proxy.
    """
    def __init__(self):
        self.__dict__["client_proxy"] = None
        
    def __setattr__(self, name, value):
        if name == "service_url":
            self.__dict__["service_url"] = value
        else:
            setattr(self.client_proxy, name, value)
    
    def __getattr__(self, name):
        if name == "service_url":
            return self.service_url
        elif name == "post_process_after_initialization":
            raise AttributeError, name
        else:
            if self.client_proxy is None:
                self.__dict__["client_proxy"] = Pyro.core.getProxyForURI(self.service_url)
            return getattr(self.client_proxy, name)

