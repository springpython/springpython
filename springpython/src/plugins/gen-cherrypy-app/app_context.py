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
from springpython.config import PythonConfig
from springpython.config import Object
from springpython.context import ApplicationContext
from springpython.security import AuthenticationException
from springpython.security.context import SecurityContext
from springpython.security.context import SecurityContextHolder
from springpython.security.providers import AuthenticationManager
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.providers.dao import DaoAuthenticationProvider
from springpython.security.providers.encoding import PlaintextPasswordEncoder
from springpython.security.providers.encoding import Md5PasswordEncoder
from springpython.security.providers.encoding import ShaPasswordEncoder
from springpython.security.userdetails import InMemoryUserDetailsService
from springpython.security.userdetails import UserDetailsService
from springpython.security.userdetails.dao import DatabaseUserDetailsService
from springpython.security.vote import AffirmativeBased
from springpython.security.vote import RoleVoter
from springpython.security.web import AuthenticationProcessingFilter
from springpython.security.web import AuthenticationProcessingFilterEntryPoint
from springpython.security.web import CP3FilterChainProxy
from springpython.security.web import CP3RedirectStrategy
from springpython.security.web import CP3SessionStrategy
from springpython.security.web import ExceptionTranslationFilter
from springpython.security.web import FilterSecurityInterceptor
from springpython.security.web import HttpSessionContextIntegrationFilter
from springpython.security.web import SimpleAccessDeniedHandler
import view

class ${properName}Configuration(PythonConfig):
    def __init__(self):
        super(${properName}Configuration, self).__init__()

    @Object
    def root(self):
        """This is the main object defined for the web application."""
        form = view.${properName}View()
        form.filter = self.authenticationProcessingFilter()
        form.hashedUserDetailsServiceList = [self.shaUserDetailsService()]
        form.authenticationManager = self.authenticationManager()
        form.redirectStrategy = self.redirectStrategy()
	form.httpSessionContextIntegrationFilter = self.httpSessionContextIntegrationFilter()
        return form
    
    @Object
    def userDetailsService(self):
        """This user details service uses a pre-built, in-memory for demonstration purposes only. Do NOT use in a
        production system!!!"""
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.user_dict = {"jcoleman": ("password5", ["CUSTOMER_ANY"], True)}
        return userDetailsService

    @Object
    def shaEncoder(self):
        """This password encoder uses the SHA hashing algorithm."""
        return ShaPasswordEncoder()

    @Object
    def shaUserDetailsService(self):
        """This wrapper around a user details service will publish an unhashed user details service with hashed passwords,
        allowing a demo set of users be stored in unhashed format. Do NOT use this for production systems!!!"""
        userDetailsService = PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService()
        userDetailsService.encoder = self.shaEncoder()
        return userDetailsService

    @Object
    def shaAuthenticationProvider(self):
        """This authentication provider takes a user details service and links it with a password encoder, to hash
        passwords before comparing with the user details service."""
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.shaUserDetailsService()
        provider.password_encoder = self.shaEncoder()
        return provider

    @Object
    def authenticationManager(self):
        """This authentication manager contains the list of authentication providers used to confirm a user's identity."""
        authManager = AuthenticationManager()
        authManager.auth_providers = []
        authManager.auth_providers.append(self.shaAuthenticationProvider())
        return authManager

    @Object
    def accessDecisionManager(self):
        """This AccessDecisionManager decides based on what ROLE_xxx the current user has."""
        adm = AffirmativeBased()
        adm.allow_if_all_abstain = False
        adm.access_decision_voters = []
        adm.access_decision_voters.append(RoleVoter()) 
        return adm
    
    @Object
    def cherrypySessionStrategy(self):
        """This is the concrete mechanism used to activate HttpSession data."""
        return CP3SessionStrategy()

    @Object
    def redirectStrategy(self):
        """This is the concrete mechanism used by several components to redirect the browser."""
        return CP3RedirectStrategy()
    
    @Object
    def httpSessionContextIntegrationFilter(self):
        """This filter is used to move SecurityContext to/from the HttpSession of the web requests."""
        filter = HttpSessionContextIntegrationFilter()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        return filter
    
    @Object
    def authenticationProcessingFilter(self):
        """This defines the filter for confirming a user's identity."""
        filter = AuthenticationProcessingFilter()
        filter.auth_manager = self.authenticationManager()
        filter.alwaysReauthenticate = False
        return filter

    @Object
    def filterSecurityInterceptor(self):
        """This is the collection of rules used to determine if logged in users have permission to access a page. It
        works top to bottom, until it finds a URI pattern match."""
        filter = FilterSecurityInterceptor()
        filter.auth_manager = self.authenticationManager()
        filter.access_decision_mgr = self.accessDecisionManager()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        filter.obj_def_source = [
                                         ("/.*", ["ROLE_ANY"])
                                         ]
        return filter

    @Object
    def authenticationProcessingFilterEntryPoint(self):
        """This entry point defines where to redirect users not already logged into the system."""
        filter = AuthenticationProcessingFilterEntryPoint()
        filter.loginFormUrl = "/login"
        filter.redirectStrategy = self.redirectStrategy()
        return filter
        
    @Object
    def accessDeniedHandler(self):
        """This handler defines the location and mechanism used to get there, when processing a security exception."""
        handler = SimpleAccessDeniedHandler()
        handler.errorPage = "/accessDenied"
        handler.redirectStrategy = self.redirectStrategy()
        return handler
        
    @Object
    def exceptionTranslationFilter(self):
        """This filter allows re-routing to an Access Denied page in the event of a security exception."""
        filter = ExceptionTranslationFilter()
        filter.authenticationEntryPoint = self.authenticationProcessingFilterEntryPoint()
        filter.accessDeniedHandler = self.accessDeniedHandler()
        return filter
    
    @Object
    def filterChainProxy(self):
        """This is the main entry point for security chain. It works from top to bottom, until it finds a match,
        based on the URI of the request, deciding what chain of filters to apply."""
        return CP3FilterChainProxy(filterInvocationDefinitionSource = 
            [
            ("/images.*", []),
            ("/html.*",   []),
            ("/login.*",  ["httpSessionContextIntegrationFilter"]),
            ("/.*",       ["httpSessionContextIntegrationFilter",
                           "exceptionTranslationFilter",
                           "authenticationProcessingFilter",
                           "filterSecurityInterceptor"])
            ])

class PreencodingUserDetailsService(UserDetailsService):
    """
    This user details service allows passwords to be created that are un-encoded, but
    will be encoded before the authentication step occurs. This is for demonstration
    purposes only, specifically to show the password encoders being plugged in.
    """
    def __init__(self, wrappedUserDetailsService = None, encoder = None):
        UserDetailsService.__init__(self)
        self.wrappedUserDetailsService = wrappedUserDetailsService
        self.encoder = encoder
        self.logger = logging.getLogger("${name}.app_context.PreencodingUserDetailsService")
        
    def load_user(self, username):
        user = self.wrappedUserDetailsService.load_user(username)
        user.password = self.encoder.encodePassword(user.password, None)
        self.logger.debug("Pre-converting %s's password to hashed format of %s, before authentication happens." % (username, user.password))
        return user
    
    def __str__(self):
        return "%s %s" % (self.encoder, self.wrappedUserDetailsService)


