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
import pickle
import unittest
from pmock import *
from springpython.security import BadCredentialsException
from springpython.security.context import SecurityContext
from springpython.security.context import SecurityContextHolder
from springpython.security.providers import AuthenticationManager
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.providers.dao import DaoAuthenticationProvider
from springpython.security.userdetails import InMemoryUserDetailsService
from springpython.security.web import Filter
from springpython.security.web import FilterChain
from springpython.security.web import HttpSessionContextIntegrationFilter
from springpython.security.web import ExceptionTranslationFilter
from springpython.security.web import AuthenticationProcessingFilter
from springpython.security.web import FilterSecurityInterceptor
from springpython.security.web import FilterChainProxy
from springpython.security.web import SessionStrategy

class StubSessionStrategy(SessionStrategy):
    """
    This is a stand-in for any web-based HTTP Session solution. It is a simple in-memory dictionary
    used to serve the role of holding session data during any tests.
    """
    def __init__(self):
        SessionStrategy.__init__(self)
        self.sessionData = {}
        
    def getHttpSession(self, environ):
        return self.sessionData

    def setHttpSession(self, key, value):
	self.sessionData[key] = value

class StubAuthenticationFilter(Filter):
    """
    This is a pass-through filter, used to help test HttpSessionContextIntegrationFilter. That filter
    expects there to be another filter in place that will authenticate credentials, and in turn modify them.
    This filter checks if the incoming (default) credentials are authenticated, and if not, sets them
    as such. Then it passes on to the next filter.
    """
    def __call__(self, environ, start_response):
        if not SecurityContextHolder.getContext().authentication.isAuthenticated():
            SecurityContextHolder.getContext().authentication.setAuthenticated(True)
        return self.doNextFilter(environ, start_response)
    
class WebInterfaceTestCase(unittest.TestCase):
    def testSessionStrategy(self):
        sessionStrategy = SessionStrategy()
        environ = {}
        self.assertRaises(NotImplementedError, sessionStrategy.getHttpSession, environ)
        
