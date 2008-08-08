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
    def getUserFromCache(self, username):
        raise NotImplementedError()

    def putUserInCache(self, user):
        raise NotImplementedError()

    def removeUserFromCache(self, username):
        raise NotImplementedError()
    
class NullUserCache(UserCache):
    def getUserFromCache(self, username):
        return None

    def putUserInCache(self, user):
        pass

    def removeUserFromCache(self, username):
        pass

class AbstractUserDetailsAuthenticationProvider(AuthenticationProvider):
    def __init__(self):
        super(AbstractUserDetailsAuthenticationProvider, self).__init__()
        self.userCache = NullUserCache()
        self.hideUserNotFoundExceptions = True
        self.forcePrincipalAsString = True
        self.logger = logging.getLogger("springpython.security.providers.AbstractUserDetailsAuthenticationProvider")

    def authenticate(self, authentication):
        # Determine username
        username = authentication.username

        cacheWasUsed = True
        user = self.userCache.getUserFromCache(username)

        if user is None:
            cacheWasUsed = False

            try:
                user = self.retrieveUser(username, authentication)
            except UsernameNotFoundException, notFound:
                if self.hideUserNotFoundExceptions:
                    raise BadCredentialsException("UsernameNotFound: Bad credentials")
                else:
                    raise notFound

            if user is None:
                raise Exception("retrieveUser returned null - a violation of the interface contract")

        if not user.accountNonLocked:
            raise LockedException("User account is locked")

        if not user.enabled:
            raise DisabledException("User is disabled")

        if not user.accountNonExpired:
            raise AccountExpiredException("User account has expired")
        
        # This check must come here, as we don't want to tell users
        # about account status unless they presented the correct credentials
        try:
            self.additionalAuthenticationChecks(user, authentication)
        except AuthenticationException, exception:
            if cacheWasUsed:
                # There was a problem, so try again after checking we're using latest data (ie not from the cache)
                cacheWasUsed = False
                user = self.retrieveUser(username, authentication)
                self.additionalAuthenticationChecks(user, authentication)
            else:
                raise exception

        if not user.credentialsNonExpired:
            raise CredentialsExpiredException("User credentials have expired")

        if not cacheWasUsed:
            self.userCache.putUserInCache(user)

        principalToReturn = user
        
        if self.forcePrincipalAsString:
            principalToReturn = user.username

        return self.createSuccessAuthentication(principalToReturn, authentication, user)

    def additionalAuthenticationChecks(self, userDetails, authentication):
        raise NotImplementedError()
    
    def retrieveUser(self, username, authentication):
        raise NotImplementedError()
    
    def createSuccessAuthentication(self, principal, authentication, user):
        # Ensure we return the original credentials the user supplied,
        # so subsequent attempts are successful even with encoded passwords.
        # Also ensure we return the original getDetails(), so that future
        # authentication events after cache expiry contain the details
        result = UsernamePasswordAuthenticationToken(principal, authentication.getCredentials(), user.authorities)
        #result.details = authentication.details
        return result

class DaoAuthenticationProvider(AbstractUserDetailsAuthenticationProvider):
    def __init__(self, userDetailsService = None, passwordEncoder = PlaintextPasswordEncoder()):
        super(DaoAuthenticationProvider, self).__init__()
        self.passwordEncoder = passwordEncoder
        self.saltSource = None
        self.userDetailsService = userDetailsService
        self.includeDetailsObject = True
        self.logger = logging.getLogger("springpython.security.providers.DaoAuthenticationProvider")
        
    def retrieveUser(self, username, authentication):
        loadedUser = None

        try:
            loadedUser = self.userDetailsService.loadUserByUsername(username)
        except DataAccessException, repositoryProblem:
            raise AuthenticationServiceException(repositoryProblem)

        if loadedUser is None:
            raise AuthenticationServiceException("UserDetailsService returned null, which is an interface contract violation")

        return loadedUser

    def additionalAuthenticationChecks(self, userDetails, authentication):
        salt = None

        if self.saltSource is not None:
            salt = self.saltSource.getSalt(userDetails)
            
        if not self.passwordEncoder.isPasswordValid(userDetails.password, authentication.getCredentials(), salt):
            raise BadCredentialsException("additionalAuthenticationChecks: Bad credentials")

class SaltSource(object):
    """Provides alternative sources of the salt to use for encoding passwords."""
    
    def getSalt(self, user):
        """Returns the salt to use for the indicated user."""
        raise NotImplementedError()
    
class SystemWideSaltSource(SaltSource):
    """
    Uses a static system-wide String as the salt.

    Does not supply a different salt for each User. This means users sharing the same
    password will still have the same digested password. Of benefit is the digested passwords will at least be more protected than if stored without any salt.
    """
    
    def __init__(self, systemWideSalt = ""):
        super(SystemWideSaltSource, self).__init__()
        self.systemWideSalt = systemWideSalt
        
    def getSalt(self, user):
        return self.systemWideSalt
    
class ReflectionSaltSource(SaltSource):
    """
    Obtains a salt from a specified property of the User object.

    This allows you to subclass User and provide an additional bean getter for a salt.
    You should use a synthetic value that does not change, such as a database primary key.
    Do not use username if it is likely to change.
    """
    
    def __init__(self, userPropertyToUser = ""):
        super(ReflectionSaltSource, self).__init__()
        self.userPropertyToUse = userPropertyToUser
        
    def getSalt(self, user):
        try:
            reflectionMethod = getattr(user, self.userPropertyToUse)
            return reflectionMethod()
        except Exception, e:
            raise AuthenticationServiceException(e);


