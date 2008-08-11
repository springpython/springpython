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
from springpython.context import DecoratorBasedApplicationContext
from springpython.context import component
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
from springpython.security.web import CherryPySessionStrategy
from springpython.security.web import ExceptionTranslationFilter
from springpython.security.web import FilterChainProxy
from springpython.security.web import FilterSecurityInterceptor
from springpython.security.web import HttpSessionContextIntegrationFilter
from springpython.security.web import MiddlewareFilter
from springpython.security.web import RedirectStrategy
from springpython.security.web import SimpleAccessDeniedHandler

class PetClinicClientAndServer(DecoratorBasedApplicationContext):
    """
    This is a non-XML, decorator based IoC container definition which includes
    both the client and server components, all in one place. This is meant to demonstrate
    a bundled set of components, running on the same machine.
    """
    def __init__(self):
        DecoratorBasedApplicationContext.__init__(self)
        
    @component
    def connectionFactory(self):
        connFactory = factory.MySQLConnectionFactory()
        connFactory.username = "springpython"
        connFactory.password = "springpython"
        connFactory.hostname = "localhost"
        connFactory.db = "petclinic"
        return connFactory
    
    @component
    def controller(self):
        return controller.PetClinicController(self.connectionFactory())   
    
    @component
    def root(self):
        return view.PetClinicView(self.controller())    
    
    @component
    def userDetailsService(self):
        return DatabaseUserDetailsService(self.connectionFactory())    
    
    @component
    def userDetailsService2(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.userMap = {"jcarter": ("password6", ["VET_ANY"], True)}
        return userDetailsService

    @component
    def userDetailsService3(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.userMap = {"jcoleman": ("password5", ["CUSTOMER_ANY"], True)}
        return userDetailsService

    @component
    def plainEncoder(self):
        return PlaintextPasswordEncoder()

    @component
    def md5Encoder(self):
        return Md5PasswordEncoder()

    @component
    def shaEncoder(self):
        return ShaPasswordEncoder()

    @component
    def md5UserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService2()
        userDetailsService.encoder = self.md5Encoder()
        return userDetailsService

    @component
    def shaUserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService3()
        userDetailsService.encoder = self.shaEncoder()
        return userDetailsService

    @component
    def plainAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.userDetailsService = self.userDetailsService()
        provider.passwordEncoder = self.plainEncoder()
        return provider   

    @component
    def md5AuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.userDetailsService = self.md5UserDetailsService()
        provider.passwordEncoder = self.md5Encoder()
        return provider

    @component
    def shaAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.userDetailsService = self.shaUserDetailsService()
        provider.passwordEncoder = self.shaEncoder()
        return provider

    @component
    def authenticationManager(self):
        authManager = AuthenticationManager()
        authManager.authenticationProviderList = []
        authManager.authenticationProviderList.append(self.plainAuthenticationProvider())
        authManager.authenticationProviderList.append(self.md5AuthenticationProvider())
        authManager.authenticationProviderList.append(self.shaAuthenticationProvider())
        return authManager

    @component
    def vetRoleVoter(self):
        return RoleVoter(rolePrefix = "VET")

    @component
    def customerRoleVoter(self):
        return RoleVoter(rolePrefix = "CUSTOMER")

    @component
    def ownerVoter(self):
        return controller.OwnerVoter(controller = self.controller())

    @component
    def accessDecisionManager(self):
        adm = AffirmativeBased()
        adm.allowIfAllAbstain = False
        adm.accessDecisionVoterList = []
        adm.accessDecisionVoterList.append(self.vetRoleVoter())
        adm.accessDecisionVoterList.append(self.customerRoleVoter())
        adm.accessDecisionVoterList.append(self.ownerVoter())
        return adm
    
    @component
    def cherrypySessionStrategy(self):
        return CherryPySessionStrategy()

    @component
    def redirectStrategy(self):
        return RedirectStrategy()
    
    @component
    def httpContextFilter(self):
        filter = HttpSessionContextIntegrationFilter()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        return filter
    
    @component
    def authenticationProcessingFilter(self):
        filter = AuthenticationProcessingFilter()
        filter.authenticationManager = self.authenticationManager()
        filter.alwaysReauthenticate = False
        return filter

    @component
    def filterSecurityInterceptor(self):
        filter = FilterSecurityInterceptor()
        filter.authenticationManager = self.authenticationManager()
        filter.accessDecisionManager = self.accessDecisionManager()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        filter.objectDefinitionSource = [
                                         ("/vets.*", ["VET_ANY"]),
                                         ("/editOwner.*", ["VET_ANY", "OWNER"]),
                                         ("/.*", ["VET_ANY", "CUSTOMER_ANY"])
                                         ]
        return filter

    @component
    def exceptionFilter(self):
        filter = MiddlewareFilter()
        filter.clazz = "paste.evalexception.middleware.EvalException"
        filter.appAttribute = "application"
        return filter 
    
    @component
    def authenticationProcessingFilterEntryPoint(self):
        filter = AuthenticationProcessingFilterEntryPoint()
        filter.loginFormUrl = "/login"
        filter.redirectStrategy = self.redirectStrategy()
        return filter
        
    @component
    def accessDeniedHandler(self):
        handler = SimpleAccessDeniedHandler()
        handler.errorPage = "/accessDenied"
        handler.redirectStrategy = self.redirectStrategy()
        return handler
        
    @component
    def exceptionTranslationFilter(self):
        filter = ExceptionTranslationFilter()
        filter.authenticationEntryPoint = self.authenticationProcessingFilterEntryPoint()
        filter.accessDeniedHandler = self.accessDeniedHandler()
        return filter
    
    @component
    def filterChainProxy(self):
        return FilterChainProxy(filterInvocationDefinitionSource = 
            [
            ("/images.*", [self.exceptionFilter(), ]),
            ("/html.*",   [self.exceptionFilter(), ]),
            ("/login.*",  [self.exceptionFilter(), self.httpContextFilter()]),
            ("/.*",       [self.exceptionFilter(),
                           self.httpContextFilter(),
                           self.exceptionTranslationFilter(),
                           self.authenticationProcessingFilter(),
                           self.filterSecurityInterceptor()])
            ])

    @component
    def filterChainProxy2(self):
        return FilterChainProxy(filterInvocationDefinitionSource = 
            [
            ("/images.*", [self.exceptionFilter(), self.root()]),
            ("/html.*",   [self.exceptionFilter(), self.root()]),
            ("/login.*",  [self.exceptionFilter(), self.httpContextFilter(), self.root()]),
            ("/.*",       [self.exceptionFilter(),
                           self.httpContextFilter(),
                           self.exceptionTranslationFilter(),
                           self.authenticationProcessingFilter(),
                           self.filterSecurityInterceptor(), self.root()])
            ])

    @component
    def loginForm(self):
        loginForm = view.CherryPyAuthenticationForm()
        loginForm.filter = self.authenticationProcessingFilter()
        loginForm.controller = self.controller()
        loginForm.hashedUserDetailsServiceList = [self.md5UserDetailsService(),
                                                  self.shaUserDetailsService()]
        loginForm.authenticationManager = self.authenticationManager()
        loginForm.redirectStrategy = self.redirectStrategy()
        return loginForm

class PetClinicServerOnly(DecoratorBasedApplicationContext):
    """
    This is a non-XML, decorator based IoC container definition which includes
    both the server components. This demonstrates splitting up client and server
    components to run on different machines.
    """
    def __init__(self):
        DecoratorBasedApplicationContext.__init__(self)

    @component
    def connectionFactory(self):
        connFactory = factory.MySQLConnectionFactory()
        connFactory.username = "springpython"
        connFactory.password = "springpython"
        connFactory.hostname = "localhost"
        connFactory.db = "petclinic"
        return connFactory
    
    @component
    def remoteController(self):
        remoteController = controller.PetClinicController()
        remoteController.connectionFactory = self.connectionFactory()
        return remoteController
    
    @component
    def controllerExporter(self):
        exporter = PyroServiceExporter()
        exporter.serviceName = "Controller"
        exporter.service = self.remoteController()
        return exporter
    
    @component
    def remoteUserDetailsService(self):
        userDetailsService = DatabaseUserDetailsService()
        userDetailsService.dataSource = self.connectionFactory()
        return userDetailsService

    @component
    def userDetailsServiceExporter(self):
        exporter = PyroServiceExporter()
        exporter.serviceName = "UserDetails"
        exporter.service = self.remoteUserDetailsService()
        return exporter

class PetClinicClientOnly(DecoratorBasedApplicationContext):
    """
    This is a non-XML, decorator based IoC container definition which includes
    both the server components. This demonstrates splitting up client and server
    components to run on different machines.
    """
    def __init__(self):
        DecoratorBasedApplicationContext.__init__(self)

    @component
    def controller(self):
        proxy = PyroProxyFactory()
        proxy.serviceUrl = "PYROLOC://localhost:7766/Controller"
        return proxy
        
    @component
    def view(self):
        petClientView = view.PetClinicView()
        petClientView.controller = self.controller()
        return petClientView

    @component
    def userDetailsService(self):
        userDetailsService = PyroProxyFactory()
        userDetailsService.serviceUrl = "PYROLOC://localhost:7766/UserDetails"
        return userDetailsService
    
    @component
    def userDetailsService2(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.userMap = {"jcarter": ("password6", ["VET_ANY"], True)}
        return userDetailsService

    @component
    def userDetailsService3(self):
        userDetailsService = InMemoryUserDetailsService()
        userDetailsService.userMap = {"jcoleman": ("password5", ["CUSTOMER_ANY"], True)}
        return userDetailsService
    
    @component
    def md5Encoder(self):
        return Md5PasswordEncoder()

    @component
    def shaEncoder(self):
        return ShaPasswordEncoder()

    @component
    def md5UserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService2()
        userDetailsService.encoder = self.md5Encoder()
        return userDetailsService    

    @component
    def shaUserDetailsService(self):
        userDetailsService = controller.PreencodingUserDetailsService()
        userDetailsService.wrappedUserDetailsService = self.userDetailsService3()
        userDetailsService.encoder = self.shaEncoder()
        return userDetailsService

    @component
    def plainEncoder(self):
        return PlaintextPasswordEncoder()

    @component
    def plainAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.userDetailsService = self.userDetailsService()
        provider.passwordEncoder = self.plainEncoder()
        return provider

    @component
    def md5AuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.userDetailsService = self.md5UserDetailsService()
        provider.passwordEncoder = self.md5Encoder()
        return provider

    @component
    def shaAuthenticationProvider(self):
        provider = DaoAuthenticationProvider()
        provider.userDetailsService = self.shaUserDetailsService()
        provider.passwordEncoder = self.shaEncoder()
        return provider

    @component
    def authenticationManager(self):
        provider = AuthenticationManager()
        provider.authenticationProviderList = []
        provider.authenticationProviderList.append(self.plainAuthenticationProvider())
        provider.authenticationProviderList.append(self.md5AuthenticationProvider())
        provider.authenticationProviderList.append(self.shaAuthenticationProvider())
        return provider

    @component
    def vetRoleVoter(self):
        return RoleVoter(rolePrefix = "VET")

    @component
    def customerRoleVoter(self):
        return RoleVoter(rolePrefix = "CUSTOMER")

    @component
    def ownerVoter(self):
        return controller.OwnerVoter(controller = self.controller())

    @component
    def accessDecisionManager(self):
        adm = AffirmativeBased()
        adm.allowIfAllAbstainDecisions = False
        adm.accessDecisionVoterList = []
        adm.accessDecisionVoterList.append(self.vetRoleVoter())
        adm.accessDecisionVoterList.append(self.customerRoleVoter())
        adm.accessDecisionVoterList.append(self.ownerVoter())
        return adm
    
    @component
    def cherrypySessionStrategy(self):
        return CherryPySessionStrategy()

    @component
    def redirectStrategy(self):
        return RedirectStrategy()
    
    @component
    def httpContextFilter(self):
        filter = HttpSessionContextIntegrationFilter()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        return filter
    
    @component
    def authenticationProcessingFilter(self):
        filter = AuthenticationProcessingFilter()
        filter.authenticationManager = self.authenticationManager()
        filter.alwaysReauthenticate = False
        return filter

    @component
    def filterSecurityInterceptor(self):
        filter = FilterSecurityInterceptor()
        filter.validateConfigAttributes = False
        filter.authenticationManager = self.authenticationManager()
        filter.accessDecisionManager = self.accessDecisionManager()
        filter.sessionStrategy = self.cherrypySessionStrategy()
        filter.objectDefinitionSource = [("/vets.*", ["VET_ANY"]),
                                         ("/editOwner.*", ["VET_ANY", "OWNER"]),
                                         ("/.*", ["VET_ANY", "CUSTOMER_ANY"])]
        return filter

    @component
    def exceptionFilter(self):
        filter = MiddlewareFilter()
        filter.clazz = "paste.evalexception.middleware.EvalException"
        filter.appAttribute = "application"
        return filter
    
    @component
    def authenticationProcessingFilterEntryPoint(self):
        filter = AuthenticationProcessingFilterEntryPoint()
        filter.loginFormUrl = "/login"
        filter.redirectStrategy = self.redirectStrategy()
        return filter
    
    @component
    def accessDeniedHandler(self):
        filter = SimpleAccessDeniedHandler()
        filter.errorPage = "/accessDenied"
        filter.redirectStrategy = self.redirectStrategy()
        return filter
        
    @component
    def exceptionTranslationFilter(self):
        filter = ExceptionTranslationFilter()
        filter.authenticationEntryPoint = self.authenticationProcessingFilterEntryPoint()
        filter.accessDeniedHandler = self.accessDeniedHandler()
        return filter
    
    @component
    def filterChainProxy(self):
        return FilterChainProxy(filterInvocationDefinitionSource = 
            [
            ("/images.*", [self.exceptionFilter(), ]),
            ("/html.*",   [self.exceptionFilter(), ]),
            ("/login.*",  [self.exceptionFilter(), self.httpContextFilter()]),
            ("/.*",       [self.exceptionFilter(),
                           self.httpContextFilter(),
                           self.exceptionTranslationFilter(),
                           self.authenticationProcessingFilter(),
                           self.filterSecurityInterceptor()])
            ])

    @component
    def loginForm(self):
        loginForm = view.CherryPyAuthenticationForm()
        loginForm.filter = self.authenticationProcessingFilter()
        loginForm.controller = self.controller()
        loginForm.hashedUserDetailsServiceList = []
        loginForm.hashedUserDetailsServiceList.append(self.md5UserDetailsService())
        loginForm.hashedUserDetailsServiceList.append(self.shaUserDetailsService())
        loginForm.authenticationManager = self.authenticationManager()
        loginForm.redirectStrategy = self.redirectStrategy()
        return loginForm
