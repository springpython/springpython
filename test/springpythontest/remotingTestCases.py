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
from springpythontest.support.testSupportClasses import RemoteService1
from springpythontest.support.testSupportClasses import RemoteService2
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
        
        remoteService1 = appContext.get_component("remoteServiceServer1")
        serviceExporter1 = appContext.get_component("serviceExporter1")
        clientSideProxy1 = appContext.get_component("accountServiceClient1")
               
        remoteService2 = appContext.get_component("remoteServiceServer2")
        serviceExporter2 = appContext.get_component("serviceExporter2")
        clientSideProxy2 = appContext.get_component("accountServiceClient2")
                      
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
        
        remoteService1 = appContext.get_component("remoteServiceServer1")
        clientSideProxy1 = appContext.get_component("accountServiceClient1")
               
        remoteService2 = appContext.get_component("remoteServiceServer2")
        clientSideProxy2 = appContext.get_component("accountServiceClient2")
        
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
        serviceExporter1.service_name = "RemoteService1"
        serviceExporter1.service = remoteService1
        clientSideProxy1 = PyroProxyFactory()
        clientSideProxy1.service_url = "PYROLOC://localhost:7766/RemoteService1"
               
        remoteService2 = RemoteService2()
        serviceExporter2 = PyroServiceExporter()
        serviceExporter2.service_name = "RemoteService2"
        serviceExporter2.service = remoteService2
        clientSideProxy2 = PyroProxyFactory()
        clientSideProxy2.service_url = "PYROLOC://localhost:7766/RemoteService2"
           
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
        os.popen("rm -f org/springframework/springpython/*.class")
        os.popen("javac -cp lib/jetty-6.1.11.jar:lib/jetty-util-6.1.11.jar:lib/servlet-api-2.5-6.1.11.jar:lib/hessian-3.1.6.jar org/springframework/springpython/*.java")
        self.predelay = 10.0
        self.postdelay = 10.0

    def run_jetty(self):
        os.popen("java  -cp lib/jetty-6.1.11.jar:lib/jetty-util-6.1.11.jar:lib/servlet-api-2.5-6.1.11.jar:lib/hessian-3.1.6.jar:. org.springframework.springpython.HessianJavaServer &")

        # This is the minimum time to wait before starting a new test,
        # allowing the jetty web server to start up.
        time.sleep(self.predelay)

    def testExportingAServiceThroughProgrammatically(self):
        self.run_jetty()

        clientSideProxy = HessianProxyFactory()
        clientSideProxy.service_url = "http://localhost:8080/"

        results = clientSideProxy.transform("Greg Turnquist a,b,c,x,y,z")

        self.assertEquals(results["firstName"], "Greg")
        self.assertEquals(results["lastName"], "Turnquist")
        self.assertEquals(results["attributes"], ["a", "b", "c", "x", "y", "z"])

        time.sleep(self.postdelay)
 
    def testExportingAServiceThroughIoC(self):
        self.run_jetty()

        appContext = XmlApplicationContext("support/remotingHessianTestApplicationContext.xml")
        clientSideProxy = appContext.get_component("personService")

        results = clientSideProxy.transform("Greg Turnquist a,b,c,x,y,z")

        self.assertEquals(results["firstName"], "Greg")
        self.assertEquals(results["lastName"], "Turnquist")
        self.assertEquals(results["attributes"], ["a", "b", "c", "x", "y", "z"])

        time.sleep(self.postdelay)
               
if __name__ == "__main__":
    unittest.main()
