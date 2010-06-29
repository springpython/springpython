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
The ldap library only works with CPython. You should NOT import this library directly.
"""
import ldap


class DefaultSpringSecurityContextSource(object):
    """
    This class is used to define the url of the ldap server. It expects a string like ldap://<server>:<port>/<baseDN>
    It provides functions to retrieve the parts
    """
    
    def __init__(self, url=None):
        self.url = url
        
    def server(self):
        """Extract the server's hostname/port from the url."""
        return self.url.split("ldap://")[1].split("/")[0].split(":")

    def base(self):
        """Extract the baseDN from the url."""
        return self.url.split("ldap://")[1].split("/")[1]

class BindAuthenticator(object):
    """
    This ldap authenticator uses binding to confirm the user's password. This means the password encoding
    depends on the ldap library's API as well as the directory server; NOT Spring Python's password
    hashing algorithms.
    """
    
    def __init__(self, context_source=None, user_dn_patterns="uid={0},ou=people"):
        self.context_source = context_source
        self.user_dn_patterns = user_dn_patterns
        self.logger = logging.getLogger("springpython.security.providers.Ldap.BindAuthenticator")

    def authenticate(self, authentication):
        """Using the user_dn_patterns, find the user's entry, and then bind to the entry using supplied credentials."""
        
        username = self.user_dn_patterns.replace("{0}", authentication.username)
        baseDn = self.context_source.base()

        parts = username.split(",")

        if len(parts) > 1:
            username = parts[0]
            baseDn = ",".join(parts[1:]) + "," + baseDn

        (host, port) = self.context_source.server()
        self.logger.debug("Opening connection to server %s/%s" % (host, int(port)))
        l = ldap.open(host, int(port))

        self.logger.debug("Searching for %s in %s" % (username, baseDn))
        result_set = l.search_s(baseDn, ldap.SCOPE_SUBTREE, username, None)

        if len(result_set) != 1:
            raise BadCredentialsException("Found %s entries at %s/%s. Should only be 1." % (len(result_set), baseDn, username))

        dn = result_set[0][0]
        self.logger.debug("Attempting to bind %s" % dn)
        try:
            l.simple_bind_s(dn, authentication.password)
            self.logger.debug("Successfully bound to server!")
            return (result_set[0],l)
        except Exception, e:
            self.logger.debug("Error %s" % e)
            raise BadCredentialsException("Invalid password")
        
class PasswordComparisonAuthenticator(object):
    """
    This ldap authenticator uses string comparison to confirm the user's password. This means a password encoder must
    be provided, or the default LdapShaPasswordEncoder will be used. It searched for the user's entry, fetches the
    password, and then does a string comparison to confirm the password.
    """

    def __init__(self, context_source=None, user_dn_patterns="uid={0},ou=people", password_attr_name="userPassword"):
        self.context_source = context_source
        self.user_dn_patterns = user_dn_patterns
        self.password_attr_name = password_attr_name
        self.encoder = LdapShaPasswordEncoder()
        self.logger = logging.getLogger("springpython.security.providers.Ldap.PasswordComparisonAuthenticator")

    def authenticate(self, authentication):
        """
        Using the user_dn_patterns, find the user's entry, and then retrieve the password field. Encode the supplied
        password with the necessary hasher, and compare to the entry.
        """

        username = self.user_dn_patterns.replace("{0}", authentication.username)
        baseDn = self.context_source.base()

        parts = username.split(",")

        if len(parts) > 1:
            username = parts[0]
            baseDn = ",".join(parts[1:]) + "," + baseDn

        (host, port) = self.context_source.server()
        self.logger.debug("Opening connection to server %s/%s" % (host, int(port)))
        l = ldap.open(host, int(port))

        self.logger.debug("Searching for %s in %s" % (username, baseDn))
        result_set = l.search_s(baseDn, ldap.SCOPE_SUBTREE, username, None)

        if len(result_set) != 1:
            raise BadCredentialsException("Found %s entries at %s/%s. Should only be 1." % (len(result_set), baseDn, username))

        self.logger.debug("Looking for attributes...%s" % result_set[0][1])
        stored_password = result_set[0][1][self.password_attr_name.lower()][0]
        self.logger.debug("Comparing passwords...")

        if self.encoder.isPasswordValid(stored_password, authentication.password, None):
            self.logger.debug("Successfully matched passwords!")
            return (result_set[0],l)
        else:
            raise BadCredentialsException("Invalid password")

class DefaultLdapAuthoritiesPopulator(object):
    """
    This ldap authorities populator follows a standard convention, where groups are created, with a member attribute, pointing
    at user entries in another part of the directory structure. It then combines ROLE_ with the name of the group, and names
    that as a granted role.
    """
    
    def __init__(self, context_source=None, group_search_base="ou=groups", group_search_filter="member={0}", group_role_attr="cn", role_prefix="ROLE_", convert_to_upper=True):
        self.logger = logging.getLogger("springpython.security.providers.Ldap.DefaultLdapAuthoritiesPopulator")
        self.context_source = context_source
        self.group_search_base = group_search_base
        self.group_search_filter = group_search_filter
        self.group_role_attr = group_role_attr 
        self.role_prefix = role_prefix
        self.convert_to_upper = convert_to_upper

    def get_granted_auths(self, user_details, l):
        group_filter = self.group_search_filter.replace("{0}", user_details[0])
        baseDn = self.group_search_base + "," + self.context_source.base()

        self.logger.debug("Searching for groups for %s" % str(user_details[0]))
        result_set = l.search_s(baseDn, ldap.SCOPE_SUBTREE, group_filter, None) 

        auths = []
        for row in result_set:
            role = self.role_prefix + row[1][self.group_role_attr][0]
            if self.convert_to_upper:
                auths.append(role.upper())
            else:
                auths.append(role)
        self.logger.debug("Authorities = %s" % auths)
        return auths
        
class LdapAuthenticationProvider(AuthenticationProvider):
    """
    This authenticator performs two steps:
        1) Authenticate the user to confirm their credentials.
        2) Lookup roles the user has stored in the directory server.
        
    It is possible to inject any type of authenticator as well as roles populator.
    
    Spring Python includes two authenticators that perform standard binding or password comparisons.
    You are able to code your own and use it instead, especially if you are using a non-conventional mechanism.
    
    Spring Python includes one role populator, based on the standard convention of defining groups elsewhere in
    the directory server's hierarchy. However, you can inject your own if you have a non-convential structure,
    such as storing the roles directly in the user's directory entry.
    """
    
    def __init__(self, ldap_authenticator=None, ldap_authorities_populator=None):
        AuthenticationProvider.__init__(self)
        self.ldap_authenticator = ldap_authenticator
        self.ldap_authorities_populator = ldap_authorities_populator
        self.logger = logging.getLogger("springpython.security.providers.Ldap.LdapAuthenticationProvider")
            
    def authenticate(self, authentication):
        user_details, l = self.ldap_authenticator.authenticate(authentication)
        from copy import deepcopy
        results = deepcopy(authentication)
        results.granted_auths = self.ldap_authorities_populator.get_granted_auths(user_details, l)
        l.unbind()
        return results
        
