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
from springpython.remoting.hessian.hessianlib import Hessian

class HessianProxyFactory(object):
    """
    This is wrapper around a Hessian client proxy. The idea is to inject this object with a 
    Hessian service_url, which in turn generates a Hessian client proxy. After that, any
    method calls or attribute accessses will be forwarded to the Hessian client proxy.
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
        elif name in ["post_process_before_initialization", "post_process_after_initialization"]:
            raise AttributeError, name
        else:
            if self.client_proxy is None:
                self.__dict__["client_proxy"] = Hessian(self.service_url)
            return getattr(self.client_proxy, name)

