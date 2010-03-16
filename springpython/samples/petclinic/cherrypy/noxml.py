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
import controller
import view
from springpython.config import PythonConfig
from springpython.config import Object
from springpython.database import factory
from springpython.remoting.pyro import PyroProxyFactory
from springpython.remoting.pyro import PyroServiceExporter
from springpython.security.providers import AuthenticationManager
from springpython.security.providers.dao import DaoAuthenticationProvider
from springpython.security.providers.encoding import PlaintextPasswordEncoder
from springpython.security.providers.encoding import Md5PasswordEncoder
from springpython.security.providers.encoding import ShaPasswordEncoder
from springpython.security.userdetails import InMemoryUserDetailsService
from springpython.security.userdetails.dao import DatabaseUserDetailsService
from springpython.security.vote import AffirmativeBased
from springpython.security.vote import RoleVoter
from springpython.security.web import AuthenticationProcessingFilter
from springpython.security.web import AuthenticationProcessingFilterEntryPoint
from springpython.security.cherrypy3 import CP3SessionStrategy
from springpython.security.web import ExceptionTranslationFilter
from springpython.security.cherrypy3 import CP3FilterChainProxy
from springpython.security.web import FilterSecurityInterceptor
from springpython.security.web import HttpSessionContextIntegrationFilter
from springpython.security.web import MiddlewareFilter
from springpython.security.cherrypy3 import CP3RedirectStrategy
from springpython.security.web import SimpleAccessDeniedHandler

