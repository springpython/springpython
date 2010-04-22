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
import Cookie
import logging
import re
import pickle
import types
from springpython.context import ApplicationContextAware
from springpython.aop import utils
from springpython.security import AccessDeniedException
from springpython.security import AuthenticationException
from springpython.security.context import SecurityContext
from springpython.security.context import SecurityContextHolder
from springpython.security.intercept import AbstractSecurityInterceptor
from springpython.security.intercept import ObjectDefinitionSource
from springpython.security.providers import UsernamePasswordAuthenticationToken

logger = logging.getLogger("springpython.security.web")

class Filter(object):
    """This is the interface definition of a filter. It must process a request/response."""

    def doNextFilter(self, environ, start_response):
        results = None
        try:
            nextFilter = environ["SPRINGPYTHON_FILTER_CHAIN"].next()
            if isinstance(nextFilter, tuple):
                func = nextFilter[0]
                args = nextFilter[1]
                results = func(args)
            else:
                results = nextFilter(environ, start_response)
        except StopIteration:
            pass
        
        # Apparently, passing back a generator trips up CherryPy and causes it to skip 
        # the filters. If a generator is detected, convert it to a standard array.
        if type(results) == types.GeneratorType:
            results = [line for line in results]
            
        return results
    
class FilterChain(object):
    """
    Collection of WSGI filters. It allows dynamic re-chaining of filters as the situation is needed.
    
    In order to link in 3rd party WSGI middleware, see MiddlewareFilter.
    """
    
    def __init__(self):
        self.chain = []

    def addFilter(self, filter):
        self.chain.append(filter)

    def getFilterChain(self):
        for filter in self.chain:
            yield filter
    
class FilterChainProxy(Filter, ApplicationContextAware):
    """
    This acts as filter, and delegates to a chain of filters. Each time a web page is called, it dynamically
    assembles a FilterChain, and then iterates over it. This is different than the conventional style of
    wrapping applications for WSGI, because each URL pattern might have a different chained combination
    of the WSGI filters.
    
    Because most middleware objects define the wrapped application using __init__, Spring provides
    the MiddlewareFilter, to help wrap any middleware object so that it can participate in a 
    FilterChain.
    """
    
    def __init__(self, filterInvocationDefinitionSource=None):
        """This class must be application-context aware in case it is instantiated inside an IoC container."""
        ApplicationContextAware.__init__(self)
        if filterInvocationDefinitionSource is None:
            self.filterInvocationDefinitionSource = []
        else:
            self.filterInvocationDefinitionSource = filterInvocationDefinitionSource
        self.logger = logging.getLogger("springpython.security.web.FilterChainProxy")
        self.application = None

    def __call__(self, environ, start_response):
        """This will route all requests/responses through the chain of filters."""
        filterChain = FilterChain()
        for urlPattern, chainOfFilters in self.filterInvocationDefinitionSource:
            if re.compile(urlPattern).match(environ["PATH_INFO"].lower()):
		self.logger.debug("We had a match of %s against %s" % (environ["PATH_INFO"], urlPattern))
                for filter in chainOfFilters:
                        try:
                            filterChain.addFilter(self.app_context.get_object(filter))
                        except AttributeError, e:
                            filterChain.addFilter(filter)
                break

        # Put the actual application on the end of the chain.
        if self.application:
            filterChain.addFilter(self.application)
        environ["SPRINGPYTHON_FILTER_CHAIN"] = filterChain.getFilterChain()
        return self.doNextFilter(environ, start_response)

class SessionStrategy(object):
    """
    This is an interface definition in defining access to session data. There may be many
    ways to implement session data. This makes the mechanism pluggable.
    """
    
    def getHttpSession(self, environ):
        raise NotImplementedError()

    def setHttpSession(self, key, value):
        raise NotImplementedError()

