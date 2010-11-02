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
from springpython.config import XMLConfig
from springpython.context import ApplicationContext
from springpythontest.support.testSupportClasses import RemoteService1
from springpythontest.support.testSupportClasses import RemoteService2
from springpython.remoting.pyro import PyroDaemonHolder
from springpython.remoting.pyro import PyroServiceExporter
from springpython.remoting.pyro import PyroProxyFactory
from springpython.remoting.pyro import Pyro4DaemonHolder
from springpython.remoting.pyro import Pyro4ServiceExporter
from springpython.remoting.pyro import Pyro4ProxyFactory
from springpython.remoting.hessian import HessianProxyFactory

class PyroRemotingTestCase(unittest.TestCase):
    def setUp(self):
        # This is the minimum time to wait before starting a new test,
        # allowing any previous Pyro daemon shutdowns to complete.
        time.sleep(3.0)
        
    def testExportingAServiceThroughIoC(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyroTestApplicationContext.xml"))
        
        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter1 = appContext.get_object("serviceExporter1")
        clientSideProxy1 = appContext.get_object("accountServiceClient1")
               
        remoteService2 = appContext.get_object("remoteServiceServer2")
        serviceExporter2 = appContext.get_object("serviceExporter2")
        clientSideProxy2 = appContext.get_object("accountServiceClient2")
                      
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

    def testExportingAServiceUsingNonStandardPortsWithValueElement(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyroTestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter3 = appContext.get_object("serviceExporter3")
        clientSideProxy3 = appContext.get_object("accountServiceClient3")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy3.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy3.getMoreData(argument), "You got more remote data => %s" % argument)

    def testExportingAServiceUsingNonStandardPortsWithValueAttribute(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyroTestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter4 = appContext.get_object("serviceExporter4")
        clientSideProxy4 = appContext.get_object("accountServiceClient4")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy4.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy4.getMoreData(argument), "You got more remote data => %s" % argument)

    def testExportingAServiceUsingNonStandardPortsWithConstructorArgsByAttribute(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyroTestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter5 = appContext.get_object("serviceExporter5")
        clientSideProxy5 = appContext.get_object("accountServiceClient5")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy5.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy5.getMoreData(argument), "You got more remote data => %s" % argument)


    def testExportingAServiceUsingNonStandardPortsWithConstructorArgsByElement(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyroTestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter6 = appContext.get_object("serviceExporter6")
        clientSideProxy6 = appContext.get_object("accountServiceClient6")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy6.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy6.getMoreData(argument), "You got more remote data => %s" % argument)

    def testExportingAServiceThroughIoCWithoutPullingTheIntermediateComponent(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyroTestApplicationContext.xml"))
        
        remoteService1 = appContext.get_object("remoteServiceServer1")
        clientSideProxy1 = appContext.get_object("accountServiceClient1")
               
        remoteService2 = appContext.get_object("remoteServiceServer2")
        clientSideProxy2 = appContext.get_object("accountServiceClient2")
        
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
        serviceExporter1.after_properties_set()
        clientSideProxy1 = PyroProxyFactory()
        clientSideProxy1.service_url = "PYROLOC://localhost:7766/RemoteService1"
               
        remoteService2 = RemoteService2()
        serviceExporter2 = PyroServiceExporter()
        serviceExporter2.service_name = "RemoteService2"
        serviceExporter2.service = remoteService2
        serviceExporter2.after_properties_set()
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

    def testExportingAServiceThroughProgrammaticallyWithNonStandardPorts(self):
        remoteService1 = RemoteService1()
        serviceExporter1 = PyroServiceExporter()
        serviceExporter1.service_name = "RemoteService1"
        serviceExporter1.service = remoteService1
        serviceExporter1.service_host = "127.0.0.1"
        serviceExporter1.service_port = 7000
        serviceExporter1.after_properties_set()
        clientSideProxy1 = PyroProxyFactory()
        clientSideProxy1.service_url = "PYROLOC://localhost:7000/RemoteService1"

        remoteService2 = RemoteService2()
        serviceExporter2 = PyroServiceExporter()
        serviceExporter2.service_name = "RemoteService2"
        serviceExporter2.service = remoteService2
        serviceExporter2.service_host = "127.0.0.1"
        serviceExporter2.service_port = 7000
        serviceExporter2.after_properties_set()
        clientSideProxy2 = PyroProxyFactory()
        clientSideProxy2.service_url = "PYROLOC://localhost:7000/RemoteService2"

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

    def testExportingAServiceThroughProgrammaticallyWithNonStandardPortsAndStrings(self):
        remoteService1 = RemoteService1()
        serviceExporter1 = PyroServiceExporter()
        serviceExporter1.service_name = "RemoteService1"
        serviceExporter1.service = remoteService1
        serviceExporter1.service_host = "127.0.0.1"
        serviceExporter1.service_port = 7000
        serviceExporter1.after_properties_set()
        clientSideProxy1 = PyroProxyFactory()
        clientSideProxy1.service_url = "PYROLOC://localhost:7000/RemoteService1"

        remoteService2 = RemoteService2()
        serviceExporter2 = PyroServiceExporter()
        serviceExporter2.service_name = "RemoteService2"
        serviceExporter2.service = remoteService2
        serviceExporter2.service_host = "127.0.0.1"
        serviceExporter2.service_port = 7000
        serviceExporter2.after_properties_set()
        clientSideProxy2 = PyroProxyFactory()
        clientSideProxy2.service_url = "PYROLOC://localhost:7000/RemoteService2"

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

class Pyro4RemotingTestCase(unittest.TestCase):
    def setUp(self):
        # This is the minimum time to wait before starting a new test,
        # allowing any previous Pyro daemon shutdowns to complete.
        time.sleep(3.0)
        
    def ttestExportingAServiceThroughIoC(self):
        import logging
        logger = logging.getLogger("springpython.test")

        logger.info("Creating appContext")
        appContext = ApplicationContext(XMLConfig("support/remotingPyro4TestApplicationContext.xml"))
        
        logger.info("Fetching server 1 stuff...")
        remoteService1 = appContext.get_object("remoteServiceServer1")
        logger.info("remoteService1 = %s" % remoteService1)
        serviceExporter1 = appContext.get_object("serviceExporter1")
        clientSideProxy1 = appContext.get_object("accountServiceClient1")
       
        remoteService2 = appContext.get_object("remoteServiceServer2")
        serviceExporter2 = appContext.get_object("serviceExporter2")
        clientSideProxy2 = appContext.get_object("accountServiceClient2")
              
        time.sleep(10.01)
        
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

	serviceExporter1.__del__()
        serviceExporter2 = None

    def ttestExportingAServiceUsingNonStandardPortsWithValueElement(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyro4TestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter3 = appContext.get_object("serviceExporter3")
        clientSideProxy3 = appContext.get_object("accountServiceClient3")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy3.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy3.getMoreData(argument), "You got more remote data => %s" % argument)

    def ttestExportingAServiceUsingNonStandardPortsWithValueAttribute(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyro4TestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter4 = appContext.get_object("serviceExporter4")
        clientSideProxy4 = appContext.get_object("accountServiceClient4")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy4.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy4.getMoreData(argument), "You got more remote data => %s" % argument)

    def ttestExportingAServiceUsingNonStandardPortsWithConstructorArgsByAttribute(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyro4TestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter5 = appContext.get_object("serviceExporter5")
        clientSideProxy5 = appContext.get_object("accountServiceClient5")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy5.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy5.getMoreData(argument), "You got more remote data => %s" % argument)


    def ttestExportingAServiceUsingNonStandardPortsWithConstructorArgsByElement(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyro4TestApplicationContext.xml"))

        time.sleep(0.01)

        remoteService1 = appContext.get_object("remoteServiceServer1")
        serviceExporter6 = appContext.get_object("serviceExporter6")
        clientSideProxy6 = appContext.get_object("accountServiceClient6")

        time.sleep(0.01)

        argument = ['a', 1, 'b']
        self.assertEquals(remoteService1.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(remoteService1.getMoreData(argument), "You got more remote data => %s" % argument)

        self.assertEquals(clientSideProxy6.getData(argument), "You got remote data => %s" % argument)
        self.assertEquals(clientSideProxy6.getMoreData(argument), "You got more remote data => %s" % argument)

    def ttestExportingAServiceThroughIoCWithoutPullingTheIntermediateComponent(self):
        appContext = ApplicationContext(XMLConfig("support/remotingPyro4TestApplicationContext.xml"))
        
        remoteService1 = appContext.get_object("remoteServiceServer1")
        clientSideProxy1 = appContext.get_object("accountServiceClient1")
               
        remoteService2 = appContext.get_object("remoteServiceServer2")
        clientSideProxy2 = appContext.get_object("accountServiceClient2")
        
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

        del(appContext)
                       
    def testExportingAServiceThroughProgrammatically(self):
        remoteService1 = RemoteService1()
        serviceExporter1 = Pyro4ServiceExporter()
        serviceExporter1.service_name = "RemoteService1"
        serviceExporter1.service = remoteService1
        serviceExporter1.after_properties_set()
        clientSideProxy1 = Pyro4ProxyFactory()
        clientSideProxy1.service_url = "PYRO:RemoteService1@localhost:7766"
               
        remoteService2 = RemoteService2()
        serviceExporter2 = Pyro4ServiceExporter()
        serviceExporter2.service_name = "RemoteService2"
        serviceExporter2.service = remoteService2
        serviceExporter2.after_properties_set()
        clientSideProxy2 = Pyro4ProxyFactory()
        clientSideProxy2.service_url = "PYRO:RemoteService2@localhost:7766"

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

    def testExportingAServiceThroughProgrammaticallyWithNonStandardPorts(self):
        remoteService1 = RemoteService1()
        serviceExporter1 = Pyro4ServiceExporter()
        serviceExporter1.service_name = "RemoteService1"
        serviceExporter1.service = remoteService1
        serviceExporter1.service_host = "127.0.0.1"
        serviceExporter1.service_port = 7000
        serviceExporter1.after_properties_set()
        clientSideProxy1 = Pyro4ProxyFactory()
        clientSideProxy1.service_url = "PYRO:RemoteService1@localhost:7000"

        remoteService2 = RemoteService2()
        serviceExporter2 = Pyro4ServiceExporter()
        serviceExporter2.service_name = "RemoteService2"
        serviceExporter2.service = remoteService2
        serviceExporter2.service_host = "127.0.0.1"
        serviceExporter2.service_port = 7000
        serviceExporter2.after_properties_set()
        clientSideProxy2 = Pyro4ProxyFactory()
        clientSideProxy2.service_url = "PYRO:RemoteService2@localhost:7000"

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

    def testExportingAServiceThroughProgrammaticallyWithNonStandardPortsAndStrings(self):
        remoteService1 = RemoteService1()
        serviceExporter1 = Pyro4ServiceExporter()
        serviceExporter1.service_name = "RemoteService1"
        serviceExporter1.service = remoteService1
        serviceExporter1.service_host = "127.0.0.1"
        serviceExporter1.service_port = 7000
        serviceExporter1.after_properties_set()
        clientSideProxy1 = Pyro4ProxyFactory()
        clientSideProxy1.service_url = "PYRO:RemoteService1@localhost:7000"

        remoteService2 = RemoteService2()
        serviceExporter2 = Pyro4ServiceExporter()
        serviceExporter2.service_name = "RemoteService2"
        serviceExporter2.service = remoteService2
        serviceExporter2.service_host = "127.0.0.1"
        serviceExporter2.service_port = 7000
        serviceExporter2.after_properties_set()
        clientSideProxy2 = Pyro4ProxyFactory()
        clientSideProxy2.service_url = "PYRO:RemoteService2@localhost:7000"

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

        appContext = ApplicationContext(XMLConfig("support/remotingHessianTestApplicationContext.xml"))
        clientSideProxy = appContext.get_object("personService")

        results = clientSideProxy.transform("Greg Turnquist a,b,c,x,y,z")

        self.assertEquals(results["firstName"], "Greg")
        self.assertEquals(results["lastName"], "Turnquist")
        self.assertEquals(results["attributes"], ["a", "b", "c", "x", "y", "z"])

        time.sleep(self.postdelay)
               
if __name__ == "__main__":
    unittest.main()