class FilterTestCase(MockTestCase):
    def testIteratingThroughASimpleFilterChain(self):
        filterChain = FilterChain()
        self.assertEquals(0, len(filterChain.chain))
        
        httpSessionContextIntegrationFilter = HttpSessionContextIntegrationFilter()
        exceptionTranslationFilter = ExceptionTranslationFilter()
        authenticationProcessFilter = AuthenticationProcessingFilter()
        filterSecurityInterceptor = FilterSecurityInterceptor()
        
        filterChain.addFilter(httpSessionContextIntegrationFilter)
        filterChain.addFilter(exceptionTranslationFilter)
        filterChain.addFilter(authenticationProcessFilter)
        filterChain.addFilter(filterSecurityInterceptor)
        
        chain = filterChain.getFilterChain()
        self.assertEquals(httpSessionContextIntegrationFilter, chain.next())
        self.assertEquals(exceptionTranslationFilter, chain.next())
        self.assertEquals(authenticationProcessFilter, chain.next())
        self.assertEquals(filterSecurityInterceptor, chain.next())
        self.assertRaises(StopIteration, chain.next)

    def testHttpSessionContextIntegrationFilter(self):
        def start_response():
            pass
        def application(environ, start_response):
            return ["Success"]

        environ = {}
        environ["PATH_INFO"] = "/index.html"
        
        sessionStrategy = StubSessionStrategy()
        httpSessionContextIntegrationFilter = HttpSessionContextIntegrationFilter(sessionStrategy)
        # HttpSessionContextIntegrationFilter expects another filter after it to alter the credentials.
        stubAuthenticationFilter = StubAuthenticationFilter()
         
        filterChainProxy = FilterChainProxy()
        filterChainProxy.filterInvocationDefinitionSource = [("/.*", [httpSessionContextIntegrationFilter, stubAuthenticationFilter])]
        filterChainProxy.application = application
        
        self.assertEquals(["Success"], filterChainProxy(environ, start_response))
        self.assertEquals(["Success"], filterChainProxy(environ, start_response))
        
        httpSession = sessionStrategy.getHttpSession(environ)
        httpSession[httpSessionContextIntegrationFilter.SPRINGPYTHON_SECURITY_CONTEXT_KEY] = pickle.dumps("Bad credentials")
        self.assertEquals(["Success"], filterChainProxy(environ, start_response))

    def testFilterChainProxyWithMixedURLs(self):
        """
        This test goes through the FilterChainProxy, and proves that it takes differing routes through filters
        based on URL pattern matching.
        """
        class PassthroughFilter1(Filter):
            """This filter inserts a simple value to prove it was used."""
            def __call__(self, environ, start_response):
                environ["PASSTHROUGH_FILTER1"] = True
                return self.doNextFilter(environ, start_response)

        class PassthroughFilter2(Filter):
            """This filter inserts a simple value to prove it was used."""
            def __call__(self, environ, start_response):
                environ["PASSTHROUGH_FILTER2"] = True
                return self.doNextFilter(environ, start_response)
    
        def start_response():
            pass
        def application(environ, start_response):
            return ["Success"]
        
        filterChainProxy = FilterChainProxy()
        filterChainProxy.filterInvocationDefinitionSource = [("/.*html", [PassthroughFilter1()]), ("/.*jsp", [PassthroughFilter2()])]
        filterChainProxy.application = application

        environ = {}
        environ["PATH_INFO"] = "/index.html"
        filterChainProxy(environ, start_response)
        self.assertTrue("PASSTHROUGH_FILTER1" in environ)
        self.assertTrue("PASSTHROUGH_FILTER2" not in environ)
        
        environ = {}
        environ["PATH_INFO"] = "/index.jsp"
        filterChainProxy(environ, start_response)
        self.assertTrue("PASSTHROUGH_FILTER1" not in environ)
        self.assertTrue("PASSTHROUGH_FILTER2" in environ)
        
        filterChainProxy2 = FilterChainProxy(filterInvocationDefinitionSource=[("/.*html", [PassthroughFilter1()]), ("/.*jsp", [PassthroughFilter2()])])
        filterChainProxy2.application = application

        environ = {}
        environ["PATH_INFO"] = "/index.html"
        filterChainProxy2(environ, start_response)
        self.assertTrue("PASSTHROUGH_FILTER1" in environ)
        self.assertTrue("PASSTHROUGH_FILTER2" not in environ)
        
        environ = {}
        environ["PATH_INFO"] = "/index.jsp"
        filterChainProxy2(environ, start_response)
        self.assertTrue("PASSTHROUGH_FILTER1" not in environ)
        self.assertTrue("PASSTHROUGH_FILTER2" in environ)
        
    def testAuthenticationProcessingFilterWithGoodPassword(self):
        def start_response():
            pass
        def application(environ, start_response):
            return ["Success"]

        environ = {}
        environ["PATH_INFO"] = "/index.html"
        
        inMemoryUserDetailsService = InMemoryUserDetailsService()
        inMemoryUserDetailsService.user_dict = {"user1": ("good_password", ["role1", "blue"], True)}
        inMemoryDaoAuthenticationProvider = DaoAuthenticationProvider()
        inMemoryDaoAuthenticationProvider.user_details_service = inMemoryUserDetailsService
        inMemoryDaoAuthenticationManager = AuthenticationManager([inMemoryDaoAuthenticationProvider])

        authenticationFilter = AuthenticationProcessingFilter()
        authenticationFilter.auth_manager = inMemoryDaoAuthenticationManager
        authenticationFilter.alwaysReauthenticate = False
        
        token = UsernamePasswordAuthenticationToken("user1", "good_password", None)
        self.assertFalse(token.isAuthenticated())
        
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = token
        
        filterChainProxy = FilterChainProxy()
        filterChainProxy.filterInvocationDefinitionSource = [("/.*", [authenticationFilter])]
        filterChainProxy.application = application
        
        self.assertEquals(["Success"], filterChainProxy(environ, start_response))        
        self.assertTrue(SecurityContextHolder.getContext().authentication.isAuthenticated())

        self.assertEquals(["Success"], filterChainProxy(environ, start_response))
        self.assertTrue(SecurityContextHolder.getContext().authentication.isAuthenticated())
        
    def testAuthenticationProcessingFilterWithBadPassword(self):
        def start_response():
            pass
        def application(environ, start_response):
            return ["Success"]

        environ = {}
        environ["PATH_INFO"] = "/index.html"
        
        inMemoryUserDetailsService = InMemoryUserDetailsService()
        inMemoryUserDetailsService.user_dict = {"user1": ("good_password", ["role1", "blue"], True)}
        inMemoryDaoAuthenticationProvider = DaoAuthenticationProvider()
        inMemoryDaoAuthenticationProvider.user_details_service = inMemoryUserDetailsService
        inMemoryDaoAuthenticationManager = AuthenticationManager([inMemoryDaoAuthenticationProvider])

        authenticationFilter = AuthenticationProcessingFilter()
        authenticationFilter.auth_manager = inMemoryDaoAuthenticationManager
        authenticationFilter.alwaysReauthenticate = False
        
        token = UsernamePasswordAuthenticationToken("user1", "bad_password", None)
        self.assertFalse(token.isAuthenticated())
        
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = token
        
        filterChainProxy = FilterChainProxy()
        filterChainProxy.filterInvocationDefinitionSource = [("/.*", [authenticationFilter])]
        filterChainProxy.application = application
        self.assertRaises(BadCredentialsException, filterChainProxy, environ, start_response)
        self.assertFalse(SecurityContextHolder.getContext().authentication.isAuthenticated())
        
