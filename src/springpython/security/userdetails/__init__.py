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
from springpython.security import UsernameNotFoundException

class User(object):
    """
    Models core user information retieved by an UserDetailsService.
    """
    
    def __init__(self, username, password, enabled, accountNonExpired=True, accountNonLocked=True, credentialsNonExpired=True, authorities=None):
        self.username = username
        self.password = password
        if authorities is None:
            self.authorities = []
        else:
            self.authorities = authorities
        self.accountNonExpired = accountNonExpired
        self.accountNonLocked = accountNonLocked
        self.credentialsNonExpired = credentialsNonExpired
        self.enabled = enabled
        
    def __str__(self):
        return "Username: %s Password: [PROTECTED] Authorities: %s Enabled: %s" % (self.username, self.authorities, self.enabled)
        
class UserDetailsService(object):
    """
    Defines an interface for implementations that wish to provide data access services to the DaoAuthenticationProvider.

    The interface requires only one read-only method, which simplifies support of new data access strategies.
    """
    
    def loadUserByUsername(self, username):
        raise NotImplementedError()


class InMemoryUserDetailsService(UserDetailsService):
    def __init__(self, userMap = None):
        super(InMemoryUserDetailsService, self).__init__()
        self.userMap = userMap
        self.logger = logging.getLogger("springpython.security.userdetails.InMemoryUserDetailsService")
        
    def loadUserByUsername(self, username):
        if username in self.userMap and len(self.userMap[username][1]) > 0:
            self.logger.debug("Found %s in %s" % (username, self.userMap))
            return User(username, self.userMap[username][0], self.userMap[username][2], True, True, True, self.userMap[username][1])
        
        error = None
        if username not in self.userMap:
            error = UsernameNotFoundException("User not found in %s" % self.userMap)
        else:
            error = UsernameNotFoundException("User has no GrantedAuthority")
        self.logger.debug(error)
        raise error
