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

class SecurityException(Exception):
    pass

class AuthenticationException(SecurityException):
    pass

class BadCredentialsException(AuthenticationException):
    pass

class DisabledException(AuthenticationException):
    pass

class LockedException(AuthenticationException):
    pass

class AccessDeniedException(SecurityException):
    pass

class AuthenticationCredentialsNotFoundException(AuthenticationException):
    pass

class UsernameNotFoundException(BadCredentialsException):
    pass

class AuthenticationServiceException(AccessDeniedException):
    pass


import sys, os, os.path
if "java" in sys.platform.lower():
    from glob import glob
    jars = os.path.join(glob("%s/lib/*.jar" % os.path.dirname(os.path.abspath(__file__))))
    sys.path.extend(jars)

