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
import unittest
from springpython.aop import MethodInterceptor
from springpython.aop import MethodMatcher
from springpython.aop import Pointcut
from springpython.aop import ProxyFactory
from springpython.aop import ProxyFactoryObject
from springpython.aop import RegexpMethodPointcutAdvisor
from springpython.config import XMLConfig
from springpython.context import ApplicationContext
from springpython.remoting.pyro import PyroDaemonHolder
from springpythontest.support.testSupportClasses import BeforeAndAfterInterceptor
from springpythontest.support.testSupportClasses import SampleService
from springpythontest.support.testSupportClasses import WrappingInterceptor

class AopInterfaceTestCase(unittest.TestCase):
    def testPointcutInterface(self):
        pointcut = Pointcut()
        self.assertRaises(NotImplementedError, pointcut.class_filter)
        self.assertRaises(NotImplementedError, pointcut.method_matcher)

    def testMethodMatcherInterface(self):
        methodMatcher = MethodMatcher()
        self.assertRaises(NotImplementedError, methodMatcher.matches_method_and_target, None, None, None)

    def testMethodInterceptorInterface(self):
        methodInterceptor = MethodInterceptor()
        self.assertRaises(NotImplementedError, methodInterceptor.invoke, None)

class AopProxyTestCase(unittest.TestCase):
    """Tests creating and using AOP proxies including unconditional interceptors."""
    def setUp(self):
        self.appContext = ApplicationContext(XMLConfig("support/aopApplicationContext.xml"))

    def testCreatingAProxyFactoryAndAddingAnInterceptorProgrammatically(self):
        factory = ProxyFactory()
        factory.target = SampleService()
        factory.interceptors.append(WrappingInterceptor())
        service = factory.getProxy()
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testCreatingAProxyFactoryAndAddingAnInterceptorIoC(self):
        factory = self.appContext.get_object("factory")
        service = factory.getProxy()
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testWrappingStringFunctionWithInterceptor(self):
        service = ProxyFactoryObject()
        service.target = SampleService()
        service.interceptors = [WrappingInterceptor()]
        self.assertEquals("This is a sample service.", service.target.__str__())
        self.assertEquals("This is a sample service.", str(service.target))
        self.assertEquals("<Wrapped>This is a sample service.</Wrapped>", str(service))
        self.assertEquals("<Wrapped>This is a sample service.</Wrapped>", service.__str__())

    def testCreatingAProxyFactoryObjectAndAddingAnInterceptorProgrammatically(self):
        service = ProxyFactoryObject()
        service.target = SampleService()
        service.interceptors = [WrappingInterceptor()]
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testCreatingAProxyFactoryObjectWithAnInterceptorIoC(self):
        service = self.appContext.get_object("sampleService4")
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testApplyingASingleConditionalPointcutIoC(self):
        sampleService = self.appContext.get_object("sampleService1")
        self.assertEquals(sampleService.doSomething(), "<Wrapped>Alright!</Wrapped>")
        self.assertEquals(sampleService.method("testdata"), "You made it! => testdata")

    def testApplyingTwoConditionalPointcutsIoC(self):
        sampleService = self.appContext.get_object("sampleService2")
        self.assertEquals(sampleService.doSomething(), "BEFORE => <Wrapped>Alright!</Wrapped> <= AFTER")
        self.assertEquals(sampleService.method("testdata"), "You made it! => testdata")

    def testApplyingASingleConditionalPointcutProgrammatically(self):
        wrappingAdvice = WrappingInterceptor()
        pointcutAdvisor = RegexpMethodPointcutAdvisor()
        pointcutAdvisor.advice = wrappingAdvice
        pointcutAdvisor.patterns = [".*do.*"]
        targetService = SampleService()
        sampleService = ProxyFactoryObject(interceptors = pointcutAdvisor)
        sampleService.target = targetService
        self.assertEquals(sampleService.doSomething(), "<Wrapped>Alright!</Wrapped>")
        self.assertEquals(sampleService.method("testdata"), "You made it! => testdata")

    def testApplyingTwoConditionalPointcutsProgrammatically(self):
        beginEndAdvice = BeforeAndAfterInterceptor()
        wrappingAdvice = WrappingInterceptor()
        pointcutAdvisor = RegexpMethodPointcutAdvisor()
        pointcutAdvisor.advice = [beginEndAdvice, wrappingAdvice]
        pointcutAdvisor.patterns = [".*do.*"]
        targetService = SampleService()
        sampleService = ProxyFactoryObject(interceptors = pointcutAdvisor)
        sampleService.target = targetService
        self.assertEquals(sampleService.doSomething(), "BEFORE => <Wrapped>Alright!</Wrapped> <= AFTER")
        self.assertEquals(sampleService.method("testdata"), "You made it! => testdata")

    def testCreatingAProxyFactoryObjectWithAnInterceptorByClassNameInsteadOfInstanceIoC(self):
        service = self.appContext.get_object("sampleService5")
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testProxyFactoryObjectInterceptorsNotWrappedInAList(self):
        service = ProxyFactoryObject()
        service.target = SampleService()

        # Note that it isn't wrapped in a list.
        service.interceptors = WrappingInterceptor()

        self.assertEquals("This is a sample service.", service.target.__str__())
        self.assertEquals("This is a sample service.", str(service.target))
        self.assertEquals("<Wrapped>This is a sample service.</Wrapped>", str(service))
        self.assertEquals("<Wrapped>This is a sample service.</Wrapped>", service.__str__())

        # sampleService6 has an interceptor which isn't wrapped in a list
        # inside its XMLConfig.
        service = self.appContext.get_object("sampleService6")
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