class HttpSessionContextIntegrationFilter(Filter):
    """
    This filter is meant to pull security context information from the HttpSession, and store it in the
    SecurityContextHolder. Then on the response, copy and SecurityContext information back into the HttpSession.
    """
    
    # Key to the SecurityContext data stored in an HttpSession dictionary.
    SPRINGPYTHON_SECURITY_CONTEXT_KEY = "SPRINGPYTHON_SECURITY_CONTEXT_KEY"
    
    # Class name used 
    context = SecurityContext
    
    def __init__(self, sessionStrategy=None):
        self.sessionStrategy = sessionStrategy
        self.logger = logging.getLogger("springpython.security.web.HttpSessionContextIntegrationFilter")

    def __call__(self, environ, start_response):
        """This filter copies SecurityContext information back and forth between the HttpSession and the SecurityContextHolder."""

        httpSession = self.sessionStrategy.getHttpSession(environ)
        contextWhenChainProceeded = None
        
        if httpSession is not None:

            contextFromSessionObject = None
            if self.SPRINGPYTHON_SECURITY_CONTEXT_KEY in httpSession:
                contextFromSessionObject = pickle.loads(httpSession[self.SPRINGPYTHON_SECURITY_CONTEXT_KEY])
            
            if contextFromSessionObject is not None:
                if isinstance(contextFromSessionObject, SecurityContext):
                    self.logger.debug("Obtained from SPRINGPYTHON_SECURITY_CONTEXT_KEY a valid SecurityContext and set "
                                        + "to SecurityContextHolder: '%s'" % contextFromSessionObject)
                    SecurityContextHolder.setContext(contextFromSessionObject)
                else:
                    self.logger.warn("SPRINGPYTHON_SECURITY_CONTEXT_KEY did not contain a SecurityContext but contained: '%s'" % contextFromSessionObject
                                        + "'; are you improperly modifying the HttpSession directly (you should always use " 
                                        + "SecurityContextHolder) or using the HttpSession attribute reserved for this class? "
                                        + "- new SecurityContext instance associated  with SecurityContextHolder")
                    SecurityContextHolder.setContext(self.generateNewContext())
            else:
                self.logger.debug("HttpSession returned null object for SPRINGPYTHON_SECURITY_CONTEXT_KEY " +
                                    "- new SecurityContext instance associated with SecurityContextHolder")
                SecurityContextHolder.setContext(self.generateNewContext())
                
        else:
            self.logger.debug("No HttpSession currently exists - new SecurityContext instance associated with SecurityContextHolder")
            SecurityContextHolder.setContext(self.generateNewContext())
            
        self.logger.debug("Setting contextWhenChainProceeded to %s" % SecurityContextHolder.getContext())
        contextWhenChainProceeded = str(SecurityContextHolder.getContext())
             
        results = self.doNextFilter(environ, start_response)

        self.sessionStrategy.setHttpSession(self.SPRINGPYTHON_SECURITY_CONTEXT_KEY,
                                            pickle.dumps(SecurityContextHolder.getContext()))
        self.logger.debug("SecurityContext stored to HttpSession: '%s'" % SecurityContextHolder.getContext())

        SecurityContextHolder.clearContext()
        self.logger.debug("SecurityContextHolder cleared out, as request processing completed")

        return results
            
    def setContext(self, clazz):
        """This is a factory setter. The context parameter is used to create new security context objects."""
        self.context = clazz
        
    def generateNewContext(self):
        """This is a factory method that instantiates the assigned class, and populates it with an empty token."""
        context = self.context()
        context.authentication = UsernamePasswordAuthenticationToken()
        return context

    def saveContext(self):
        self.sessionStrategy.setHttpSession(self.SPRINGPYTHON_SECURITY_CONTEXT_KEY,
                                            pickle.dumps(SecurityContextHolder.getContext()))

class RedirectStrategy(object):
    """
    This class provides a mechanism to redirect users to another page. Currently, it returns a 
    standard forwarding message to the browser. This may not be the most efficient, but it guarantees
    the entire WSGI stack is processed on both request and response.
    """
    
    def redirect(self, url):
        """This is a 0-second redirect."""
        return """<META HTTP-EQUIV="Refresh" CONTENT="0; URL=%s">""" % url

