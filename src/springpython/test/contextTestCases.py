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
from springpython.context import ApplicationContext
from springpython.context import XmlApplicationContext
from springpython.context import ComponentNotFound
from springpython.test.support import testSupportClasses

class XmlApplicationContextTestCase(unittest.TestCase):        
    def testCreatingAnApplicationContext(self):
        movieAppContainer = XmlApplicationContext("support/contextTestPrimaryApplicationContext.xml")
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.getComponent("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        
    def testLoadingMultipleApplicationContexts(self):
        movieAppContainer = XmlApplicationContext(["support/contextTestPrimaryApplicationContext.xml", "support/contextTestSecondaryApplicationContext.xml"])
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.getComponent("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "Sta")

    def testCreatingXmlBasedIocContainerUsingDirectFunctionCalls(self):
        movieAppContainer = XmlApplicationContext("support/contextSingletonPrototypeCOmponentContext.xml")
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.getComponent("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = XmlApplicationContext("support/contextSingletonPrototypeCOmponentContext.xml")
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.getComponent("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.getComponent("MovieLister")

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

class ContextInterfacesTestCase(unittest.TestCase):
    def testInterfaces(self):
        applicationContext = ApplicationContext()
        self.assertRaises(NotImplementedError, applicationContext.getComponent, "foo")
    
class DecoratorBasedContextTestCase(unittest.TestCase):
    def testCreatingDecoratorBasedIocContainerUsingAppContextCalls(self):
        movieAppContainer = testSupportClasses.MovieBasedApplicationContext()
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.getComponent("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")
        
    def testCreatingDecoratorBasedIocContainerUsingDirectFunctionCalls(self):
        movieAppContainer = testSupportClasses.MovieBasedApplicationContext()
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.MovieLister()
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = testSupportClasses.MovieBasedApplicationContext()
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.MovieLister()
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.MovieLister()

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

    def testCreatingDuckTypeBasedIocContainerUsingAppContextCalls(self):
        movieAppContainer = testSupportClasses.DuckTypedMovieBasedApplicationContext()
        self.assertFalse(isinstance(movieAppContainer, ApplicationContext))
        self.assertFalse(hasattr(movieAppContainer, "getComponent"))

    def testCreatingDuckTypedBasedIocContainer(self):
        movieAppContainer = testSupportClasses.DuckTypedMovieBasedApplicationContext()
        self.assertFalse(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.MovieLister()
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = testSupportClasses.DuckTypedMovieBasedApplicationContext()
        self.assertFalse(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.MovieLister()
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.MovieLister()

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)
