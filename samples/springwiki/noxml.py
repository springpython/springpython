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

import controller
import view

from springpython.config import *
from springpython.security.cherrypy3 import *
from springpython.security.web import *
from springpython.security.providers import *
from springpython.security.providers.dao import *
from springpython.security.userdetails import *
from springpython.security.vote import *

class SpringWikiClientAndServer(PythonConfig):
    def __init__(self):
        super(SpringWikiClientAndServer, self).__init__()
        
    @Object
    def controller(self):
        return controller.SpringWikiController()
    
    @Object
    def read(self):
        wikiView = view.Springwiki()
        wikiView.controller = self.controller()
        return wikiView
    
    @Object
    def userDetailsService2(self):
        service = InMemoryUserDetailsService()
        service.user_dict = {"writer": ("comein", ["VET_ANY"], True)}
        return service

    @Object
    def plainEncoder(self):
        return PlaintextPasswordEncoder()

    @Object
    def plainAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.userDetailsService2()
        provider.password_encoder = self.plainEncoder()
        return provider
        

    @Object
    def authenticationManager(self):
        manager = AuthenticationManager()
        manager.auth_providers = [self.plainAuthenticationProvider()]
        return manager
        
    @Object
    def authenticationProcessingFilter(self):
        filter = AuthenticationProcessingFilter()
        filter.auth_manager = self.authenticationManager()
        filter.alwaysReauthenticate = False
        return filter
        
    @Object
    def cherrypySessionStrategy(self):
        return CP3SessionStrategy()
        	
    @Object
    def redirectStrategy(self):
        return CP3RedirectStrategy()
        
    @Object      
    def httpContextFilter(self):
        filter = HttpSessionContextIntegrationFilter()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        return filter

    @Object
    def authenticationProcessingFilterEntryPoint(self):
        filter_point = AuthenticationProcessingFilterEntryPoint()
        filter_point.loginFormUrl = "/login"
        filter_point.redirectStrategy = self.redirectStrategy()
        return filter_point	
    @Object
    def accessDeniedHandler(self):
        handler = SimpleAccessDeniedHandler()
        handler.errorPage = "/accessDenied"
        handler.redirectStrategy = self.redirectStrategy()
        return handler

    @Object
    def exceptionTranslationFilter(self):
        filter = ExceptionTranslationFilter()
        filter.authenticationEntryPoint = self.authenticationProcessingFilterEntryPoint()
        filter.accessDeniedHandler = self.accessDeniedHandler()
        return filter

    @Object
    def filterSecurityInterceptor(self):
        interceptor = FilterSecurityInterceptor()
        interceptor.validate_config_attributes = False
        interceptor.auth_manager = self.authenticationManager()
        interceptor.access_decision_mgr = self.accessDecisionManager()
        interceptor.sessionStrategy = self.cherrypySessionStrategy()
        interceptor.obj_def_source = [("/.*", ["VET_ANY", "CUSTOMER_ANY"])]
        return interceptor

    @Object
    def vetRoleVoter(self):
        voter = RoleVoter()
        voter.role_prefix = "VET"
        return voter

    @Object
    def customerRoleVoter(self):
        voter = RoleVoter()
        voter.role_prefix = "CUSTOMER"
        return voter
        	
    @Object
    def accessDecisionManager(self):
        policy = AffirmativeBased()
        policy.allow_if_all_abstain = False
        policy.access_decision_voters = [self.vetRoleVoter(), self.customerRoleVoter()]
        return policy

    @Object
    def filterChainProxy(self):
        proxy = CP3FilterChainProxy()
        proxy.filterInvocationDefinitionSource = [
                                ("/login.*",
                                    ["httpContextFilter"]),
                                ("/.*",
                                    ["httpContextFilter",
                                    "exceptionTranslationFilter", 
                                    "authenticationProcessingFilter",
                                    "filterSecurityInterceptor"]
                                 )]
        return proxy

    @Object
    def loginForm(self):
        form = view.CherryPyAuthenticationForm()
        form.filter = self.authenticationProcessingFilter()
        form.controller = self.controller()
        form.authenticationManager = self.authenticationManager()
        form.redirectStrategy = self.redirectStrategy()
        form.httpContextFilter = self.httpContextFilter()
        return form