class AuthenticationProcessingFilter(Filter):
    """
    This filter utilizes the authentication manager to make sure the requesting person is authenticated.
    It expects the SecurityContextHolder to be populated when it runs, so it is always good to preceed it
    with the HttpSessionContextIntegrationFilter.
    """
    
    def __init__(self, auth_manager=None, alwaysReauthenticate=False):
        self.auth_manager = auth_manager
        self.alwaysReauthenticate = alwaysReauthenticate
        self.logger = logging.getLogger("springpython.security.web.AuthenticationProcessingFilter")
        
    def __call__(self, environ, start_response):
        """
        Check if the user is trying to access the login url. Then see if they are already authenticated (and
        alwaysReauthenticate is disabled). Finally, try to authenticate the user. If successful, stored credentials
        in SecurityContextHolder. Otherwise, redirect to the login page.
        """
        # If the user is already authenticated, skip this filter.
        if not self.alwaysReauthenticate and SecurityContextHolder.getContext().authentication.isAuthenticated():
            self.logger.debug("You are not required to reauthenticate everytime, and appear to already be authenticted, access GRANTED.")
            return self.doNextFilter(environ, start_response)
        
        try:
            # Authenticate existing credentials using the authentication manager.
            token = SecurityContextHolder.getContext().authentication
            self.logger.debug("Trying to authenticate %s using the authentication manager" % token)
            SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(token)
            self.logger.debug("%s was successfully authenticated, access GRANTED." % token.username)
        except AuthenticationException, e:
            self.logger.debug("Authentication failure, access DENIED.")
            raise

        return self.doNextFilter(environ, start_response)

    def logout(self):
        SecurityContextHolder.getContext().authentication = UsernamePasswordAuthenticationToken()

class FilterInvocation:
    """Holds objects associated with a WSGI filter, such as environ. This is the web-application equivalent to MethodInvocation."""
    
    def __init__(self, environ):
        self.environ = environ

    def requestUrl(self):
        return self.environ["PATH_INFO"]

class AbstractFilterInvocationDefinitionSource(ObjectDefinitionSource):
    """Abstract implementation of ObjectDefinitionSource."""
    
    def get_attributes(self, obj):
        try:
            return self.lookupAttributes(obj.requestUrl())
        except AttributeError:
            raise TypeError("obj must be a FilterInvocation")

    def lookupAttributes(self, url):
        raise NotImplementedError()

class RegExpBasedFilterInvocationDefinitionMap(AbstractFilterInvocationDefinitionSource):
    """
    Maintains a list of ObjectDefinitionSource's associated with different HTTP request URL regular expression patterns.
    
    Regular expressions are used to match a HTTP request URL against a ConfigAttributeDefinition. The order of registering
    the regular expressions is very important. The system will identify the first matching regular expression for a given
    HTTP URL. It will not proceed to evaluate later regular expressions if a match has already been found.
    
    Accordingly, the most specific regular expressions should be registered first, with the most general regular expressions registered last.
    """
    
    def __init__(self, obj_def_source):
        self.obj_def_source = obj_def_source

    def lookupAttributes(self, url):
        if self.obj_def_source:
            for rule, attr in self.obj_def_source:
                if re.compile(rule).match(url):
                    return attr 
        return None

class FilterSecurityInterceptor(Filter, AbstractSecurityInterceptor):
    """
    Performs security handling of HTTP resources via a filter implementation.

    The ObjectDefinitionSource required by this security interceptor is of type AbstractFilterInvocationDefinitionSource.

    Refer to AbstractSecurityInterceptor for details on the workflow.
    """
    
    # Key to the FilterSecurityInterceptor's token data stored in an HttpSession dictionary.
    SPRINGPYTHON_FILTER_SECURITY_INTERCEPTOR_KEY = "SPRINGPYTHON_FILTER_SECURITY_INTERCEPTOR_KEY"
    
    def __init__(self, auth_manager = None, access_decision_mgr = None, obj_def_source = None, sessionStrategy=None):
        Filter.__init__(self)
        AbstractSecurityInterceptor.__init__(self, auth_manager, access_decision_mgr, obj_def_source)
        self.sessionStrategy = sessionStrategy
        self.obj_def_source = obj_def_source

    def __setattr__(self, name, value):
        if name == "obj_def_source" and value is not None:
            self.__dict__[name] = RegExpBasedFilterInvocationDefinitionMap(value)
        else:
            self.__dict__[name] = value

    def obtain_obj_def_source(self):
        return self.obj_def_source

    def __call__(self, environ, start_response):
        httpSession = self.sessionStrategy.getHttpSession(environ)
	self.logger.debug("Trying to check if you are authorized for this.")
        fi = FilterInvocation(environ)
        token = self.before_invocation(fi)
        if httpSession is not None:
            httpSession[self.SPRINGPYTHON_FILTER_SECURITY_INTERCEPTOR_KEY] = token

        return self.doNextFilter(environ, start_response)

        if httpSession is not None and self.SPRINGPYTHON_FILTER_SECURITY_INTERCEPTOR_KEY in httpSession:
            token = httpSession[self.SPRINGPYTHON_FILTER_SECURITY_INTERCEPTOR_KEY]
            self.after_invocation(token, None)

        return results

