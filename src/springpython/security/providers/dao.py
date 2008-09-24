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
from springpython.database import DataAccessException
from springpython.security import AuthenticationException
from springpython.security import AuthenticationServiceException
from springpython.security import BadCredentialsException
from springpython.security import DisabledException
from springpython.security import UsernameNotFoundException
from springpython.security.providers import AuthenticationProvider
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.providers.encoding import PlaintextPasswordEncoder

class UserCache(object):
    def get_user(self, username):
        raise NotImplementedError()

    def put_user(self, user):
        raise NotImplementedError()

    def remove_user(self, username):
        raise NotImplementedError()
    
class NullUserCache(UserCache):
    def get_user(self, username):
        return None

    def put_user(self, user):
        pass

    def remove_user(self, username):
        pass

class AbstractUserDetailsAuthenticationProvider(AuthenticationProvider):
    def __init__(self):
        super(AbstractUserDetailsAuthenticationProvider, self).__init__()
        self.user_cache = NullUserCache()
        self.hide_user_not_found_exceptions = True
        self.force_principal_as_str = True
        self.logger = logging.getLogger("springpython.security.providers.AbstractUserDetailsAuthenticationProvider")

    def authenticate(self, authentication):
        # Determine username
        username = authentication.username

        cache_was_used = True
        user = self.user_cache.get_user(username)

        if user is None:
            cache_was_used = False

            try:
                user = self.retrieve_user(username, authentication)
            except UsernameNotFoundException, notFound:
                if self.hide_user_not_found_exceptions:
                    raise BadCredentialsException("UsernameNotFound: Bad credentials")
                else:
                    raise notFound

            if user is None:
                raise Exception("retrieve_user returned null - a violation of the interface contract")

        if not user.accountNonLocked:
            raise LockedException("User account is locked")

        if not user.enabled:
            raise DisabledException("User is disabled")

        if not user.accountNonExpired:
            raise AccountExpiredException("User account has expired")
        
        # This check must come here, as we don't want to tell users
        # about account status unless they presented the correct credentials
        try:
            self.additional_auth_checks(user, authentication)
        except AuthenticationException, exception:
            if cache_was_used:
                # There was a problem, so try again after checking we're using latest data (ie not from the cache)
                cache_was_used = False
                user = self.retrieve_user(username, authentication)
                self.additional_auth_checks(user, authentication)
            else:
                raise exception

        if not user.credentialsNonExpired:
            raise CredentialsExpiredException("User credentials have expired")

        if not cache_was_used:
            self.user_cache.put_user(user)

        principal_to_return = user
        
        if self.force_principal_as_str:
            principal_to_return = user.username

        return self.create_success_auth(principal_to_return, authentication, user)

    def additional_auth_checks(self, user_details, authentication):
        raise NotImplementedError()
    
    def retrieve_user(self, username, authentication):
        raise NotImplementedError()
    
    def create_success_auth(self, principal, authentication, user):
        # Ensure we return the original credentials the user supplied,
        # so subsequent attempts are successful even with encoded passwords.
        # Also ensure we return the original getDetails(), so that future
        # authentication events after cache expiry contain the details
        result = UsernamePasswordAuthenticationToken(principal, authentication.getCredentials(), user.authorities)
        #result.details = authentication.details
        return result

class DaoAuthenticationProvider(AbstractUserDetailsAuthenticationProvider):
    def __init__(self, user_details_service = None, password_encoder = PlaintextPasswordEncoder()):
        super(DaoAuthenticationProvider, self).__init__()
        self.password_encoder = password_encoder
        self.salt_source = None
        self.user_details_service = user_details_service
        self.include_details_obj = True
        self.logger = logging.getLogger("springpython.security.providers.DaoAuthenticationProvider")
        
    def retrieve_user(self, username, authentication):
        loaded_user = None

        try:
            loaded_user = self.user_details_service.load_user(username)
        except DataAccessException, repositoryProblem:
            raise AuthenticationServiceException(repositoryProblem)

        if loaded_user is None:
            raise AuthenticationServiceException("UserDetailsService returned null, which is an interface contract violation")

        return loaded_user

    def additional_auth_checks(self, user_details, authentication):
        salt = None

        if self.salt_source is not None:
            salt = self.salt_source.get_salt(user_details)
            
        if not self.password_encoder.isPasswordValid(user_details.password, authentication.getCredentials(), salt):
            raise BadCredentialsException("additional_auth_checks: Bad credentials")

class SaltSource(object):
    """Provides alternative sources of the salt to use for encoding passwords."""
    
    def get_salt(self, user):
        """Returns the salt to use for the indicated user."""
        raise NotImplementedError()
    
class SystemWideSaltSource(SaltSource):
    """
    Uses a static system-wide String as the salt.

    Does not supply a different salt for each User. This means users sharing the same
    password will still have the same digested password. Of benefit is the digested passwords will at least be more protected than if stored without any salt.
    """
    
    def __init__(self, system_wide_salt = ""):
        super(SystemWideSaltSource, self).__init__()
        self.system_wide_salt = system_wide_salt
        
    def get_salt(self, user):
        return self.system_wide_salt
    
class ReflectionSaltSource(SaltSource):
    """
    Obtains a salt from a specified property of the User object.

    This allows you to subclass User and provide an additional bean getter for a salt.
    You should use a synthetic value that does not change, such as a database primary key.
    Do not use username if it is likely to change.
    """
    
    def __init__(self, user_prop_to_use = ""):
        super(ReflectionSaltSource, self).__init__()
        self.user_prop_to_use = user_prop_to_use
        
    def get_salt(self, user):
        try:
            reflectionMethod = getattr(user, self.user_prop_to_use)
            return reflectionMethod()
        except Exception, e:
            raise AuthenticationServiceException(e);


