"""
   Copyright 2006-2009 SpringSource (http://springsource.com), All Rights Reserved

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
import re
import sys
from springpython.security import AuthenticationException
from springpython.security import AuthenticationServiceException
from springpython.security import BadCredentialsException
from springpython.security import DisabledException
from springpython.security import UsernameNotFoundException
from springpython.security.providers import AuthenticationProvider
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.providers.dao import AbstractUserDetailsAuthenticationProvider
from springpython.security.providers.encoding import LdapShaPasswordEncoder


"""
The ldap library only works with Jython. You should NOT import this library directly.

Due to the lack of a pure Python library, this version uses Spring Security/Spring LDAP jar files to perform
authentication and LDAP lookups.
"""
import java
import org.springframework.security.ldap.DefaultSpringSecurityContextSource
import org.springframework.security.ldap.populator.DefaultLdapAuthoritiesPopulator
import org.springframework.security.providers.ldap.authenticator.BindAuthenticator
import org.springframework.security.providers.ldap.authenticator.PasswordComparisonAuthenticator
import org.springframework.security.providers.UsernamePasswordAuthenticationToken
from jarray import array

print """
WARNING WARNING WARNING WARNING
===============================
This doesn't yet work. There is some issue with Jython.
See http://bugs.jython.org/issue1489 and http://jira.springframework.org/browse/SESPRINGPYTHONPY-121 for more details.
===============================
WARNING WARNING WARNING WARNING
"""

class DefaultSpringSecurityContextSource(object):
    def __init__(self, url):
        self._context = org.springframework.security.ldap.DefaultSpringSecurityContextSource(url)
        java.lang.Thread.currentThread().setContextClassLoader(self._context.getClass().getClassLoader())
        self._context.afterPropertiesSet()
        
class BindAuthenticator(object):
    def __init__(self, context_source=None, user_dn_patterns="uid={0},ou=people"):
        self.context_source = context_source
        self.user_dn_patterns = user_dn_patterns
        self.logger = logging.getLogger("springpython.security.providers.Ldap.BindAuthenticator")
        self._authenticator = None

    def authenticate(self, authentication):
        if self._authenticator is None:
            self._authenticator = org.springframework.security.providers.ldap.authenticator.BindAuthenticator(self.context_source._context)
            self._authenticator.setUserDnPatterns(array([self.user_dn_patterns], java.lang.String))
            self._authenticator.afterPropertiesSet()
            #java.lang.Thread.currentThread().setContextClassLoader(self._authenticator.getClass().getClassLoader())
            #print "BindAuthenticator class loader %s" % self._authenticator.getClass().getClassLoader()
        token = org.springframework.security.providers.UsernamePasswordAuthenticationToken(authentication.username, authentication.password)
        return self._authenticator.authenticate(token)
        
class PasswordComparisonAuthenticator(object):
    def __init__(self, context_source=None, user_dn_patterns="uid={0},ou=people", password_attr_name="userPassword"):
        self.context_source = context_source
        self.user_dn_patterns = user_dn_patterns
        self.password_attr_name = password_attr_name
        self.encoder = LdapShaPasswordEncoder()
        self.logger = logging.getLogger("springpython.security.providers.Ldap.PasswordComparisonAuthenticator")

    def authenticate(self, authentication):
        if jython:
            raise Exception("This code doesn't work inside Jython.")

class DefaultLdapAuthoritiesPopulator(object):
    def __init__(self, context_source=None, group_search_base="ou=groups", group_search_filter="(member={0})", group_role_attr="cn", role_prefix="ROLE_", convert_to_upper=True):
        self.logger = logging.getLogger("springpython.security.providers.Ldap.DefaultLdapAuthoritiesPopulator")
        self.context_source = context_source
        self.group_search_base = group_search_base
        self.group_search_filter = group_search_filter
        self.group_role_attr = group_role_attr 
        self.role_prefix = role_prefix
        self.convert_to_upper = convert_to_upper
        self._populator = org.springframework.security.ldap.populator.DefaultLdapAuthoritiesPopulator(self.context_source._context, self.group_search_base)
        #java.lang.Thread.currentThread().setContextClassLoader(self._populator.getClass().getClassLoader())
        self._populator.setGroupSearchFilter(self.group_search_filter)
        self._populator.setGroupRoleAttribute(self.group_role_attr)
        self._populator.setRolePrefix(self.role_prefix)
        self._populator.setConvertToUpperCase(self.convert_to_upper)
        print "LdapAuthoritiesPopulator class loader %s" % self._populator.getClass().getClassLoader()

    def get_granted_auths(self, user_details, username):
        results = self._populator.getGrantedAuthorities(user_details, username)
        print results
        return results
        
class LdapAuthenticationProvider(AuthenticationProvider):
    def __init__(self, ldap_authenticator=None, ldap_authorities_populator=None):
        AuthenticationProvider.__init__(self)
        self.ldap_authenticator = ldap_authenticator
        self.ldap_authorities_populator = ldap_authorities_populator
        self.logger = logging.getLogger("springpython.security.providers.Ldap.LdapAuthenticationProvider")
            
    def authenticate(self, authentication):
        user_details = self.ldap_authenticator.authenticate(authentication)
        print "Context class loader %s" % user_details.getClass().getClassLoader()
        from copy import deepcopy
        results = deepcopy(authentication)
        results.granted_auths = self.ldap_authorities_populator.get_granted_auths(user_details, authentication.username)
        results.setAuthenticated(True)
        l.unbind()
        return results
        
