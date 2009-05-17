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
from springpython.database.core import DatabaseTemplate
from springpython.database.core import RowMapper
from springpython.security import UsernameNotFoundException
from springpython.security.userdetails import User
from springpython.security.userdetails import UserDetailsService

class DatabaseUserDetailsService(UserDetailsService):
    """
    Retrieves user details (username, password, enabled flag, and authorities) from a database location.
 
    A default database structure is assumed, (see DEF_USERS_BY_USERNAME_QUERY and DEF_AUTHORITIES_BY_USERNAME_QUERY,
    which most users of this class will need to override, if using an existing scheme. This may be done by
    setting the default query strings used. If this does not provide enough flexibility, another strategy
    would be to subclass this class and override relevant parts.

    In order to minimise backward compatibility issues, this DAO does not recognise the expiration of user
    accounts or the expiration of user credentials. However, it does recognise and honour the user enabled/disabled
    column.   
    """
    
    DEF_USERS_BY_USERNAME_QUERY = "SELECT username,password,enabled FROM users WHERE username = ?"
    DEF_AUTHORITIES_BY_USERNAME_QUERY = "SELECT username,authority FROM authorities WHERE username = ?"

    class UsersByUsernameMapping(RowMapper):
        """A row handler that processes one user entry."""
        def map_row(self, row, metadata=None):
            username = row[0]
            password = row[1]
            enabled = row[2]
            return User(username, password, enabled, True, True, True, ["HOLDER"])
    
    class AuthoritiesByUsernameMapping(RowMapper):
        """A row handler that processes one granted authority for a given user."""
        def __init__(self, role_prefix):
            self.role_prefix = role_prefix
            
        def map_row(self, row, metadata=None):
            return self.role_prefix + row[1]
    
    def __init__(self, dataSource = None):
        super(DatabaseUserDetailsService, self).__init__()
        self.users_by_username_query = self.DEF_USERS_BY_USERNAME_QUERY
        self.auth_by_username_query = self.DEF_AUTHORITIES_BY_USERNAME_QUERY
        self.dataSource = dataSource
        self.role_prefix = ""
        self.username_based_pk = True
        self.logger = logging.getLogger("springpython.security.userdetails.DatabaseUserDetailsService")
        
    def load_user(self, username):
        dt = DatabaseTemplate(self.dataSource)
        
        users = dt.query(self.users_by_username_query, (username,), self.UsersByUsernameMapping())

        if len(users) == 0:
            raise UsernameNotFoundException("User not found")

        user = users[0] # First item in list, first column of tuple, containing no GrantedAuthority[]
        dbAuths = dt.query(self.auth_by_username_query, (user.username,), self.AuthoritiesByUsernameMapping(self.role_prefix))
        self.add_custom_authorities(user.username, dbAuths)

        if len(dbAuths) == 0:
            raise UsernameNotFoundException("User has no GrantedAuthority")

        auths = [dbAuth for dbAuth in dbAuths]
        return_username = user.username

        if not self.username_based_pk:
            return_username = username
            
        self.logger.debug("Just fetched %s from the database" % user)
        return User(return_username, user.password, user.enabled, True, True, True, auths)
    
    def add_custom_authorities(self, username, authorities):
        pass
