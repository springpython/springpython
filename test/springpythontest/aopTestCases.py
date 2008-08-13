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
import unittest
from springpython.aop import MethodInterceptor
from springpython.aop import MethodMatcher
from springpython.aop import Pointcut
from springpython.aop import ProxyFactory
from springpython.aop import ProxyFactoryComponent
from springpython.aop import RegexpMethodPointcutAdvisor
from springpython.context import XmlApplicationContext
from springpython.remoting.pyro import PyroDaemonHolder
from springpythontest.support.testSupportClasses import BeforeAndAfterInterceptor
from springpythontest.support.testSupportClasses import SampleService
from springpythontest.support.testSupportClasses import WrappingInterceptor

class AopInterfaceTestCase(unittest.TestCase):
    def testPointcutInterface(self):
        pointcut = Pointcut()
        self.assertRaises(NotImplementedError, pointcut.getClassFilter)
        self.assertRaises(NotImplementedError, pointcut.getMethodMatcher)
        
    def testMethodMatcherInterface(self):
        methodMatcher = MethodMatcher()
        self.assertRaises(NotImplementedError, methodMatcher.matchesMethodAndTarget, None, None, None)
        
    def testMethodInterceptorInterface(self):
        methodInterceptor = MethodInterceptor()
        self.assertRaises(NotImplementedError, methodInterceptor.invoke, None)

class AopProxyTestCase(unittest.TestCase):
    """Tests creating and using AOP proxies including unconditional interceptors."""
    def setUp(self):
        self.appContext = XmlApplicationContext("support/aopApplicationContext.xml")

    def testCreatingAProxyFactoryAndAddingAnInterceptorProgrammatically(self):
        factory = ProxyFactory()
        factory.target = SampleService()
        factory.addInterceptor(WrappingInterceptor())
        service = factory.getProxy()
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it!</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testCreatingAProxyFactoryAndAddingAnInterceptorIoC(self):
        factory = self.appContext.getComponent("factory")
        service = factory.getProxy()
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it!</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testCreatingAProxyFactoryComponentAndAddingAnInterceptorProgrammatically(self):
        service = ProxyFactoryComponent()
        service.target = SampleService()
        service.interceptors = [WrappingInterceptor()]
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it!</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testCreatingAProxyFactoryComponentWithAnInterceptorIoC(self):
        service = self.appContext.getComponent("sampleService4")
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it!</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

    def testApplyingASingleConditionalPointcutIoC(self):
        sampleService = self.appContext.getComponent("sampleService1")
        self.assertEquals(sampleService.doSomething(), "<Wrapped>Alright!</Wrapped>")
        self.assertEquals(sampleService.method("testdata"), "You made it!")

    def testApplyingTwoConditionalPointcutsIoC(self):
        sampleService = self.appContext.getComponent("sampleService2")
        self.assertEquals(sampleService.doSomething(), "BEFORE => <Wrapped>Alright!</Wrapped> <= AFTER")
        self.assertEquals(sampleService.method("testdata"), "You made it!")
        
    def testApplyingASingleConditionalPointcutProgrammatically(self):
        wrappingAdvice = WrappingInterceptor()
        pointcutAdvisor = RegexpMethodPointcutAdvisor()
        pointcutAdvisor.advice = wrappingAdvice
        pointcutAdvisor.patterns = [".*do.*"]
        targetService = SampleService()
        sampleService = ProxyFactoryComponent(interceptors = pointcutAdvisor)
        sampleService.target = targetService
        self.assertEquals(sampleService.doSomething(), "<Wrapped>Alright!</Wrapped>")
        self.assertEquals(sampleService.method("testdata"), "You made it!")

    def testApplyingTwoConditionalPointcutsProgrammatically(self):
        beginEndAdvice = BeforeAndAfterInterceptor()
        wrappingAdvice = WrappingInterceptor()
        pointcutAdvisor = RegexpMethodPointcutAdvisor()
        pointcutAdvisor.advice = [beginEndAdvice, wrappingAdvice]
        pointcutAdvisor.patterns = [".*do.*"]
        targetService = SampleService()
        sampleService = ProxyFactoryComponent(interceptors = pointcutAdvisor)
        sampleService.target = targetService
        self.assertEquals(sampleService.doSomething(), "BEFORE => <Wrapped>Alright!</Wrapped> <= AFTER")
        self.assertEquals(sampleService.method("testdata"), "You made it!")
        
    def testCreatingAProxyFactoryComponentWithAnInterceptorByClassNameInsteadOfInstanceIoC(self):
        service = self.appContext.getComponent("sampleService5")
        self.assertEquals("<Wrapped>Alright!</Wrapped>", service.doSomething())
        self.assertEquals("<Wrapped>You made it!</Wrapped>", service.method("test"))
        self.assertEquals("sample", service.attribute)

class AopProxyFactoryCombinedWithPyroTestCase(unittest.TestCase):
    """Tests mixing AOP proxies and Pyro with the point cut on either the client or the server side."""
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.appContext = XmlApplicationContext("support/aopPyroApplicationContext.xml")

    def __del__(self):
        PyroDaemonHolder.shutdown()

    def testWrappingPyroProxyOnClientSideIoC(self):
        remoteService = self.appContext.getComponent("remoteService1")
        clientService = self.appContext.getComponent("service1")
        self.assertEquals("You got remote data => test1", remoteService.getData("test1"))
        self.assertEquals("<Wrapped>You got remote data => test1</Wrapped>", clientService.getData("test1"))
        self.appContext.dispose()

    # TODO: There is some issue with running this and the previous test at the same time. It is some type of unforseeable
    # dependency. Each test works fine when the other is commented out. Must resolve.
    
    #def testWrappingPyroProxyOnServerSideIoC(self):
    #    remoteService = self.appContext.getComponent("remoteService2")
    #    clientService = self.appContext.getComponent("service2")
    #    self.assertEquals("<Wrapped>You got remote data => test2</Wrapped>", remoteService.getData("test2"))
    #    self.assertEquals("<Wrapped>You got remote data => test2</Wrapped>", clientService.getData("test2"))
    #    self.appContext.dispose()

if __name__ == "__main__":
    unittest.main()
