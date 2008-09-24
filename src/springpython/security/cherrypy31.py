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

from springpython.security import AuthenticationException
from springpython.security.context import SecurityContextHolder, SecurityContext
from springpython.security.intercept import AbstractSecurityInterceptor
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.web import RegExpBasedFilterInvocationDefinitionMap, FilterInvocation

class ContextSessionFilter(object):
    """
    This filter ensures that a SecurityContext is always available for others
    filters to work on. If the session doesn't have it yet, it creates one
    and stores it.
    """
    def newContext(self):
        context = SecurityContext()
        context.authentication = UsernamePasswordAuthenticationToken()
        return context
        
    def run(self):
        context = cherrypy.session.get("SPRINGPYTHON_SECURITY_CONTEXT_KEY")
        if not context:
            context = self.newContext()
        
        SecurityContextHolder.setContext(context)
        cherrypy.session["SPRINGPYTHON_SECURITY_CONTEXT_KEY"] = context

class SecurityFilter(object):
    """
    This filter is similar to the AuthenicationFilter except that it validates
    the user's credentials that was found in the session. If the user had been
    for instance deleted or his role had changed this is where it'll be rejected.
    """
    def __init__(self, authManager, redirectPath):
        self.authManager = authManager
        self.redirectPath = redirectPath

    def run(self):
        if SecurityContextHolder.getContext().authentication.isAuthenticated():
            cherrypy.log("You are not required to reauthenticate everytime, and appear to already be authenticted, access GRANTED.")
        
        try:
            token = SecurityContextHolder.getContext().authentication
            cherrypy.log("Trying to authenticate %s using the authentication manager" % token)
            SecurityContextHolder.getContext().authentication = self.authManager.authenticate(token)
            cherrypy.log("%s was successfully authenticated, access GRANTED." % token.username)
        except AuthenticationException, e:
            cherrypy.log("Authentication failure, access DENIED.")
            raise cherrypy.HTTPRedirect(self.redirectPath)

class AuthenticationFilter(object):
    """
    The AuthenicationFilter is in charge of validating that
    the username and password input and sent by the user is correct
    according to the users we've enabled.

    Upon success the SecurityContextHolder.getContext().authentication
    object will contain the user's credentials which is
    stored in the session by the ContextSessionFilter.

    If the credentials aren't valid this filter automatically redirects
    back to the login form which in this example is part of the home page.
    """
    def __init__(self, authManager):
        self.authManager = authManager

    def run(self):
        try:
            username = cherrypy.request.params.get('username', '')
            password = cherrypy.request.params.get('password', '')
            token = UsernamePasswordAuthenticationToken(username, password)
            SecurityContextHolder.getContext().authentication = self.authManager.authenticate(token)
            cherrypy.log("%s was successfully authenticated, access GRANTED." % token.username)
        except AuthenticationException, e:
            cherrypy.log("Authentication failure, access DENIED.")
            raise cherrypy.HTTPRedirect('/')

class SecurityInterceptorFilter(AbstractSecurityInterceptor, cherrypy.Tool):
    """
    The FilterSecurityInterceptor
    
    TODO: This filter needs more work. It has to be able to trap before/after situations, and also
    deny access properly, if user doesn't have proper roles through AccessDecisionManager.
    
    For now, it has been pulled from the PetClinic sample application so that a partial upgrade to
    CherryPy 3.1 can be completed on schedule.
    """
    SPRINGPYTHON_FILTER_SECURITY_INTERCEPTOR_KEY = "SPRINGPYTHON_FILTER_SECURITY_INTERCEPTOR_KEY"

    def __init__(self, authenticationManager = None, accessDecisionManager = None, objectDefinitionSource = None):
        AbstractSecurityInterceptor.__init__(self, authenticationManager, accessDecisionManager, objectDefinitionSource)
        cherrypy.Tool.__init__(self, "'before_handler'", self._do_before)
        self.objectDefinitionSource = objectDefinitionSource
        
    def _setup(self):        
        cherrypy.log.error(str(self._merged_args))
        conf = self._merged_args()
        cherrypy.request.hooks.attach('before_finalize', self._do_after, **conf)

    def _do_before(self, *args, **kwargs):
        cherrypy.log.error("BEFORE: " + cherrypy.request.path_info)

    def _do_after(self, *args, **kwargs):
        cherrypy.log.error("AFTER: " + cherrypy.request.path_info)
        
    def run(self):
        pass
