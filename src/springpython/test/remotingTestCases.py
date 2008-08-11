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
import os
import unittest
import time
from springpython.context import XmlApplicationContext
from springpython.test.support.testSupportClasses import RemoteService1
from springpython.test.support.testSupportClasses import RemoteService2
from springpython.remoting.pyro import PyroDaemonHolder
from springpython.remoting.pyro import PyroServiceExporter
from springpython.remoting.pyro import PyroProxyFactory
from springpython.remoting.hessian import HessianProxyFactory

class PyroRemotingTestCase(unittest.TestCase):
    def setUp(self):
        # This is the minimum time to wait before starting a new test,
        # allowing any previous Pyro daemon shutdowns to complete.
        time.sleep(3.0)
        
    def testExportingAServiceThroughIoC(self):
        appContext = XmlApplicationContext("support/remotingPyroTestApplicationContext.xml")
        
        remoteService1 = appContext.getComponent("remoteServiceServer1")
        serviceExporter1 = appContext.getComponent("serviceExporter1")
        clientSideProxy1 = appContext.getComponent("accountServiceClient1")
               
        remoteService2 = appContext.getComponent("remoteServiceServer2")
        serviceExporter2 = appContext.getComponent("serviceExporter2")
        clientSideProxy2 = appContext.getComponent("accountServiceClient2")
                      
        time.sleep(0.01)
        
        argument1 = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument1), "You got remote data => %s" % argument1)
        self.assertEquals(remoteService1.getMoreData(argument1), "You got more remote data => %s" % argument1)
        
        self.assertEquals(clientSideProxy1.getData(argument1), "You got remote data => %s" % argument1)
        self.assertEquals(clientSideProxy1.getMoreData(argument1), "You got more remote data => %s" % argument1)

        routineToRun = "testit"
        self.assertEquals(remoteService2.executeOperation(routineToRun), "Operation %s has been carried out" % routineToRun)
        self.assertEquals(remoteService2.executeOtherOperation(routineToRun), "Other operation %s has been carried out" % routineToRun)

        self.assertEquals(clientSideProxy2.executeOperation(routineToRun), "Operation %s has been carried out" % routineToRun)
        self.assertEquals(clientSideProxy2.executeOtherOperation(routineToRun), "Other operation %s has been carried out" % routineToRun)
                       
    def testExportingAServiceThroughIoCWithoutPullingTheIntermediateComponent(self):
        appContext = XmlApplicationContext("support/remotingPyroTestApplicationContext.xml")
        
        remoteService1 = appContext.getComponent("remoteServiceServer1")
        clientSideProxy1 = appContext.getComponent("accountServiceClient1")
               
        remoteService2 = appContext.getComponent("remoteServiceServer2")
        clientSideProxy2 = appContext.getComponent("accountServiceClient2")
        
        time.sleep(0.01)
        
        argument1 = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument1), "You got remote data => %s" % argument1)
        self.assertEquals(remoteService1.getMoreData(argument1), "You got more remote data => %s" % argument1)
        
        self.assertEquals(clientSideProxy1.getData(argument1), "You got remote data => %s" % argument1)
        self.assertEquals(clientSideProxy1.getMoreData(argument1), "You got more remote data => %s" % argument1)

        routineToRun = "testit"
        self.assertEquals(remoteService2.executeOperation(routineToRun), "Operation %s has been carried out" % routineToRun)
        self.assertEquals(remoteService2.executeOtherOperation(routineToRun), "Other operation %s has been carried out" % routineToRun)

        self.assertEquals(clientSideProxy2.executeOperation(routineToRun), "Operation %s has been carried out" % routineToRun)
        self.assertEquals(clientSideProxy2.executeOtherOperation(routineToRun), "Other operation %s has been carried out" % routineToRun)
                       
    def testExportingAServiceThroughProgrammatically(self):
        remoteService1 = RemoteService1()
        serviceExporter1 = PyroServiceExporter()
        serviceExporter1.serviceName = "RemoteService1"
        serviceExporter1.service = remoteService1
        clientSideProxy1 = PyroProxyFactory()
        clientSideProxy1.serviceUrl = "PYROLOC://localhost:7766/RemoteService1"
               
        remoteService2 = RemoteService2()
        serviceExporter2 = PyroServiceExporter()
        serviceExporter2.serviceName = "RemoteService2"
        serviceExporter2.service = remoteService2
        clientSideProxy2 = PyroProxyFactory()
        clientSideProxy2.serviceUrl = "PYROLOC://localhost:7766/RemoteService2"
           
        time.sleep(0.01)
        
        argument1 = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument1), "You got remote data => %s" % argument1)
        self.assertEquals(remoteService1.getMoreData(argument1), "You got more remote data => %s" % argument1)
        
        self.assertEquals(clientSideProxy1.getData(argument1), "You got remote data => %s" % argument1)
        self.assertEquals(clientSideProxy1.getMoreData(argument1), "You got more remote data => %s" % argument1)

        routineToRun = "testit"
        self.assertEquals(remoteService2.executeOperation(routineToRun), "Operation %s has been carried out" % routineToRun)
        self.assertEquals(remoteService2.executeOtherOperation(routineToRun), "Other operation %s has been carried out" % routineToRun)

        self.assertEquals(clientSideProxy2.executeOperation(routineToRun), "Operation %s has been carried out" % routineToRun)
        self.assertEquals(clientSideProxy2.executeOtherOperation(routineToRun), "Other operation %s has been carried out" % routineToRun)

