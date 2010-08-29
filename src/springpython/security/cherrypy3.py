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

import cherrypy
import logging

from springpython.security import AuthenticationException
from springpython.security.context import SecurityContextHolder, SecurityContext
from springpython.security.intercept import AbstractSecurityInterceptor
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.web import FilterChainProxy, SessionStrategy,RegExpBasedFilterInvocationDefinitionMap, FilterInvocation

class CP3FilterChainProxy(FilterChainProxy):
    def __init__(self, filterInvocationDefinitionSource=None):
        FilterChainProxy.__init__(self, filterInvocationDefinitionSource)
        self.logger = logging.getLogger("springpython.security.cherrypy3.Another")
        cherrypy.tools.securityFilterChain = cherrypy._cptools.HandlerTool(self)

    def __call__(self, environ=None, start_response=None):
        if cherrypy.request.handler is None:
            return False

        def cherrypy_handler(*args, **kwargs):
            return cherrypy.request.handler(*args, **kwargs)

        def func(args):
           return args[0]()

        self.application = (func, (cherrypy_handler,))
        cherrypy.response.body = FilterChainProxy.__call__(self, cherrypy.request.wsgi_environ, None)
        return True

class CP3SessionStrategy(SessionStrategy):
    def __init__(self):
        SessionStrategy.__init__(self)
        self.logger = logging.getLogger("springpython.security.cherrypy3.CP3SessionStrategy")

    def getHttpSession(self, environ):
        return cherrypy.session.get("session_id")

    def setHttpSession(self, key, value):
        if "session_id" not in cherrypy.session:
            cherrypy.session["session_id"] = {}
        cherrypy.session["session_id"][key] = value

class CP3RedirectStrategy(object):
    def redirect(self, url):
        raise cherrypy.HTTPRedirect(url)
