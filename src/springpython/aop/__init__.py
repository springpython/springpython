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
import copy
import logging
import re
import types
from springpython.aop import utils

class Pointcut(object):
    """Interface defining where to apply an aspect."""
    def class_filter(self):
        raise NotImplementedError()
    def method_matcher(self):
        raise NotImplementedError()

class MethodMatcher(object):
    """Interface defining how to apply aspects based on methods."""
    def matches_method_and_target(self, method, targetClass, args):
        raise NotImplementedError()

class MethodInterceptor(object):
    """Interface defining "around" advice."""
    def invoke(self, invocation):
        raise NotImplementedError()

class MethodInvocation(object):
    """Encapsulation of invoking a method on a proxied service. It iterates throgh the list of interceptors by using
    a generator."""
    def __init__(self, instance, method_name, args, kwargs, interceptors):
        self.instance = instance
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self.intercept_stack = copy.copy(interceptors)
        self.intercept_stack.append(FinalInterceptor())
        self.logger = logging.getLogger("springpython.aop.MethodInvocation")

    def getInterceptor(self):
        """This is a generator to proceed through the stack of interceptors. By using generator convention, code may
        proceed in a nested fashion, versus a for-loop which would act in a chained fashion."""
        for interceptor in self.intercept_stack:
            yield interceptor

    def proceed(self):
        """This is the method every interceptor should call in order to continue down the chain of interceptors."""
        interceptor = self.iterator.next()
        self.logger.debug("Calling %s.%s(%s, %s)" % (interceptor.__class__.__name__, self.method_name, self.args, self.kwargs))
        return interceptor.invoke(self)

    def __getattr__(self, name):
        """This only deals with method invocations. Attributes are dealt with by the AopProxy, and don't every reach this
        block of code."""
        self.iterator = self.getInterceptor()
        self.method_name = name
        return self

    def __call__ (self, *args, **kwargs):
        """This method converts this from being a stored object into a callable class. This is effectively like a metaclass
        that dispatches calls to proceed through a stack of interceptors."""
        self.args = args
        self.kwargs = kwargs
        return self.proceed()

    def dump_interceptors(self, level = logging.INFO):
        """DEBUG: Method used to dump the stack of interceptors in order of execution."""
        for interceptor in self.intercept_stack:
            self.logger.log(level, "Interceptor stack: %s" % interceptor.__class__.__name__)

class RegexpMethodPointcutAdvisor(Pointcut, MethodMatcher, MethodInterceptor):
    """
    This is a combination PointCut/MethodMatcher/MethodInterceptor. It allows associating one or more
    defined advices with a set of regular expression patterns.
    """
    def __init__(self, advice = None, patterns = None):
        Pointcut.__init__(self)
        MethodMatcher.__init__(self)
        self.advice = advice
        if not patterns:
            self.patterns = []
        else:
            self.patterns = patterns
        self.logger = logging.getLogger("springpython.aop.RegexpMethodPointcut")

    def init_patterns(self):
        """Precompile the regular expression pattern matcher list."""
        self.compiled_patterns = {}
        for pattern in self.patterns:
            self.compiled_patterns[pattern] = re.compile(pattern)

    def matches_method_and_target(self, method, target_class, args):
        """Iterate through all patterns, checking for a match. Calls the pattern matcher against "class.method_name"."""
        for pointcut_pattern in self.patterns:
            if (self.matches_pattern(target_class + "." + method, pointcut_pattern)):
                return True
        return False

    def matches_pattern(self, method_name, pointcut_pattern):
        """Uses a pre-built dictionary of regular expression patterns to check for a matcch."""
        if self.compiled_patterns[pointcut_pattern].match(method_name):
            matched = True
        else:
            matched = False
        self.logger.debug("Candidate is [%s]; pattern is [%s]; matched=%s" % (method_name, pointcut_pattern, matched))
        return matched

    def invoke(self, invocation):
        """Compares "class.method" against regular expression pattern and if it passes, it will
        pass through to the chain of interceptors. Otherwise, bypass interceptors and invoke class
        method directly."""

        className = invocation.instance.__class__.__name__

        if self.matches_method_and_target(invocation.method_name, className, invocation.args):
            # This constant is not class level, because it is a hack solution, and should only be used
            # used here, and not known outside the scope of this block of code. --G.Turnquist (9/22/2008)
            ASSUME_THIS_ADVISOR_WAS_FIRST = 1
            invocation.intercept_stack[ASSUME_THIS_ADVISOR_WAS_FIRST:ASSUME_THIS_ADVISOR_WAS_FIRST] = self.advice

            self.logger.debug("We have a match, passing through to the advice.")
            invocation.dump_interceptors(logging.DEBUG)

            return invocation.proceed()
        else:
            self.logger.debug("No match, bypassing advice, going straight to targetClass.")
            return getattr(invocation.instance, invocation.method_name)(*invocation.args, **invocation.kwargs)

    def __setattr__(self, name, value):
        """If "advice", make sure it is a list. Anything else, pass through to simple assignment.
        Also, if "patterns", initialize the regular expression parsers.
        """
        if name == "advice" and type(value) != list:
            self.__dict__[name] = [value]
        else:
            self.__dict__[name] = value

        if name == "patterns":
            self.init_patterns()

