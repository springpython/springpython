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
import re
from springpython.security import AuthenticationCredentialsNotFoundException
from springpython.security.context import SecurityContextHolder
from springpython.aop import MethodInterceptor
from springpython.aop import MethodInvocation

logger = logging.getLogger("springpython.security.intercept")

class ObjectDefinitionSource(object):
    """Implemented by classes that store and can identify the ConfigAttributeDefinition that applies to a given secure object invocation."""

    def get_attributes(obj):
        """Accesses the ConfigAttributeDefinition that applies to a given secure object."""
        raise NotImplementedError()

    def get_conf_attr_defs():
        """If available, all of the ConfigAttributeDefinitions defined by the implementing class."""
        raise NotImplementedError()

    def supports(cls):
        """Indicates whether the ObjectDefinitionSource implementation is able to provide ConfigAttributeDefinitions for
        the indicated secure object type."""
        raise NotImplementedError()

class InterceptorStatusToken(object):
    """
    A return object received by AbstractSecurityInterceptor subclasses.

    This class reflects the status of the security interception, so that the final call to
    AbstractSecurityInterceptor.after_invocation(InterceptorStatusToken, Object) can tidy up correctly.
    """
    
    def __init__(self, authentication = None, attr = None, secure_obj = None):
        self.authentication = authentication
        self.attr = attr
        self.secure_obj = secure_obj

class AbstractSecurityInterceptor(object):
    """
    Abstract class that implements security interception for secure objects.
    
    It will implements the proper handling of secure object invocations, being:
    
       1. Obtain the Authentication object from the SecurityContextHolder.
       2. Determine if the request relates to a secured or public invocation by looking up the secure object request
          against the ObjectDefinitionSource.
       3. For an invocation that is secured (there is a ConfigAttributeDefinition for the secure object invocation):
             1. If either the Authentication.isAuthenticated() returns false, or the alwaysReauthenticate is true,
                authenticate the request against the configured AuthenticationManager. When authenticated, replace
                the Authentication object on the SecurityContextHolder with the returned value.
             2. Authorize the request against the configured AccessDecisionManager.
             (3. Perform any run-as replacement via the configured RunAsManager. FUTURE)
             4. Pass control back to the concrete subclass, which will actually proceed with executing the object.
                An InterceptorStatusToken is returned so that after the subclass has finished proceeding with execution
                of the object, its finally clause can ensure the AbstractSecurityInterceptor is re-called and tidies up
                correctly.
             5. The concrete subclass will re-call the AbstractSecurityInterceptor via the after_invocation(InterceptorStatusToken, Object) method.
             (6. If the RunAsManager replaced the Authentication object, return the SecurityContextHolder to the object
                that existed after the call to AuthenticationManager. FUTURE)
             7. If an AfterInvocationManager is defined, invoke the invocation manager and allow it to replace the object
                due to be returned to the caller.
       (4. For an invocation that is public (there is no ConfigAttributeDefinition for the secure object invocation):
             1. As described above, the concrete subclass will be returned an InterceptorStatusToken which is subsequently
                re-presented to the AbstractSecurityInterceptor after the secure object has been executed. The
                AbstractSecurityInterceptor will take no further action when its after_invocation(InterceptorStatusToken, Object)
                is called. FUTURE)
       5. Control again returns to the concrete subclass, along with the Object that should be returned to the caller. The
          subclass will then return that result or exception to the original caller.
    """
    
    def __init__(self, auth_manager = None, access_decision_mgr = None, obj_def_source = None):
        self.auth_manager = auth_manager
        self.access_decision_mgr = access_decision_mgr
        self.obj_def_source = obj_def_source
        self.logger = logging.getLogger("springpython.security.intercept.AbstractSecurityInterceptor")

    def obtain_obj_def_source(self):
       raise NotImplementedError()

    def before_invocation(self, invocation):
        attr = self.obtain_obj_def_source().get_attributes(invocation)
        if attr:
            self.logger.debug("Secure object: %s; ConfigAttributes: %s" % (invocation, attr))
            if not SecurityContextHolder.getContext().authentication:
                raise AuthenticationCredentialsNotFoundException("An Authentication object was not found in the security credentials")
            if not SecurityContextHolder.getContext().authentication.isAuthenticated():
                authenticated = self.auth_manager.authenticate(SecurityContextHolder.getContext().authentication)
                self.logger.debug("Successfully Authenticated: " + authenticated)
                SecurityContextHolder.getContext().authentication = authenticated
            else:
                authenticated = SecurityContextHolder.getContext().authentication
                self.logger.debug("Previously Authenticated: %s" % authenticated)
            self.access_decision_mgr.decide(authenticated, invocation, attr)
            self.logger.debug("Authorization successful")
            return InterceptorStatusToken(authenticated, attr, invocation)
        else:
            return None
    
    def after_invocation(self, token, results):
        """As a minimum, this needs to pass the results right on through. Subclasses can extend this behavior
        to utilize the token information."""
        return results

class AbstractMethodDefinitionSource(ObjectDefinitionSource):
    """Abstract implementation of ObjectDefinitionSource."""
    
    def get_attributes(self, obj):
        try:
            module_name = obj.instance.__module__
            class_name = obj.instance.__class__.__name__
            method_name = obj.method_name
            full_method_name = "%s.%s.%s" % (module_name, class_name, method_name)
            return self.lookupAttributes(full_method_name)
        except AttributeError:
            raise TypeError("obj must be a MethodInvocation")

    def lookupAttributes(self, method):
        raise NotImplementedError()

class MethodDefinitionMap(AbstractMethodDefinitionSource):
    """
    Stores an obj_def_source for each method signature defined in a object.
    
    Regular expressions are used to match a method request in a ConfigAttributeDefinition. The order of registering
    the regular expressions is very important. The system will identify the first matching regular expression for a given
    method. It will not proceed to evaluate later regular expressions if a match has already been found.
    
    Accordingly, the most specific regular expressions should be registered first, with the most general regular expressions registered last.    
    """
    
    def __init__(self, obj_def_source):
        self.obj_def_source = obj_def_source

    def lookupAttributes(self, method):
        if self.obj_def_source:
            for rule, attr in self.obj_def_source:
                if re.compile(rule).match(method):
                    return attr 
        return None

class MethodSecurityInterceptor(MethodInterceptor, AbstractSecurityInterceptor):
    """
    Provides security interception of Spring Python AOP-based method invocations.

    The ObjectDefinitionSource required by this security interceptor is of type MethodDefinitionMap.

    Refer to AbstractSecurityInterceptor for details on the workflow.   
    """
    
    def __init__(self):
        MethodInterceptor.__init__(self)
        AbstractSecurityInterceptor.__init__(self)
        self.validate_config_attributes = False
        self.obj_def_source = None

    def __setattr__(self, name, value):
        if name == "obj_def_source" and value is not None:
            self.__dict__[name] = MethodDefinitionMap(value)
        else:
            self.__dict__[name] = value

    def obtain_obj_def_source(self):
        return self.obj_def_source

    def invoke(self, invocation):
        token = self.before_invocation(invocation)
        results = None
        try:
            results = invocation.proceed()
        finally:
            results = self.after_invocation(token, results)
        return results
