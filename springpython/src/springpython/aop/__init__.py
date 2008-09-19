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
 
   NOTE: This module contains parts of PyContainer written by Rafal Sniezynski.
   They have been adapted to work outside the container.
"""
import logging
import re
import types
from springpython.context.pycontainer import utils

class Pointcut(object):
    """Interface defining where to apply an aspect."""
    def getClassFilter(self):
        raise NotImplementedError()
    def getMethodMatcher(self):
        raise NotImplementedError()

class MethodMatcher(object):
    """Interface defining how to apply aspects based on methods."""
    def matchesMethodAndTarget(self, method, targetClass, args):
        raise NotImplementedError()

class MethodInterceptor(object):
    """Interface defining "around" advice."""
    def invoke(self, invocation):
        raise NotImplementedError()

class MethodInvocation(object):
    """Encapsulation of invoking a method on a proxied service. It iterates throgh the list of interceptors by using
    a generator."""
    def __init__(self, instance, methodName, args, kwargs, interceptors):
        self.instance = instance
        self.methodName = methodName
        self.args = args
        self.kwargs = kwargs
        self.interceptorStack = interceptors
        self.interceptorStack.append(FinalInterceptor()) 
        self.logger = logging.getLogger("springpython.aop.MethodInvocation")

    def getInterceptor(self):
        """This is a generator to proceed through the stack of interceptors. By using generator convention, code may
        proceed in a nested fashion, versus a for-loop which would act in a chained fashion."""
        for interceptor in self.interceptorStack:
            yield interceptor

    def proceed(self):
        """This is the method every interceptor should call in order to continue down the chain of interceptors."""
        interceptor = self.iterator.next()
        self.logger.debug("Calling %s.%s(%s, %s)" % (interceptor.__class__.__name__, self.methodName, self.args, self.kwargs))
        return interceptor.invoke(self)

    def __getattr__(self, name):
        """This only deals with method invocations. Attributes are dealt with by the AopProxy, and don't every reach this
        block of code."""
        self.iterator = self.getInterceptor()
        self.methodName = name
        return self

    def __call__ (self, *args, **kwargs):
        """This method converts this from being a stored object into a callable class. This is effectively like a metaclass
        that dispatches calls to proceed through a stack of interceptors."""
        self.args = args
        self.kwargs = kwargs
        return self.proceed()

    def dumpInterceptors(self, level = logging.INFO):
        """DEBUG: Method used to dump the stack of interceptors in order of execution."""
        for interceptor in self.interceptorStack:
            self.logger.log(level, "Interceptor stack: %s" % interceptor.__class__.__name__)

class RegexpMethodPointcutAdvisor(Pointcut, MethodMatcher, MethodInterceptor):
    """
    This is a combination PointCut/MethodMatcher/MethodInterceptor. It allows associating one or more
    defined advices with a set of regular expression patterns.

    The following block shows how to configure one using IoC.

    <components>

	<component id="wrappingInterceptor" class="springpython.test.support.testSupportClasses.WrappingInterceptor"/>

	<component id="beginEndInterceptor" class="springpython.test.support.testSupportClasses.BeforeAndAfterInterceptor"/>

	<component id="pointcutTest" class="springpython.aop.RegexpMethodPointcutAdvisor">
		<property name="advice">
			<list local="beginEndInterceptor"/>
			<list local="wrappingInterceptor"/>
		</property>
		<property name="patterns">[".*do.*"]</property>
	</component>

	<component id="targetService" class="springpython.test.support.testSupportClasses.SampleService">
		<interceptor-ref name="pointcutTest"/>
	</component>
    
    <component id="sampleService" class="springpython.aop.ProxyFactoryComponent">
        <property name="target" local="targetService"/>
        <property name="advice">
            <list local="pointcutTest"/>
        </property>
    </component>
    
    </components>
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

    def initPatternRepresentation(self):
        """Precompile the regular expression pattern matcher list."""
        self.compiledPatterns = {}
        for pattern in self.patterns:
            self.compiledPatterns[pattern] = re.compile(pattern)

    def matchesMethodAndTarget(self, method, targetClass, args):
        """Iterate through all patterns, checking for a match. Calls the pattern matcher against "class.methodname"."""
        for pointcutPattern in self.patterns:
            if (self.matchesPattern(targetClass + "." + method, pointcutPattern)):
                return True
        return False

    def matchesPattern(self, methodName, pointcutPattern):
        """Uses a pre-built dictionary of regular expression patterns to check for a matcch."""
        if self.compiledPatterns[pointcutPattern].match(methodName):
            matched = True
        else:
            matched = False
        self.logger.debug("Candidate is [%s]; pattern is [%s]; matched=%s" % (methodName, pointcutPattern, matched))
        return matched

    def invoke(self, invocation):
        """Compares "class.method" against regular expression pattern and if it passes, it will
        pass through to the chain of interceptors. Otherwise, bypass interceptors and invoke class
        method directly."""

        className = invocation.instance.__class__.__name__

        if self.matchesMethodAndTarget(invocation.methodName, className, invocation.args):
            ASSUME_THIS_ADVISOR_WAS_FIRST = 1
            invocation.interceptorStack[ASSUME_THIS_ADVISOR_WAS_FIRST:ASSUME_THIS_ADVISOR_WAS_FIRST] = self.advice

            self.logger.debug("We have a match, passing through to the advice.")
            invocation.dumpInterceptors(logging.DEBUG)

            return invocation.proceed()
        else:
            self.logger.debug("No match, bypassing advice, going straight to targetClass.")
            return getattr(invocation.instance, invocation.methodName)(invocation.args)

    def __setattr__(self, name, value):
        """If "advice", make sure it is a list. Anything else, pass through to simple assignment.
        Also, if "patterns", initialize the regular expression parsers. 
        """
        if name == "advice" and type(value) != list:
            self.__dict__[name] = [value]
        else:
            self.__dict__[name] = value

        if name == "patterns":
            self.initPatternRepresentation()