class ExceptionTranslationFilter(Filter):
    """
    Handles any AccessDeniedException and AuthenticationException thrown within the filter chain.

    This filter is necessary because it provides the bridge between Python exceptions and HTTP responses.
    It is solely concerned with maintaining the user interface. This filter does not do any actual security enforcement.
    
    If an AuthenticationException is detected, the filter will launch the authenticationEntryPoint. This allows common
    handling of authentication failures originating from any subclass of AuthenticationProcessingFilter.
    
    If an AccessDeniedException is detected, the filter will launch the accessDeniedHandler. This allows common
    handling of access failures originating from any subclass of AbstractSecurityInterceptor.
    """
    
    def __init__(self, authenticationEntryPoint=None, accessDeniedHandler=None, redirectStrategy=None):
        Filter.__init__(self)
        self.authenticationEntryPoint = authenticationEntryPoint
        self.accessDeniedHandler = accessDeniedHandler
        self.logger = logging.getLogger("springpython.security.web.ExceptionTranslationFilter")
        
    def __call__(self, environ, start_response):
        try:
            return self.doNextFilter(environ, start_response)
        except AuthenticationException, e:
            self.logger.debug("AuthenticationException => %s, redirecting through authenticationEntryPoint" % e)
            return self.authenticationEntryPoint(environ, start_response)
        except AccessDeniedException, e:
            self.logger.debug("AccessDeniedException => %s, redirect through accessDeniedHandler" % e)
            return self.accessDeniedHandler(environ, start_response)

class AuthenticationProcessingFilterEntryPoint(Filter):
    """This object holds the location of the login form, and is used to commence a redirect to that form."""
    
    def __init__(self, loginFormUrl=None, redirectStrategy=None):
        Filter.__init__(self)
        self.loginFormUrl = loginFormUrl
        self.redirectStrategy = redirectStrategy
        self.logger = logging.getLogger("springpython.security.web.AuthenticationProcessingFilterEntryPoint")

    def __call__(self, environ, start_response):
        self.logger.debug("Redirecting to login page %s" % self.loginFormUrl)
        return self.redirectStrategy.redirect(self.loginFormUrl)
    
class AccessDeniedHandler(Filter):
    """Used by ExceptionTranslationFilter to handle an AccessDeniedException."""
    
    def __init__(self):
        Filter.__init__(self)
        
class SimpleAccessDeniedHandler(AccessDeniedHandler):
    """A simple default implementation of the AccessDeniedHandler interface."""
    
    def __init__(self, errorPage=None, redirectStrategy=None):
        AccessDeniedHandler.__init__(self)
        self.errorPage = errorPage
        self.redirectStrategy = redirectStrategy
        self.logger = logging.getLogger("springpython.security.web.SimpleAccessDeniedHandler")
        
    def __call__(self, environ, start_response):
        self.logger.debug("Redirecting to error page %s" % self.errorPage)
        return self.redirectStrategy.redirect(self.errorPage)

class MiddlewareFilter(Filter):
    """
    This filter allows you to wrap any WSGI-compatible middleware and use it as a Spring Python filter.
    This is primary because lots of middleware objects requires the wrapped WSGI app to be included
    in the __init__ method. Spring's IoC container currently doesn't support constructor arguments.
    """
    
    def __init__(self, clazz = None, appAttribute = None):
        Filter.__init__(self)
        self.clazz = clazz
        self.appAttribute = appAttribute

    def __setattr__(self, name, value):
        if name == "clazz" and value is not None:
            self.__dict__[name] = value
            self.middleware = utils.getClass(value)(None)
        else:
            self.__dict__[name] = value

    def __call__(self, environ, start_response):
        setattr(self.middleware, self.appAttribute, environ["SPRINGPYTHON_FILTER_CHAIN"].next())
        return self.middleware(environ, start_response)
