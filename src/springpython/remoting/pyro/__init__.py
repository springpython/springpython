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
import Pyro.core
from springpython.context import InitializingObject
from springpython.remoting.pyro import PyroDaemonHolder

class PyroServiceExporter(InitializingObject):
    """
    This class will expose an object using Pyro. It requires that a daemon thread
    be up and running in order to receive requests and allow dispatching to the exposed
    object.
    """
    def __init__(self, service = None, service_name = None, service_host = "localhost", service_port = 7766):
        self.logger = logging.getLogger("springpython.remoting.pyro.PyroServiceExporter")
        self.service = service
        self.service_name = service_name
        self.service_host = service_host
        self.service_port = service_port
        self._pyro_thread = None
        
    def __del__(self):
        """
        When the service exporter goes out of scope and is garbage collected, the
        service must be deregistered.
        """
        PyroDaemonHolder.deregister(self.service_name, self.service_host, self.service_port)
        
    def __setattr__(self, name, value):
        """
        Only the explicitly listed attributes can be assigned values. Everything else is passed through to
        the actual service.
        """
        if name in ["logger", "service", "service_name", "service_host", "service_port", "_pyro_thread"]:
            self.__dict__[name] = value
        else:
            object.__setattr__(self, name, value)

    def after_properties_set(self):
        if self.service is None: raise Exception("service must NOT be None")
        if self.service_name is None: raise Exception("service_name must NOT be None")
        if self.service_host is None: raise Exception("service_host must NOT be None")
        if self.service_port is None: raise Exception("service_port must NOT be None")
        self.logger.debug("Exporting %s as a Pyro service at %s:%s" % (self.service_name, self.service_host, self.service_port))
        pyro_obj = Pyro.core.ObjBase()
        pyro_obj.delegateTo(self.service)
        PyroDaemonHolder.register(pyro_obj, self.service_name, self.service_host, self.service_port)
            
class PyroProxyFactory(object):
    """
    This is wrapper around a Pyro client proxy. The idea is to inject this object with a 
    Pyro service_url, which in turn generates a Pyro client proxy. After that, any
    method calls or attribute accessses will be forwarded to the Pyro client proxy.
    """
    def __init__(self):
        self.__dict__["client_proxy"] = None
        self.__dict__["service_url"] = None
        
    def __setattr__(self, name, value):
        if name == "service_url":
            self.__dict__["service_url"] = value
        else:
            setattr(self.client_proxy, name, value)
    
    def __getattr__(self, name):
        if name in ["service_url"]:
            return self.__dict__[name]
        elif name in ["post_process_before_initialization", "post_process_after_initialization"]:
            raise AttributeError, name
        else:
            if self.client_proxy is None:
                self.__dict__["client_proxy"] = Pyro.core.getProxyForURI(self.service_url)
            return getattr(self.client_proxy, name)

class Pyro4ServiceExporter(InitializingObject):
    """
    This class will expose an object using Pyro. It requires that a daemon thread
    be up and running in order to receive requests and allow dispatching to the exposed
    object.
    """
    def __init__(self, service = None, service_name = None, service_host = "localhost", service_port = 7766):
        self.logger = logging.getLogger("springpython.remoting.pyro.Pyro4ServiceExporter")
        self.service = service
        self.service_name = service_name
        self.service_host = service_host
        self.service_port = service_port
        self._pyro_thread = None
        
    def __del__(self):
        """
        When the service exporter goes out of scope and is garbage collected, the
        service must be deregistered.
        """
        from springpython.remoting.pyro import Pyro4DaemonHolder
        Pyro4DaemonHolder.deregister(self.service_name, self.service_host, self.service_port)
        
    def __setattr__(self, name, value):
        """
        Only the explicitly listed attributes can be assigned values. Everything else is passed through to
        the actual service.
        """
        if name in ["logger", "service", "service_name", "service_host", "service_port", "_pyro_thread"]:
            self.__dict__[name] = value
        else:
            object.__setattr__(self, name, value)

    def after_properties_set(self):
        import Pyro4
        from springpython.remoting.pyro import Pyro4DaemonHolder
        if self.service is None: raise Exception("service must NOT be None")
        if self.service_name is None: raise Exception("service_name must NOT be None")
        if self.service_host is None: raise Exception("service_host must NOT be None")
        if self.service_port is None: raise Exception("service_port must NOT be None")
        self.logger.debug("Exporting %s as a Pyro service at %s:%s" % (self.service_name, self.service_host, self.service_port))
	wrapping_obj = PyroWrapperObj(self.service)
        Pyro4DaemonHolder.register(wrapping_obj, self.service_name, self.service_host, self.service_port)
            
class PyroWrapperObj(object):
    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        if name in ["__pyroInvoke", "__call__", "_pyroId", "_pyroDaemon", "delegate"]:
            return self.__dict__[name]
        else:
            return getattr(self.delegate, name)

    def __setattr__(self, name, value):
        if name in ["__pyroInvoke", "__call__", "_pyroId", "_pyroDaemon", "delegate"]:
            self.__dict__[name] = value
        else:
            setattr(self.delegate, name, value)

class Pyro4ProxyFactory(object):
    """
    This is wrapper around a Pyro client proxy. The idea is to inject this object with a 
    Pyro service_url, which in turn generates a Pyro client proxy. After that, any
    method calls or attribute accessses will be forwarded to the Pyro client proxy.
    """
    def __init__(self):
        self.__dict__["client_proxy"] = None
        self.__dict__["service_url"] = None
        
    def __setattr__(self, name, value):
        if name == "service_url":
            self.__dict__["service_url"] = value
        else:
            setattr(self.client_proxy, name, value)
    
    def __getattr__(self, name):
        import Pyro4
        if name in ["service_url"]:
            return self.__dict__[name]
        elif name in ["post_process_before_initialization", "post_process_after_initialization"]:
            raise AttributeError, name
        else:
            if self.client_proxy is None:
                self.__dict__["client_proxy"] = Pyro4.Proxy(self.service_url)
            return getattr(self.client_proxy, name)