class FinalInterceptor(MethodInterceptor):
    """
    Final interceptor is always at the bottom of interceptor stack.
    It executes the actual target method on the instance.
    """
    def __init__(self):
        MethodInterceptor.__init__(self)
        self.logger = logging.getLogger("springpython.aop.FinalInterceptor")

    def invoke(self, invocation):
        return getattr(invocation.instance, invocation.methodName)(*invocation.args, **invocation.kwargs)

class AopProxy(object):
    """AopProxy acts like the target component by dispatching all method calls to the target through a MethodInvocation.
    The MethodInvocation object actually deals with potential "around" advice, referred to as interceptors. Attribute
    lookups are not intercepted, but instead fetched from the actual target object."""
    
    def __init__(self, target, interceptors):
        if type(target).__name__ != "instance":
            raise Exception("Target attribute must be an instance.")
        self.target = target
        if type(interceptors) == list:
            self.interceptors = interceptors
        else:
            self.interceptors = [interceptors]
        self.logger = logging.getLogger("springpython.aop.AopProxy")

    def dispatch(self, *args, **kwargs):
        """This method is returned to the caller through __getattr__, to emulate all function calls being sent to the 
        target object. This allow this object to serve as a proxying agent for the target object."""
        self.logger.debug("Calling AopProxy.%s(%s)" % (self.methodName, args))
        invocation = MethodInvocation(self.target, self.methodName, args, kwargs, self.interceptors)
        return invocation.__getattr__(self.methodName)(*args, **kwargs)

    def __getattr__(self, name):
        """If any of the parameters are local objects, they are immediately retrieved. Callables cause the dispatch method
        to be return, which forwards callables through the interceptor stack. Target attributes are retrieved directly from
        the target object."""
        if name in ["target", "interceptors", "methodName"]:
            return self.__dict__[name]
        else:
            attr = getattr(self.target, name)
            if not callable(attr):
               return attr
            self.methodName = name
            return self.dispatch
        
class ProxyFactory(object):
    """This object helps to build AopProxy objects programmatically. It allows configuring advice and target objects.
    Then it will produce an AopProxy when needed. To use similar behavior in an IoC environment, see ProxyFactoryComponent."""
    
    def __init__(self, target = None, interceptors = None):
        self.logger = logging.getLogger("springpython.aop.ProxyFactory")
        self.target = target
        if not interceptors:
            self.interceptors = []
        elif type(interceptors) == list:
            self.interceptors = interceptors
        else:
            self.interceptors = [interceptors]

    def addInterceptor(self, interceptor):
        self.interceptors.append(interceptor)

    def getProxy(self):
        """Generate an AopProxy given the current target and list of interceptors. Any changes to the factory after
        proxy creation do NOT propogate to the proxies."""
        return AopProxy(self.target, self.interceptors)
    
    def __setattr__(self, name, value):
        if name == "target" and type(value) == types.StringType:
            self.__dict__[name] = utils.getClass(value)()
        else:
            self.__dict__[name] = value

class ProxyFactoryComponent(ProxyFactory, AopProxy):
    """This class acts as both a ProxyFactory to build and an AopProxy. It makes itself look like the target object.
    Any changes to the target and list of interceptors is immediately seen when using this as a proxy."""
    def __init__(self, target = None, interceptors = None):
        ProxyFactory.__init__(self, target, interceptors)
        self.logger = logging.getLogger("springpython.aop.ProxyFactoryComponent")
        
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
