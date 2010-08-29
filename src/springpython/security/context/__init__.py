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
from springpython.security.providers import Authentication

# See GlobalSecurityContextHolderStrategy
_globalContext = None

class SecurityContext(object):
    def __init__(self, authentication = Authentication()):
        self.authentication = authentication

    def __str__(self):
        if self.authentication == None:
            return "Authentication is empty"
        else:
            return self.authentication.__str__()

class SecurityContextHolderStrategy(object):
    """Strategy interface to allow defining ways to store security context."""
    def clearContext(self):
        raise NotImplementedError()
    def getContext(self):
        raise NotImplementedError()
    def setContext(self, context):
        raise NotImplementedError()

class ThreadLocalSecurityContextHolderStrategy(SecurityContextHolderStrategy):
    """Strategy to store the security context in a local thread. This allows multi-threaded
    apps to manage multiple contexts at the same time."""
    def __init__(self):
        self.logger = logging.getLogger("springpython.security.context.ThreadLocalSecurityContextHolderStrategy")
        self.contextHolder = threading.local()
        self.logger.debug("Creating a new threadlocal security context.")
        self.clearContext()

    def clearContext(self):
        self.contextHolder.context = None

    def getContext(self):
        if not self.contextHolder.context:
            self.setContext(SecurityContext())
        return self.contextHolder.context     

    def setContext(self, context):
        if not context:
            raise SecurityException("Only non-None security context's are allowed")
        self.contextHolder.context = context    

class GlobalSecurityContextHolderStrategy(SecurityContextHolderStrategy):
    """Store one context in the entire python virtual machine. This typically suits a client-side
    application."""
    def __init__(self):
        self.logger = logging.getLogger("springpython.security.context.GlobalSecurityContextHolderStrategy")
        self.clearContext()

    def clearContext(self):
        global _globalContext
        _globalContext = None

    def getContext(self):
        global _globalContext
        if not _globalContext:
            self.setContext(SecurityContext())
        return _globalContext

    def setContext(self, context):
        global _globalContext
        if not context:
            raise SecurityException("Only non-None security context's are allowed")
        _globalContext = context