class PetClinicClientAndServer(PythonConfig):
    """
    This is a non-XML, decorator based IoC container definition which includes
    both the client and server objects, all in one place. This is meant to demonstrate
    a bundled set of objects, running on the same machine.
    """
    def __init__(self):
        super(PetClinicClientAndServer, self).__init__()
        
    @Object
    def connectionFactory(self):
        connFactory = factory.MySQLConnectionFactory()
        connFactory.username = "springpython"
        connFactory.password = "springpython"
        connFactory.hostname = "localhost"
        connFactory.db = "petclinic"
        return connFactory
    
    @Object
    def controller(self):
        return controller.PetClinicController(self.connectionFactory())
    
    @Object
    def root(self):
        form = view.PetClinicView(controller = self.controller())
        form.filter = self.authenticationProcessingFilter()
        form.hashedUserDetailsServiceList = [self.md5UserDetailsService(),
                                             self.shaUserDetailsService()]
        form.authenticationManager = self.authenticationManager()
        form.redirectStrategy = self.redirectStrategy()
	form.httpContextFilter = self.httpContextFilter()
        return form
    
    @Object
    def userDetailsService(self):
        return DatabaseUserDetailsService(self.connectionFactory())    
    
    @Object
    def userDetailsService2(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.user_dict = {"jcarter": ("password6", ["VET_ANY"], True)}
        return userDetailsService

    @Object
    def userDetailsService3(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.user_dict = {"jcoleman": ("password5", ["CUSTOMER_ANY"], True)}
        return userDetailsService

    @Object
    def plainEncoder(self):
        return PlaintextPasswordEncoder()

    @Object
    def md5Encoder(self):
        return Md5PasswordEncoder()

    @Object
    def shaEncoder(self):
        return ShaPasswordEncoder()

    @Object
    def md5UserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService2()
        userDetailsService.encoder = self.md5Encoder()
        return userDetailsService

    @Object
    def shaUserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService3()
        userDetailsService.encoder = self.shaEncoder()
        return userDetailsService

    @Object
    def plainAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.userDetailsService()
        provider.password_encoder = self.plainEncoder()
        return provider   

    @Object
    def md5AuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.md5UserDetailsService()
        provider.password_encoder = self.md5Encoder()
        return provider

    @Object
    def shaAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.shaUserDetailsService()
        provider.password_encoder = self.shaEncoder()
        return provider

    @Object
    def authenticationManager(self):
        authManager = AuthenticationManager()
        authManager.auth_providers = []
        authManager.auth_providers.append(self.plainAuthenticationProvider())
        authManager.auth_providers.append(self.md5AuthenticationProvider())
        authManager.auth_providers.append(self.shaAuthenticationProvider())
        return authManager

    @Object
    def vetRoleVoter(self):
        return RoleVoter(role_prefix = "VET")

    @Object
    def customerRoleVoter(self):
        return RoleVoter(role_prefix = "CUSTOMER")

    @Object
    def ownerVoter(self):
        return controller.OwnerVoter(controller = self.controller())

    @Object
    def accessDecisionManager(self):
        adm = AffirmativeBased()
        adm.allow_if_all_abstain = False
        adm.access_decision_voters = []
        adm.access_decision_voters.append(self.vetRoleVoter())
        adm.access_decision_voters.append(self.customerRoleVoter())
        adm.access_decision_voters.append(self.ownerVoter())
        return adm
    
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
    def authenticationProcessingFilter(self):
        filter = AuthenticationProcessingFilter()
        filter.auth_manager = self.authenticationManager()
        filter.alwaysReauthenticate = False
        return filter

    @Object
    def filterSecurityInterceptor(self):
        filter = FilterSecurityInterceptor()
        filter.auth_manager = self.authenticationManager()
        filter.access_decision_mgr = self.accessDecisionManager()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        filter.obj_def_source = [
                                         ("/vets.*", ["VET_ANY"]),
                                         ("/editOwner.*", ["VET_ANY", "OWNER"]),
                                         ("/.*", ["VET_ANY", "CUSTOMER_ANY"])
                                         ]
        return filter

    @Object
    def authenticationProcessingFilterEntryPoint(self):
        filter = AuthenticationProcessingFilterEntryPoint()
        filter.loginFormUrl = "/login"
        filter.redirectStrategy = self.redirectStrategy()
        return filter
        
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
    def filterChainProxy(self):
        return CP3FilterChainProxy(filterInvocationDefinitionSource = 
            [
            ("/images.*", []),
            ("/html.*",   []),
            ("/login.*",  ["httpContextFilter"]),
            ("/.*",       ["httpContextFilter",
                           "exceptionTranslationFilter",
                           "authenticationProcessingFilter",
                           "filterSecurityInterceptor"])
            ])

class PetClinicServerOnly(PythonConfig):
    """
    This is a non-XML, decorator based IoC container definition which includes
    both the server objects. This demonstrates splitting up client and server
    objects to run on different machines.
    """
    def __init__(self):
        super(PetClinicServerOnly, self).__init__()

    @Object
    def connectionFactory(self):
        connFactory = factory.MySQLConnectionFactory()
        connFactory.username = "springpython"
        connFactory.password = "springpython"
        connFactory.hostname = "localhost"
        connFactory.db = "petclinic"
        return connFactory
    
    @Object
    def remoteController(self):
        remoteController = controller.PetClinicController()
        remoteController.connection_factory = self.connectionFactory()
        return remoteController
    
    @Object
    def controllerExporter(self):
        exporter = PyroServiceExporter()
        exporter.service_name = "Controller"
        exporter.service = self.remoteController()
        return exporter
    
    @Object
    def remoteUserDetailsService(self):
        userDetailsService = DatabaseUserDetailsService()
        userDetailsService.dataSource = self.connectionFactory()
        return userDetailsService

    @Object
    def userDetailsServiceExporter(self):
        exporter = PyroServiceExporter()
        exporter.service_name = "UserDetails"
        exporter.service = self.remoteUserDetailsService()
        return exporter

class PetClinicClientOnly(PythonConfig):
    """
    This is a non-XML, decorator based IoC container definition which includes
    both the server objects. This demonstrates splitting up client and server
    objects to run on different machines.
    """
    def __init__(self):
        super(PetClinicClientOnly, self).__init__()

    @Object
    def controller(self):
        proxy = PyroProxyFactory()
        proxy.service_url = "PYROLOC://localhost:7766/Controller"
        return proxy
        
    @Object
    def view(self):
        petClientView = view.PetClinicView()
        petClientView.controller = self.controller()
        return petClientView

    @Object
    def root(self):
        form = view.PetClinicView(self.controller())    
        form.filter = self.authenticationProcessingFilter()
        form.controller = self.controller()
        form.hashedUserDetailsServiceList = []
        form.hashedUserDetailsServiceList.append(self.md5UserDetailsService())
        form.hashedUserDetailsServiceList.append(self.shaUserDetailsService())
        form.authenticationManager = self.authenticationManager()
        form.redirectStrategy = self.redirectStrategy()
	form.httpContextFilter = self.httpContextFilter()
	return form

    @Object
    def userDetailsService(self):
        userDetailsService = PyroProxyFactory()
        userDetailsService.service_url = "PYROLOC://localhost:7766/UserDetails"
        return userDetailsService
    
    @Object
    def userDetailsService2(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.user_dict = {"jcarter": ("password6", ["VET_ANY"], True)}
        return userDetailsService

    @Object
    def userDetailsService3(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.user_dict = {"jcoleman": ("password5", ["CUSTOMER_ANY"], True)}
        return userDetailsService
    
    @Object
    def md5Encoder(self):
        return Md5PasswordEncoder()

    @Object
    def shaEncoder(self):
        return ShaPasswordEncoder()

    @Object
    def md5UserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService2()
        userDetailsService.encoder = self.md5Encoder()
        return userDetailsService    

    @Object
    def shaUserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService3()
        userDetailsService.encoder = self.shaEncoder()
        return userDetailsService

    @Object
    def plainEncoder(self):
        return PlaintextPasswordEncoder()

    @Object
    def plainAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.userDetailsService()
        provider.password_encoder = self.plainEncoder()
        return provider

    @Object
    def md5AuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.md5UserDetailsService()
        provider.password_encoder = self.md5Encoder()
        return provider

    @Object
    def shaAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.user_details_service = self.shaUserDetailsService()
        provider.password_encoder = self.shaEncoder()
        return provider

    @Object
    def authenticationManager(self):
        provider = AuthenticationManager()
        provider.auth_providers = []
        provider.auth_providers.append(self.plainAuthenticationProvider())
        provider.auth_providers.append(self.md5AuthenticationProvider())
        provider.auth_providers.append(self.shaAuthenticationProvider())
        return provider

    @Object
    def vetRoleVoter(self):
        return RoleVoter(role_prefix = "VET")

    @Object
    def customerRoleVoter(self):
        return RoleVoter(role_prefix = "CUSTOMER")

    @Object
    def ownerVoter(self):
        return controller.OwnerVoter(controller = self.controller())

    @Object
    def accessDecisionManager(self):
        adm = AffirmativeBased()
        adm.allow_if_all_abstain_decisions = False
        adm.access_decision_voters = []
        adm.access_decision_voters.append(self.vetRoleVoter())
        adm.access_decision_voters.append(self.customerRoleVoter())
        adm.access_decision_voters.append(self.ownerVoter())
        return adm
    
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
    def authenticationProcessingFilter(self):
        filter = AuthenticationProcessingFilter()
        filter.auth_manager = self.authenticationManager()
        filter.alwaysReauthenticate = False
        return filter

    @Object
    def filterSecurityInterceptor(self):
        filter = FilterSecurityInterceptor()
        filter.validate_config_attributes = False
        filter.auth_manager = self.authenticationManager()
        filter.access_decision_mgr = self.accessDecisionManager()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        filter.obj_def_source = [("/vets.*", ["VET_ANY"]),
                                         ("/editOwner.*", ["VET_ANY", "OWNER"]),
                                         ("/.*", ["VET_ANY", "CUSTOMER_ANY"])]
        return filter

    @Object
    def authenticationProcessingFilterEntryPoint(self):
        filter = AuthenticationProcessingFilterEntryPoint()
        filter.loginFormUrl = "/login"
        filter.redirectStrategy = self.redirectStrategy()
        return filter
    
    @Object
    def accessDeniedHandler(self):
        filter = SimpleAccessDeniedHandler()
        filter.errorPage = "/accessDenied"
        filter.redirectStrategy = self.redirectStrategy()
        return filter
        
    @Object
    def exceptionTranslationFilter(self):
        filter = ExceptionTranslationFilter()
        filter.authenticationEntryPoint = self.authenticationProcessingFilterEntryPoint()
        filter.accessDeniedHandler = self.accessDeniedHandler()
        return filter
    
    @Object
    def filterChainProxy(self):
        return CP3FilterChainProxy(filterInvocationDefinitionSource = 
            [
            ("/images.*", []),
            ("/html.*",   []),
            ("/login.*",  ["httpContextFilter"]),
            ("/.*",       ["httpContextFilter",
                           "exceptionTranslationFilter",
                           "authenticationProcessingFilter",
                           "filterSecurityInterceptor"])
            ])