class FinalInterceptor(MethodInterceptor):
    """
    Final interceptor is always at the bottom of interceptor stack.
    It executes the actual target method on the instance.
    """
    def __init__(self):
        MethodInterceptor.__init__(self)
        self.logger = logging.getLogger("springpython.aop.FinalInterceptor")

    def invoke(self, invocation):
        return getattr(invocation.instance, invocation.method_name)(*invocation.args, **invocation.kwargs)

class AopProxy(object):
    """AopProxy acts like the target object by dispatching all method calls to the target through a MethodInvocation.
    The MethodInvocation object actually deals with potential "around" advice, referred to as interceptors. Attribute
    lookups are not intercepted, but instead fetched from the actual target object."""

    def __init__(self, target, interceptors):
        self.target = target
        if type(interceptors) == list:
            self.interceptors = interceptors
        else:
            self.interceptors = [interceptors]
        self.logger = logging.getLogger("springpython.aop.AopProxy")

    def __getattr__(self, name):
        """If any of the parameters are local objects, they are immediately retrieved. Callables cause the dispatch method
        to be return, which forwards callables through the interceptor stack. Target attributes are retrieved directly from
        the target object."""
        if name in ["target", "interceptors", "method_name"]:
            return self.__dict__[name]
        else:
            attr = getattr(self.target, name)
            if not callable(attr):
                return attr

            def dispatch(*args, **kwargs):
                """This method is returned to the caller emulating the function call being sent to the
                target object. This services as a proxying agent for the target object."""
                invocation = MethodInvocation(self.target, name, args, kwargs, self.interceptors)
                ##############################################################################
                # NOTE:
                # getattr(invocation, name) doesn't work here, because __str__ will print
                # the MethodInvocation's string, instead of trigger the interceptor stack.
                ##############################################################################
                return invocation.__getattr__(name)(*args, **kwargs)

            return dispatch

class ProxyFactory(object):
    """This object helps to build AopProxy objects programmatically. It allows configuring advice and target objects.
    Then it will produce an AopProxy when needed. To use similar behavior in an IoC environment, see ProxyFactoryObject."""

    def __init__(self, target = None, interceptors = None):
        self.logger = logging.getLogger("springpython.aop.ProxyFactory")
        self.target = target
        if not interceptors:
            self.interceptors = []
        elif type(interceptors) == list:
            self.interceptors = interceptors
        else:
            self.interceptors = [interceptors]

    def getProxy(self):
        """Generate an AopProxy given the current target and list of interceptors. Any changes to the factory after
        proxy creation do NOT propagate to the proxies."""
        return AopProxy(self.target, self.interceptors)

    def __setattr__(self, name, value):
        if name == "target" and type(value) == types.StringType:
            value = utils.getClass(value)()
        elif name == "interceptors" and not isinstance(value, list):
            value = [value]

        self.__dict__[name] = value

class ProxyFactoryObject(ProxyFactory, AopProxy):
    """This class acts as both a ProxyFactory to build and an AopProxy. It makes itself look like the target object.
    Any changes to the target and list of interceptors is immediately seen when using this as a proxy."""
    def __init__(self, target = None, interceptors = None):
        ProxyFactory.__init__(self, target, interceptors)
        self.logger = logging.getLogger("springpython.aop.ProxyFactoryObject")

    def __str__(self):
        return self.__getattr__("__str__")()

class PerformanceMonitorInterceptor(MethodInterceptor):
    def __init__(self, prefix = None, level = logging.DEBUG):
        self.prefix = prefix
        self.level = level
        self.logger = logging.getLogger("springpython.aop")

    def invoke(self, invocation):
        self.logger.log(self.level, "%s BEGIN" % (self.prefix))
        timing.start()
        results = invocation.proceed()
        timing.finish()
        self.logger.log(self.level, "%s END => %s" % (self.prefix, timing.milli()/1000.0))
        return results
