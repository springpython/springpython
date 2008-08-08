"""
   Copyright 2006-2008 Greg L. Turnquist, All Rights Reserved

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
from springpython.security import AuthenticationException
from springpython.security import BadCredentialsException
from springpython.security import DisabledException

class ProviderNotFoundException(AuthenticationException):
    """
    An exception thrown when a list of providers are polled for a security decision,
    and none of them supports the request.
    """
    
    pass

class Authentication:
    """
    Abstract representation of credential data. The premise is that username and password
    are populated, and after authentication this record is returned with the third attribute,
    granted authorities, populated.
    """
    
    def __init__(self):
        self.__authenticated = False

    def isAuthenticated(self):
        return self.__authenticated

    def setAuthenticated(self, authenticated):
        self.__authenticated = authenticated
        
    def getCredentials(self):
        raise NotImplementedError()

    def __str__(self):
        raise AuthenticationException("You should be using a concrete authentication object")

class UsernamePasswordAuthenticationToken(Authentication):
    """
    A basic concrete version of authentication. Works for most scenarios.
    """
    
    def __init__(self, username = None, password = None, grantedAuthorities = None):
        Authentication.__init__(self)
        self.username = username
        self.password = password
        if grantedAuthorities is None:
            self.grantedAuthorities = []
        else:
            self.grantedAuthorities = grantedAuthorities
            
    def getCredentials(self):
        return self.password

    def __str__(self):
        return "[UsernamePasswordAuthenticationToken] User: [%s] Password: [PROTECTED] GrantedAuthorities: %s Authenticated: %s" % \
            (self.username, self.grantedAuthorities, self.isAuthenticated())

class AuthenticationManager:
    """
    Iterates an Authentication request through a list of AuthenticationProviders. 
    
    AuthenticationProviders are tried in order until one provides a non-null response.
    A non-null response indicates the provider had authority to decide on the authentication
    request and no further providers are tried. If an AuthenticationException is thrown by
    a provider, it is retained until subsequent providers are tried. If a subsequent provider
    successfully authenticates the request, the earlier authentication exception is disregarded
    and the successful authentication will be used. If no subsequent provider provides a
    non-null response, or a new AuthenticationException, the last AuthenticationException
    received will be used. If no provider returns a non-null response, or indicates it can
    even process an Authentication, the AuthenticationManager will throw a ProviderNotFoundException.
    """
    
    def __init__(self, authenticationProviderList = []):
        self.authenticationProviderList = authenticationProviderList
        self.logger = logging.getLogger("springpython.security.providers.AuthenticationManager")

    def authenticate(self, authentication):
        """
        Attempts to authenticate the passed Authentication object, returning a fully
        populated Authentication object (including granted authorities) if successful.
        """
        authenticationException = ProviderNotFoundException()
        for authenticationProvider in self.authenticationProviderList:
            try:
                results = authenticationProvider.authenticate(authentication)
                if results:
                    results.setAuthenticated(True)
                    return results
            except DisabledException, e: # Disabled means account found, but invalid
                raise e
            except AuthenticationException, e:
                authenticationException = e
        raise authenticationException

class AuthenticationProvider(object):
    """
    Indicates a class can process a specific Authentication implementation.
    """
    
    def authenticate(self, authentication):
        """
        Performs authentication with the same contract as AuthenticationManager.authenticate(Authentication).
        """
        raise NotImplementedError()
    
    def supports(self, authentication):
        """
        Returns true if this AuthenticationProvider supports the indicated Authentication object.
        """
        raise NotImplementedError()

class LdapAuthenticationProvider(AuthenticationProvider):
    """
    An AuthenticationProvider implementation that provides integration with an LDAP server.
    """
    
    pass

class InMemoryAuthenticationProvider(AuthenticationProvider):
    """
    Retrieves user details from an in-memory list created by the bean context.
    DEPRECATED since v0.2: Use InMemoryUserDetailsService with a DaoAuthenticationProvider instead. 
    """
    
    def __init__(self, userMap = None):
        super(InMemoryAuthenticationProvider, self).__init__()
        if not userMap:
            self.userMap = {}
        else:
            self.userMap = userMap

    def authenticate(self, authentication):
        if self.supports(authentication):
            if authentication.username not in self.userMap:
                raise BadCredentialsException("Account %s does NOT exist" % authentication.username)
            (password, authentication.grantedAuthorities, enabled) = self.userMap[authentication.username]
            if not enabled:
                raise DisabledException("Account %s is disabled" % authentication.username)
            if password != authentication.password:
                raise BadCredentialsException("Account %s has invalid password" % authentication.username)
            return authentication
            
    def supports(self, authentication):
        """
        This provider can handle UsernamePasswordAuthenticationTokens
        """
        return isinstance(authentication, UsernamePasswordAuthenticationToken)

       