class HessianRemotingTestCase(unittest.TestCase):
    def __init__(self, tests):
        unittest.TestCase.__init__(self, tests)
        os.popen("cd .. ; rm -f net/sourceforge/springpython/*.class")
        os.popen("cd .. ; javac -cp lib/jetty-6.1.11.jar:lib/jetty-util-6.1.11.jar:lib/servlet-api-2.5-6.1.11.jar:lib/hessian-3.1.6.jar net/sourceforge/springpython/*.java")
        self.predelay = 5.0
        self.postdelay = 4.0

    def testExportingAServiceThroughProgrammatically(self):
        os.popen("cd .. ; java  -cp lib/jetty-6.1.11.jar:lib/jetty-util-6.1.11.jar:lib/servlet-api-2.5-6.1.11.jar:lib/hessian-3.1.6.jar:. net.sourceforge.springpython.HessianJavaServer &")

        # This is the minimum time to wait before starting a new test,
        # allowing the jetty web server to start up.
        time.sleep(self.predelay)

        clientSideProxy = HessianProxyFactory()
        clientSideProxy.serviceUrl = "http://localhost:8080/"

        results = clientSideProxy.transform("Greg Turnquist a,b,c,x,y,z")

        self.assertEquals(results["firstName"], "Greg")
        self.assertEquals(results["lastName"], "Turnquist")
        self.assertEquals(results["attributes"], ["a", "b", "c", "x", "y", "z"])

        time.sleep(self.postdelay)
 
    def testExportingAServiceThroughIoC(self):
        os.popen("cd .. ; java  -cp lib/jetty-6.1.11.jar:lib/jetty-util-6.1.11.jar:lib/servlet-api-2.5-6.1.11.jar:lib/hessian-3.1.6.jar:. net.sourceforge.springpython.HessianJavaServer &")

        # This is the minimum time to wait before starting a new test,
        # allowing the jetty web server to start up.
        time.sleep(self.predelay)

        appContext = XmlApplicationContext("support/remotingHessianTestApplicationContext.xml")
        clientSideProxy = appContext.getComponent("personService")

        results = clientSideProxy.transform("Greg Turnquist a,b,c,x,y,z")

        self.assertEquals(results["firstName"], "Greg")
        self.assertEquals(results["lastName"], "Turnquist")
        self.assertEquals(results["attributes"], ["a", "b", "c", "x", "y", "z"])

        time.sleep(self.postdelay)
               
if __name__ == "__main__":
    unittest.main()