#class AopProxyFactoryCombinedWithPyroTestCase(unittest.TestCase):
#    """Tests mixing AOP proxies and Pyro with the point cut on either the client or the server side."""
#    def __init__(self, methodName='runTest'):
#        unittest.TestCase.__init__(self, methodName)
#        self.appContext = XmlApplicationContext("support/aopPyroApplicationContext.xml")
#
#    def __del__(self):
#        PyroDaemonHolder.shutdown()
#
#    def testWrappingPyroProxyOnClientSideIoC(self):
#        remoteService = self.appContext.get_object("remoteService1")
#        clientService = self.appContext.get_object("service1")
#        self.assertEquals("You got remote data => test1", remoteService.getData("test1"))
#        self.assertEquals("<Wrapped>You got remote data => test1</Wrapped>", clientService.getData("test1"))
#        self.appContext.dispose()
#
#    # TODO: There is some issue with running this and the previous test at the same time. It is some type of unforseeable
#    # dependency. Each test works fine when the other is commented out. Must resolve.
#
#    #def testWrappingPyroProxyOnServerSideIoC(self):
#    #    remoteService = self.appContext.get_object("remoteService2")
#    #    clientService = self.appContext.get_object("service2")
#    #    self.assertEquals("<Wrapped>You got remote data => test2</Wrapped>", remoteService.getData("test2"))
#    #    self.assertEquals("<Wrapped>You got remote data => test2</Wrapped>", clientService.getData("test2"))
#    #    self.appContext.dispose()

class AopProxiedArgumentsTest(unittest.TestCase):
    def testCallingProxiedMethodWithProxiedPositionalArguments(self):
        targetService = SampleService()

        service = ProxyFactoryObject(target = targetService, interceptors = WrappingInterceptor())

        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => Alright!</Wrapped>",
                          service.method(targetService.doSomething()))
        self.assertEquals("<Wrapped>You made it! => <Wrapped>Alright!</Wrapped></Wrapped>",
                          service.method(service.doSomething()))

    def testCallingProxiedMethodWithProxiedNamedArguments(self):
        targetService = SampleService()
        service = ProxyFactoryObject(target = targetService, interceptors = WrappingInterceptor())

        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method(data="test"))
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => Alright!</Wrapped>",
                          service.method(data=targetService.doSomething()))
        self.assertEquals("<Wrapped>You made it! => <Wrapped>Alright!</Wrapped></Wrapped>",
                          service.method(service.doSomething()))

    def testCallingRegExpProxiedMethodThatHasArgumentsWithProxiedPositionalArguments(self):
        pointcutAdvisor = RegexpMethodPointcutAdvisor(advice = WrappingInterceptor(),
                                                      patterns = ["SampleService.method"])
        service = ProxyFactoryObject(target = SampleService(), interceptors = pointcutAdvisor)

        self.assertEquals("Alright!", service.doSomething())
        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method("test"))
        self.assertEquals("<Wrapped>You made it! => Alright!</Wrapped>",
                          service.method(service.doSomething()))

    def testCallingRegExpProxiedMethodThatHasArgumentsWithProxiedNamedArguments(self):
        pointcutAdvisor = RegexpMethodPointcutAdvisor(advice = WrappingInterceptor(),
                                                      patterns = ["SampleService.method"])
        service = ProxyFactoryObject(target = SampleService(), interceptors = pointcutAdvisor)

        self.assertEquals("<Wrapped>You made it! => test</Wrapped>", service.method(data="test"))
        self.assertEquals("<Wrapped>You made it! => Alright!</Wrapped>",
                          service.method(data=service.doSomething()))

    def testCallingRegExpProxiedMethodThatHasNoArgumentsWithProxiedPositionalArguments(self):
        pointcutAdvisor = RegexpMethodPointcutAdvisor(advice = WrappingInterceptor(),
                                                      patterns = ["SampleService.doSomething"])
        service = ProxyFactoryObject(target = SampleService(), interceptors = pointcutAdvisor)

        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("You made it! => test", service.method("test"))
        self.assertEquals("You made it! => <Wrapped>Alright!</Wrapped>",
                          service.method(service.doSomething()))

    def testCallingRegExpProxiedMethodThatHasNoArgumentsWithProxiedNamedArguments(self):
        pointcutAdvisor = RegexpMethodPointcutAdvisor(advice = WrappingInterceptor(),
                                                      patterns = ["SampleService.doSomething"])
        service = ProxyFactoryObject(target = SampleService(), interceptors = pointcutAdvisor)

        self.assertEquals("You made it! => test", service.method(data="test"))
        self.assertEquals("You made it! => <Wrapped>Alright!</Wrapped>",
                          service.method(data=service.doSomething()))

if __name__ == "__main__":
    logger = logging.getLogger("springpython")
    loggingLevel = logging.INFO
    logger.setLevel(loggingLevel)
    ch = logging.StreamHandler()
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    unittest.main()
