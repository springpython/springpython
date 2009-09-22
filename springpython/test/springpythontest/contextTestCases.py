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

# pmock
from pmock import *

import sys
import atexit
import unittest
from springpython.context import DisposableObject
from springpython.context import ApplicationContext
from springpython.context import ObjectPostProcessor
from springpython.config import PythonConfig
from springpython.config import PyContainerConfig
from springpython.config import SpringJavaConfig
from springpython.config import Object
from springpython.config import XMLConfig
from springpython.config import YamlConfig
from springpython.security.userdetails import InMemoryUserDetailsService
from springpythontest.support import testSupportClasses

class PyContainerTestCase(unittest.TestCase):        
    def testCreatingAnApplicationContext(self):
        movieAppContainer = ApplicationContext(PyContainerConfig("support/contextTestPrimaryApplicationContext.xml"))
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        
    def testLoadingMultipleApplicationContexts(self):
        """When reading multiple sources, later object definitions can override earlier ones."""
        movieAppContainer = ApplicationContext(PyContainerConfig(["support/contextTestPrimaryApplicationContext.xml", "support/contextTestSecondaryApplicationContext.xml"]))
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "Sta")

    def testCreatingXmlBasedIocContainerUsingDirectFunctionCalls(self):
        movieAppContainer = ApplicationContext(PyContainerConfig("support/contextSingletonPrototypeObjectContext.xml"))
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = ApplicationContext(PyContainerConfig("support/contextSingletonPrototypeObjectContext.xml"))
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.get_object("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.get_object("MovieLister")

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

class PurePythonContainerTestCase(unittest.TestCase):
    def testCreatingDecoratorBasedIocContainerUsingAppContextCalls(self):
        movieAppContainer = ApplicationContext(testSupportClasses.MovieBasedApplicationContext())
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")
        
    def testCreatingMovieListerBeforeSingletonString(self):
        movieAppContainer = ApplicationContext(testSupportClasses.MovieBasedApplicationContext())
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        singleString = movieAppContainer.get_object("SingletonString")
        
        # Identity test
        self.assertEquals(lister.description, singleString)

    def testCreatingSingletonStringBeforeMovieLister(self):
        movieAppContainer = ApplicationContext(testSupportClasses.MovieBasedApplicationContext())
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        singleString = movieAppContainer.get_object("SingletonString")
        lister = movieAppContainer.get_object("MovieLister")

        # Identity test
#        self.assertEquals(lister.description, singleString)

    def testCreatingDecoratorBasedIocContainerUsingDirectFunctionCalls(self):
        movieAppContainer = ApplicationContext(testSupportClasses.MovieBasedApplicationContext())
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = ApplicationContext(testSupportClasses.MovieBasedApplicationContext())
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.get_object("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.get_object("MovieLister")

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)
        
class MixedConfigurationContainerTestCase(unittest.TestCase):
    def testXmlPullingPurePythonObject(self):
        movieAppContainer = ApplicationContext([testSupportClasses.MixedApplicationContext(),
                                                PyContainerConfig("support/contextMixedObjectContext.xml")])

        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = ApplicationContext([testSupportClasses.MixedApplicationContext(),
                                                PyContainerConfig("support/contextMixedObjectContext.xml")])
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.get_object("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.get_object("MovieLister")

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)

    def testPurePythonPullingXmlObject(self):
        movieAppContainer = ApplicationContext([testSupportClasses.MixedApplicationContext2(),
                                                PyContainerConfig("support/contextMixedObjectContext2.xml")])

        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = ApplicationContext([testSupportClasses.MixedApplicationContext2(),
                                                PyContainerConfig("support/contextMixedObjectContext2.xml")])
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.get_object("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.get_object("MovieLister")

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)

    def testNamedConstructorArguments(self):
        ctx = ApplicationContext(testSupportClasses.ConstructorBasedContainer())
        self.assertTrue(isinstance(ctx, ApplicationContext))

        m = ctx.get_object("MultiValueHolder")
        self.assertEquals("alt a", m.a)
        self.assertEquals("alt b", m.b)
        self.assertEquals("c", m.c)

        m2 = ctx.get_object("MultiValueHolder2")
        self.assertEquals("a", m2.a)
        self.assertEquals("alt b", m2.b)
        self.assertEquals("alt c", m2.c)

class SpringJavaConfigTestCase(unittest.TestCase):
    def testPullingJavaConfig(self):
        movieAppContainer = ApplicationContext(SpringJavaConfig("support/contextSpringJavaAppContext.xml"))

        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = ApplicationContext(SpringJavaConfig("support/contextSpringJavaAppContext.xml"))
        
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.get_object("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.get_object("MovieLister")

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)

    def testInnerObjects(self):
        movieAppContainer = ApplicationContext(SpringJavaConfig("support/contextSpringJavaAppContext.xml"))

        lister = movieAppContainer.get_object("MovieLister2")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")
        
        lister2 = movieAppContainer.get_object("MovieLister3")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")
        
        self.assertNotEqual(lister, lister2)

    def testPrefetchingObjects(self):
        movieAppContainer = ApplicationContext(SpringJavaConfig("support/contextSpringJavaAppContext.xml"))

        self.assertEqual(len(movieAppContainer.object_defs), 10)
        self.assertTrue("MovieLister" in movieAppContainer.object_defs)
        self.assertTrue("MovieFinder" in movieAppContainer.object_defs)
        self.assertTrue("SingletonString" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister2" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister3" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister2.finder.<anonymous>" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister3.finder.named" in movieAppContainer.object_defs)
        self.assertTrue("ValueHolder" in movieAppContainer.object_defs)
        self.assertTrue("AnotherSingletonString" in movieAppContainer.object_defs)
        self.assertTrue("AThirdSingletonString" in movieAppContainer.object_defs)

    def testCollections(self):
        ctx = ApplicationContext(SpringJavaConfig("support/contextSpringJavaAppContext.xml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))
        value_holder = ctx.get_object("ValueHolder")
        
        self.assertTrue(isinstance(value_holder.some_dict, dict))
        self.assertEquals(4, len(value_holder.some_dict))
        
        self.assertEquals("Python", value_holder.some_dict["Spring"])
        self.assertEquals("World", value_holder.some_dict["Hello"])
        self.assertTrue(isinstance(value_holder.some_dict["holder"], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_dict["holder"].str)
        self.assertEquals("There should only be one copy of this string", value_holder.some_dict["another copy"].str)
        
        # Verify they are both referencing the same StringHolder class
        self.assertEquals(value_holder.some_dict["holder"], value_holder.some_dict["another copy"])
        
        self.assertTrue(isinstance(value_holder.some_list, list))
        self.assertEquals(3, len(value_holder.some_list))
        self.assertEquals("Hello, world!", value_holder.some_list[0])
        self.assertTrue(isinstance(value_holder.some_list[1], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_list[1].str)
        self.assertEquals("Spring Python", value_holder.some_list[2])

        # Verify this is also using the same singleton object
        self.assertEquals(value_holder.some_dict["holder"], value_holder.some_list[1])

        self.assertTrue(isinstance(value_holder.some_props, dict))
        self.assertEquals(3, len(value_holder.some_props))
        self.assertEquals("administrator@example.org", value_holder.some_props["administrator"])
        self.assertEquals("support@example.org", value_holder.some_props["support"])
        self.assertEquals("development@example.org", value_holder.some_props["development"])
        
        self.assertTrue(isinstance(value_holder.some_set, set))
        self.assertEquals(3, len(value_holder.some_set))
        self.assertTrue("Hello, world!" in value_holder.some_set)
        self.assertTrue("Spring Python" in value_holder.some_set)
        
        foundStringHolder = False
        for item in value_holder.some_set:
            if isinstance(item, testSupportClasses.StringHolder):
                self.assertEquals("There should only be one copy of this string", item.str)
                self.assertEquals(item, value_holder.some_list[1])
                foundStringHolder = True
        self.assertTrue(foundStringHolder)

    def testConstructors(self):
        ctx = ApplicationContext(SpringJavaConfig("support/contextSpringJavaAppContext.xml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))
        
        another_str = ctx.get_object("AnotherSingletonString")
        a_third_str = ctx.get_object("AThirdSingletonString")
        
        self.assertEquals("attributed value", another_str.str)
        self.assertEquals("elemental value", a_third_str.str)
        
        value_holder = ctx.get_object("ValueHolder")
        self.assertTrue(isinstance(value_holder.string_holder, testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.string_holder.str)
        
        single_str = ctx.get_object("SingletonString")
        
        self.assertEquals(single_str.str, value_holder.string_holder.str)
        self.assertEquals(single_str, value_holder.string_holder)

class XMLConfigTestCase(unittest.TestCase):
    def testPullingXMLConfig(self):
        movieAppContainer = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))

        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))
        
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.get_object("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.get_object("MovieLister")

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)

    def testInnerObjects(self):
        movieAppContainer = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))

        lister = movieAppContainer.get_object("MovieLister2")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")
        
        lister2 = movieAppContainer.get_object("MovieLister3")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")
        
        self.assertNotEqual(lister, lister2)

    def testPrefetchingObjects(self):
        movieAppContainer = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))

        self.assertEqual(len(movieAppContainer.object_defs), 12)
        self.assertTrue("MovieLister" in movieAppContainer.object_defs)
        self.assertTrue("MovieFinder" in movieAppContainer.object_defs)
        self.assertTrue("SingletonString" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister2" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister3" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister2.finder.<anonymous>" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister3.finder.named" in movieAppContainer.object_defs)
        self.assertTrue("ValueHolder" in movieAppContainer.object_defs)
        self.assertTrue("AnotherSingletonString" in movieAppContainer.object_defs)
        self.assertTrue("AThirdSingletonString" in movieAppContainer.object_defs)
        self.assertTrue("MultiValueHolder" in movieAppContainer.object_defs)
        self.assertTrue("MultiValueHolder2" in movieAppContainer.object_defs)

    def testCollections(self):
        ctx = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))
        value_holder = ctx.get_object("ValueHolder")
        
        self.assertTrue(isinstance(value_holder.some_dict, dict))
        self.assertEquals(4, len(value_holder.some_dict))
        
        self.assertEquals("Python", value_holder.some_dict["Spring"])
        self.assertEquals("World", value_holder.some_dict["Hello"])
        self.assertTrue(isinstance(value_holder.some_dict["holder"], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_dict["holder"].str)
        self.assertEquals("There should only be one copy of this string", value_holder.some_dict["another copy"].str)
        
        # Verify they are both referencing the same StringHolder class
        self.assertEquals(value_holder.some_dict["holder"], value_holder.some_dict["another copy"])
        
        self.assertTrue(isinstance(value_holder.some_list, list))
        self.assertEquals(3, len(value_holder.some_list))
        self.assertEquals("Hello, world!", value_holder.some_list[0])
        self.assertTrue(isinstance(value_holder.some_list[1], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_list[1].str)
        self.assertEquals("Spring Python", value_holder.some_list[2])

        # Verify this is also using the same singleton object
        self.assertEquals(value_holder.some_dict["holder"], value_holder.some_list[1])

        self.assertTrue(isinstance(value_holder.some_props, dict))
        self.assertEquals(3, len(value_holder.some_props))
        self.assertEquals("administrator@example.org", value_holder.some_props["administrator"])
        self.assertEquals("support@example.org", value_holder.some_props["support"])
        self.assertEquals("development@example.org", value_holder.some_props["development"])
        
        self.assertTrue(isinstance(value_holder.some_set, set))
        self.assertEquals(3, len(value_holder.some_set))
        self.assertTrue("Hello, world!" in value_holder.some_set)
        self.assertTrue("Spring Python" in value_holder.some_set)

        self.assertTrue(isinstance(value_holder.some_frozen_set, frozenset))
        self.assertEquals(3, len(value_holder.some_frozen_set))
        self.assertTrue("Hello, world!" in value_holder.some_frozen_set)
        self.assertTrue("Spring Python" in value_holder.some_frozen_set)
        
        self.assertTrue(isinstance(value_holder.some_tuple, tuple))
        self.assertEquals(3, len(value_holder.some_tuple))
        self.assertEquals("Hello, world!", value_holder.some_tuple[0])
        self.assertTrue(isinstance(value_holder.some_tuple[1], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_tuple[1].str)
        self.assertEquals("Spring Python", value_holder.some_tuple[2])
        
        foundStringHolder = False
        for item in value_holder.some_set:
            if isinstance(item, testSupportClasses.StringHolder):
                self.assertEquals("There should only be one copy of this string", item.str)
                self.assertEquals(item, value_holder.some_list[1])
                foundStringHolder = True
        self.assertTrue(foundStringHolder)

    def testConstructors(self):
        ctx = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))
        
        another_str = ctx.get_object("AnotherSingletonString")
        a_third_str = ctx.get_object("AThirdSingletonString")
        
        self.assertEquals("attributed value", another_str.str)
        self.assertEquals("elemental value", a_third_str.str)
        
        value_holder = ctx.get_object("ValueHolder")
        self.assertTrue(isinstance(value_holder.string_holder, testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.string_holder.str)
        
        single_str = ctx.get_object("SingletonString")
        
        self.assertEquals(single_str.str, value_holder.string_holder.str)
        self.assertEquals(single_str, value_holder.string_holder)

    def testNamedConstructorArguments(self):
        ctx = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))

        m = ctx.get_object("MultiValueHolder")
        self.assertEquals("alt a", m.a)
        self.assertEquals("alt b", m.b)
        self.assertEquals("c", m.c)

        m2 = ctx.get_object("MultiValueHolder2")
        self.assertEquals("a", m2.a)
        self.assertEquals("alt b", m2.b)
        self.assertEquals("alt c", m2.c)

    def testGetComplexValueObject(self):
        ctx1 = ApplicationContext(PyContainerConfig("support/contextComplexPyContainer.xml"))
        ctx2 = ApplicationContext(XMLConfig("support/contextComplexXMLConfig.xml"))
        
        # This is what PyContainerConfig could handle
        for ctx in [ctx1, ctx2]:
            service = ctx.get_object("user_details_service")
            self.assertEquals(8, len(service.user_dict))
            self.assertEquals(3, len(service.user_dict["basichiorangeuser"]))
            self.assertEquals("ASSIGNED_ORANGE", service.user_dict["basichiorangeuser"][1][1])
    
            service = ctx.get_object("user_details_service")
            self.assertTrue(isinstance(service.user_dict, dict))
            self.assertEquals(8, len(service.user_dict))
            self.assertEquals(3, len(service.user_dict["basichiorangeuser"]))
            self.assertEquals("ASSIGNED_ORANGE", service.user_dict["basichiorangeuser"][1][1])
        
        # These are the other things that XMLConfig can handle
        service2 = ctx2.get_object("user_details_service2")
        self.assertTrue(isinstance(service2.user_dict, list))
        self.assertEquals(5, len(service2.user_dict))
        
        self.assertEquals("Hello, world!", service2.user_dict[0])
        
        self.assertTrue(isinstance(service2.user_dict[1], dict))
        self.assertEquals("This is working", service2.user_dict[1]["yes"])
        self.assertEquals("Maybe it's not?", service2.user_dict[1]["no"])

        self.assertTrue(isinstance(service2.user_dict[2], tuple))
        self.assertEquals(4, len(service2.user_dict[2]))
        self.assertEquals("Hello, from Spring Python!", service2.user_dict[2][0])

        self.assertTrue(isinstance(service2.user_dict[2][2], dict))
        self.assertEquals(2, len(service2.user_dict[2][2]))
        self.assertEquals("This is working", service2.user_dict[2][2]["yes"])
        self.assertEquals("Maybe it's not?", service2.user_dict[2][2]["no"])

        self.assertTrue(isinstance(service2.user_dict[2][3], list))
        self.assertEquals(2, len(service2.user_dict[2][3]))
        self.assertEquals("This is a list element inside a tuple.", service2.user_dict[2][3][0])
        self.assertEquals("And so is this :)", service2.user_dict[2][3][1])

        self.assertTrue(isinstance(service2.user_dict[3], set))
        self.assertEquals(2, len(service2.user_dict[3]))
        self.assertTrue("1" in service2.user_dict[3])
        self.assertTrue("2" in service2.user_dict[3])
        self.assertTrue("3" not in service2.user_dict[3])
        
        self.assertTrue(isinstance(service2.user_dict[4], frozenset))
        self.assertEquals(2, len(service2.user_dict[4]))
        self.assertTrue("a" in service2.user_dict[4])
        self.assertTrue("b" in service2.user_dict[4])
        self.assertTrue("c" not in service2.user_dict[4])

class YamlConfigTestCase(unittest.TestCase):
    def testPullingYamlConfig(self):
        movieAppContainer = ApplicationContext(YamlConfig("support/contextSpringPythonAppContext.yaml"))
        self.assertTrue(isinstance(movieAppContainer, ApplicationContext))
        lister = movieAppContainer.get_object("MovieLister")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")

        # Create a separate container, which has its own instances of singletons
        movieAppContainer2 = ApplicationContext(YamlConfig("support/contextSpringPythonAppContext.yaml"))
        
        self.assertTrue(isinstance(movieAppContainer2, ApplicationContext))
        lister2 = movieAppContainer2.get_object("MovieLister")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")

        # Create another MovieLister based on the first app context
        lister3 = movieAppContainer.get_object("MovieLister")

        # Identity test. Verify objects were created in separate app contexts, and that
        # singletons exist only once, while prototypes are different on a per instance
        # basis.
        
        # The MovieLister's are prototypes, and different within and between containers.
        self.assertNotEquals(lister, lister2)
        self.assertNotEquals(lister, lister3)
        self.assertNotEquals(lister2, lister3)

        # While the strings hold the same value...
        self.assertEquals(lister.description.str, lister2.description.str)
        self.assertEquals(lister2.description.str, lister3.description.str)
        
        # ...they are not necessarily the same object
        self.assertEquals(lister.description, lister3.description)
        self.assertNotEquals(lister.description, lister2.description)
        
        # The finder is also a singleton, only varying between containers
        self.assertNotEquals(lister.finder, lister2.finder)
        self.assertEquals(lister.finder, lister3.finder)

    def testInnerObjects(self):
        movieAppContainer = ApplicationContext(YamlConfig("support/contextSpringPythonAppContext.yaml"))

        lister = movieAppContainer.get_object("MovieLister2")
        movieList = lister.finder.findAll()
        self.assertEquals(movieList[0], "The Count of Monte Cristo")
        self.assertEquals(lister.description.str, "There should only be one copy of this string")
        
        lister2 = movieAppContainer.get_object("MovieLister3")
        movieList2 = lister2.finder.findAll()
        self.assertEquals(movieList2[0], "The Count of Monte Cristo")
        self.assertEquals(lister2.description.str, "There should only be one copy of this string")
        
        self.assertNotEqual(lister, lister2)

    def testPrefetchingObjects(self):
        movieAppContainer = ApplicationContext(YamlConfig("support/contextSpringPythonAppContext.yaml"))

        self.assertEqual(len(movieAppContainer.object_defs), 12)
        self.assertTrue("MovieLister" in movieAppContainer.object_defs)
        self.assertTrue("MovieFinder" in movieAppContainer.object_defs)
        self.assertTrue("SingletonString" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister2" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister3" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister2.finder.<anonymous>" in movieAppContainer.object_defs)
        self.assertTrue("MovieLister3.finder.named" in movieAppContainer.object_defs)
        self.assertTrue("ValueHolder" in movieAppContainer.object_defs)
        self.assertTrue("AnotherSingletonString" in movieAppContainer.object_defs)
        self.assertTrue("AThirdSingletonString" in movieAppContainer.object_defs)
        self.assertTrue("MultiValueHolder" in movieAppContainer.object_defs)
        self.assertTrue("MultiValueHolder2" in movieAppContainer.object_defs)

    def testCollections(self):
        ctx = ApplicationContext(YamlConfig("support/contextSpringPythonAppContext.yaml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))
        value_holder = ctx.get_object("ValueHolder")
        
        self.assertTrue(isinstance(value_holder.some_dict, dict))
        self.assertEquals(4, len(value_holder.some_dict))
        
        self.assertEquals("Python", value_holder.some_dict["Spring"])
        self.assertEquals("World", value_holder.some_dict["Hello"])
        self.assertTrue(isinstance(value_holder.some_dict["holder"], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_dict["holder"].str)
        self.assertEquals("There should only be one copy of this string", value_holder.some_dict["another copy"].str)
        
        # Verify they are both referencing the same StringHolder class
        self.assertEquals(value_holder.some_dict["holder"], value_holder.some_dict["another copy"])
        
        self.assertTrue(isinstance(value_holder.some_list, list))
        self.assertEquals(3, len(value_holder.some_list))
        self.assertEquals("Hello, world!", value_holder.some_list[0])
        self.assertTrue(isinstance(value_holder.some_list[1], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_list[1].str)
        self.assertEquals("Spring Python", value_holder.some_list[2])

        # Verify this is also using the same singleton object
        self.assertEquals(value_holder.some_dict["holder"], value_holder.some_list[1])

        self.assertTrue(isinstance(value_holder.some_props, dict))
        self.assertEquals(3, len(value_holder.some_props))
        self.assertEquals("administrator@example.org", value_holder.some_props["administrator"])
        self.assertEquals("support@example.org", value_holder.some_props["support"])
        self.assertEquals("development@example.org", value_holder.some_props["development"])
        
        self.assertTrue(isinstance(value_holder.some_set, set))
        self.assertEquals(3, len(value_holder.some_set))
        self.assertTrue("Hello, world!" in value_holder.some_set)
        self.assertTrue("Spring Python" in value_holder.some_set)

        self.assertTrue(isinstance(value_holder.some_frozen_set, frozenset))
        self.assertEquals(3, len(value_holder.some_frozen_set))
        self.assertTrue("Hello, world!" in value_holder.some_frozen_set)
        self.assertTrue("Spring Python" in value_holder.some_frozen_set)
        
        self.assertTrue(isinstance(value_holder.some_tuple, tuple))
        self.assertEquals(3, len(value_holder.some_tuple))
        self.assertEquals("Hello, world!", value_holder.some_tuple[0])
        self.assertTrue(isinstance(value_holder.some_tuple[1], testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.some_tuple[1].str)
        self.assertEquals("Spring Python", value_holder.some_tuple[2])
        
        foundStringHolder = False
        for item in value_holder.some_set:
            if isinstance(item, testSupportClasses.StringHolder):
                self.assertEquals("There should only be one copy of this string", item.str)
                self.assertEquals(item, value_holder.some_list[1])
                foundStringHolder = True
        self.assertTrue(foundStringHolder)

    def testConstructors(self):
        ctx = ApplicationContext(YamlConfig("support/contextSpringPythonAppContext.yaml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))
        
        another_str = ctx.get_object("AnotherSingletonString")
        a_third_str = ctx.get_object("AThirdSingletonString")
        
        self.assertEquals("attributed value", another_str.str)
        self.assertEquals("elemental value", a_third_str.str)
        
        value_holder = ctx.get_object("ValueHolder")
        self.assertTrue(isinstance(value_holder.string_holder, testSupportClasses.StringHolder))
        self.assertEquals("There should only be one copy of this string", value_holder.string_holder.str)
        
        single_str = ctx.get_object("SingletonString")
        
        self.assertEquals(single_str.str, value_holder.string_holder.str)
        self.assertEquals(single_str, value_holder.string_holder)

    def testNamedConstructorArguments(self):
        ctx = ApplicationContext(YamlConfig("support/contextSpringPythonAppContext.yaml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))

        m = ctx.get_object("MultiValueHolder")
        self.assertEquals("alt a", m.a)
        self.assertEquals("alt b", m.b)
        self.assertEquals("c", m.c)

        m2 = ctx.get_object("MultiValueHolder2")
        self.assertEquals("a", m2.a)
        self.assertEquals("alt b", m2.b)
        self.assertEquals("alt c", m2.c)

class YamlConfigTestCase2(unittest.TestCase):
    def testAnotherComplexContainer(self):
        ctx = ApplicationContext(YamlConfig("support/contextComplexYamlConfig2.yaml"))
        service3 = ctx.get_object("user_details_service3")
        self.assertTrue(isinstance(service3.user_dict, list))
        self.assertEquals(7, len(service3.user_dict))

        self.assertTrue(isinstance(service3.user_dict[0], list))
        self.assertEquals(2, len(service3.user_dict[0]))

        self.assertTrue(isinstance(service3.user_dict[0][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service3.user_dict[0][0].user_dict)
        self.assertEquals("Test2", service3.user_dict[0][1].user_dict)

        self.assertTrue(isinstance(service3.user_dict[1], tuple))
        self.assertEquals(2, len(service3.user_dict[1]))

        self.assertTrue(isinstance(service3.user_dict[1][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service3.user_dict[1][0].user_dict)
        self.assertEquals("Test2", service3.user_dict[1][1].user_dict)

        self.assertTrue(isinstance(service3.user_dict[2], InMemoryUserDetailsService))
        self.assertEquals("Test3", service3.user_dict[2].user_dict)

        self.assertTrue(isinstance(service3.user_dict[3], set))
        self.assertEquals(2, len(service3.user_dict[3]))
        self.assertTrue("Test4" in [item.user_dict for item in service3.user_dict[3]])
        self.assertTrue("Test5" in [item.user_dict for item in service3.user_dict[3]])

        self.assertTrue(isinstance(service3.user_dict[4], frozenset))
        self.assertEquals(2, len(service3.user_dict[4]))
        self.assertTrue("Test6" in [item.user_dict for item in service3.user_dict[4]])
        self.assertTrue("Test7" in [item.user_dict for item in service3.user_dict[4]])

        self.assertTrue(isinstance(service3.user_dict[5], set))
        self.assertEquals(1, len(service3.user_dict[5]))
        self.assertTrue("Test8" in [item.user_dict for item in service3.user_dict[5]])

        self.assertTrue(isinstance(service3.user_dict[6], frozenset))
        self.assertEquals(1, len(service3.user_dict[6]))
        self.assertTrue("Test9" in [item.user_dict for item in service3.user_dict[6]])

    def testNamedConstructorArguments(self):
        ctx = ApplicationContext(XMLConfig("support/contextSpringPythonAppContext.xml"))
        self.assertTrue(isinstance(ctx, ApplicationContext))

        m = ctx.get_object("MultiValueHolder")
        self.assertEquals("alt a", m.a)
        self.assertEquals("alt b", m.b)
        self.assertEquals("c", m.c)

        m2 = ctx.get_object("MultiValueHolder2")
        self.assertEquals("a", m2.a)
        self.assertEquals("alt b", m2.b)
        self.assertEquals("alt c", m2.c)

class XMLConfigTestCase3(unittest.TestCase):
    def testAThirdComplexContainer(self):
        ctx = ApplicationContext(XMLConfig("support/contextComplexXMLConfig3.xml"))
        service4 = ctx.get_object("user_details_service4")
        self.assertTrue(isinstance(service4.user_dict, tuple))
        self.assertEquals(7, len(service4.user_dict))

        self.assertTrue(isinstance(service4.user_dict[0], list))
        self.assertEquals(2, len(service4.user_dict[0]))

        self.assertTrue(isinstance(service4.user_dict[0][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service4.user_dict[0][0].user_dict)
        self.assertEquals("Test2", service4.user_dict[0][1].user_dict)

        self.assertTrue(isinstance(service4.user_dict[1], tuple))
        self.assertEquals(2, len(service4.user_dict[1]))

        self.assertTrue(isinstance(service4.user_dict[1][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service4.user_dict[1][0].user_dict)
        self.assertEquals("Test2", service4.user_dict[1][1].user_dict)

        self.assertTrue(isinstance(service4.user_dict[2], InMemoryUserDetailsService))
        self.assertEquals("Test3", service4.user_dict[2].user_dict)

        self.assertTrue(isinstance(service4.user_dict[3], set))
        self.assertEquals(2, len(service4.user_dict[3]))
        self.assertTrue("Test4" in [item.user_dict for item in service4.user_dict[3]])
        self.assertTrue("Test5" in [item.user_dict for item in service4.user_dict[3]])

        self.assertTrue(isinstance(service4.user_dict[4], frozenset))
        self.assertEquals(2, len(service4.user_dict[4]))
        self.assertTrue("Test6" in [item.user_dict for item in service4.user_dict[4]])
        self.assertTrue("Test7" in [item.user_dict for item in service4.user_dict[4]])

        self.assertTrue(isinstance(service4.user_dict[5], set))
        self.assertEquals(1, len(service4.user_dict[5]))
        self.assertTrue("Test8" in [item.user_dict for item in service4.user_dict[5]])

        self.assertTrue(isinstance(service4.user_dict[6], frozenset))
        self.assertEquals(1, len(service4.user_dict[6]))
        self.assertTrue("Test9" in [item.user_dict for item in service4.user_dict[6]])

class YamlConfigTestCase3(unittest.TestCase):
    def testAThirdComplexContainer(self):
        ctx = ApplicationContext(YamlConfig("support/contextComplexYamlConfig3.yaml"))
        service4 = ctx.get_object("user_details_service4")
        self.assertTrue(isinstance(service4.user_dict, tuple))
        self.assertEquals(7, len(service4.user_dict))

        self.assertTrue(isinstance(service4.user_dict[0], list))
        self.assertEquals(2, len(service4.user_dict[0]))

        self.assertTrue(isinstance(service4.user_dict[0][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service4.user_dict[0][0].user_dict)
        self.assertEquals("Test2", service4.user_dict[0][1].user_dict)

        self.assertTrue(isinstance(service4.user_dict[1], tuple))
        self.assertEquals(2, len(service4.user_dict[1]))

        self.assertTrue(isinstance(service4.user_dict[1][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service4.user_dict[1][0].user_dict)
        self.assertEquals("Test2", service4.user_dict[1][1].user_dict)

        self.assertTrue(isinstance(service4.user_dict[2], InMemoryUserDetailsService))
        self.assertEquals("Test3", service4.user_dict[2].user_dict)

        self.assertTrue(isinstance(service4.user_dict[3], set))
        self.assertEquals(2, len(service4.user_dict[3]))
        self.assertTrue("Test4" in [item.user_dict for item in service4.user_dict[3]])
        self.assertTrue("Test5" in [item.user_dict for item in service4.user_dict[3]])

        self.assertTrue(isinstance(service4.user_dict[4], frozenset))
        self.assertEquals(2, len(service4.user_dict[4]))
        self.assertTrue("Test6" in [item.user_dict for item in service4.user_dict[4]])
        self.assertTrue("Test7" in [item.user_dict for item in service4.user_dict[4]])

        self.assertTrue(isinstance(service4.user_dict[5], set))
        self.assertEquals(1, len(service4.user_dict[5]))
        self.assertTrue("Test8" in [item.user_dict for item in service4.user_dict[5]])

        self.assertTrue(isinstance(service4.user_dict[6], frozenset))
        self.assertEquals(1, len(service4.user_dict[6]))
        self.assertTrue("Test9" in [item.user_dict for item in service4.user_dict[6]])

class XMLConfigTestCase4(unittest.TestCase):
    def testAThirdComplexContainer(self):
        ctx = ApplicationContext(XMLConfig("support/contextComplexXMLConfig4.xml"))
        service5 = ctx.get_object("user_details_service5")
        self.assertTrue(isinstance(service5.user_dict, set))
        self.assertEquals(4, len(service5.user_dict))

        for item in service5.user_dict:
            if isinstance(item, tuple):
                self.assertEquals(2, len(item))
                self.assertEquals("Test1", item[0].user_dict)
                self.assertEquals("Test2", item[1].user_dict)
            elif isinstance(item, InMemoryUserDetailsService):
                self.assertEquals("Test3", item.user_dict)
            elif isinstance(item, frozenset):
                if len(item) == 1:
                    self.assertTrue("Test9" in [i.user_dict for i in item])
                elif len(item) == 2:
                    values = [i.user_dict for i in item]
                    for test_value in ["Test6", "Test7"]:
                        self.assertTrue(test_value in values)
                else:
                    self.fail("Did NOT expect a frozenset of length %s" % len(item))
            else:
                self.fail("Cannot handle %s" % type(item))

class YamlConfigTestCase4(unittest.TestCase):
    def testAThirdComplexContainer(self):
        import logging
        logger = logging.getLogger("springpython.yamltest")

        ctx = ApplicationContext(YamlConfig("support/contextComplexYamlConfig4.yaml"))
        service5 = ctx.get_object("user_details_service5")
        self.assertTrue(isinstance(service5.user_dict, set))
        self.assertEquals(4, len(service5.user_dict))

        logger.debug("About to parse dict %s" % service5.user_dict)

        for item in service5.user_dict:
            logger.debug("Looking at item %s inside user_dict" % str(item))
            logger.debug("It is a %s type object." % type(item))
            if isinstance(item, tuple):
                self.assertEquals(2, len(item))
                self.assertEquals("Test1", item[0].user_dict)
                self.assertEquals("Test2", item[1].user_dict)
            elif isinstance(item, InMemoryUserDetailsService):
                self.assertEquals("Test3", item.user_dict)
            elif isinstance(item, frozenset):
                if len(item) == 1:
                    self.assertTrue("Test9" in [i.user_dict for i in item])
                elif len(item) == 2:
                    values = [i.user_dict for i in item]
                    for test_value in ["Test6", "Test7"]:
                        self.assertTrue(test_value in values)
                else:
                    self.fail("Did NOT expect a frozenset of length %s" % len(item))
            else:
                self.fail("Cannot handle %s" % type(item))

class XMLConfigTestCase5(unittest.TestCase):
    def testAFourthComplexContainer(self):
        ctx = ApplicationContext(XMLConfig("support/contextComplexXMLConfig5.xml"))
        service6 = ctx.get_object("user_details_service6")
        self.assertTrue(isinstance(service6.user_dict, frozenset))
        self.assertEquals(4, len(service6.user_dict))

        for item in service6.user_dict:
            if isinstance(item, tuple):
                self.assertEquals(2, len(item))
                self.assertEquals("Test1", item[0].user_dict)
                self.assertEquals("Test2", item[1].user_dict)
            elif isinstance(item, InMemoryUserDetailsService):
                self.assertEquals("Test3", item.user_dict)
            elif isinstance(item, frozenset):
                if len(item) == 1:
                    self.assertTrue("Test9" in [i.user_dict for i in item])
                elif len(item) == 2:
                    values = [i.user_dict for i in item]
                    for test_value in ["Test6", "Test7"]:
                        self.assertTrue(test_value in values)
                else:
                    self.fail("Did NOT expect a frozenset of length %s" % len(item))
            else:
                self.fail("Cannot handle %s" % type(item))

class YamlConfigTestCase5(unittest.TestCase):
    def testAFourthComplexContainer(self):
        ctx = ApplicationContext(YamlConfig("support/contextComplexYamlConfig5.yaml"))
        service6 = ctx.get_object("user_details_service6")
        self.assertTrue(isinstance(service6.user_dict, frozenset))
        self.assertEquals(4, len(service6.user_dict))

        for item in service6.user_dict:
            if isinstance(item, tuple):
                self.assertEquals(2, len(item))
                self.assertEquals("Test1", item[0].user_dict)
                self.assertEquals("Test2", item[1].user_dict)
            elif isinstance(item, InMemoryUserDetailsService):
                self.assertEquals("Test3", item.user_dict)
            elif isinstance(item, frozenset):
                if len(item) == 1:
                    self.assertTrue("Test9" in [i.user_dict for i in item])
                elif len(item) == 2:
                    values = [i.user_dict for i in item]
                    for test_value in ["Test6", "Test7"]:
                        self.assertTrue(test_value in values)
                else:
                    self.fail("Did NOT expect a frozenset of length %s" % len(item))
            else:
                self.fail("Cannot handle %s" % type(item))

class XMLConfigTestCase6(unittest.TestCase):
    def testAThirdComplexContainer(self):
        ctx = ApplicationContext(XMLConfig("support/contextComplexXMLConfig6.xml"))
        service4 = ctx.get_object("user_details_service4")
        self.assertTrue(isinstance(service4.user_dict, dict))
        self.assertEquals(8, len(service4.user_dict))

        self.assertTrue(isinstance(service4.user_dict["list"], list))
        self.assertEquals(2, len(service4.user_dict["list"]))

        self.assertTrue(isinstance(service4.user_dict["list"][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service4.user_dict["list"][0].user_dict)
        self.assertEquals("Test2", service4.user_dict["list"][1].user_dict)

        self.assertTrue(isinstance(service4.user_dict["tuple"], tuple))
        self.assertEquals(2, len(service4.user_dict["tuple"]))

        self.assertTrue(isinstance(service4.user_dict["tuple"][0], InMemoryUserDetailsService))
        self.assertEquals("Test1", service4.user_dict["tuple"][0].user_dict)
        self.assertEquals("Test2", service4.user_dict["tuple"][1].user_dict)

        self.assertTrue(isinstance(service4.user_dict["inner_object"], InMemoryUserDetailsService))
        self.assertEquals("Test3", service4.user_dict["inner_object"].user_dict)

        self.assertTrue(isinstance(service4.user_dict["set1"], set))
        self.assertEquals(2, len(service4.user_dict["set1"]))
        self.assertTrue("Test4" in [item.user_dict for item in service4.user_dict["set1"]])
        self.assertTrue("Test5" in [item.user_dict for item in service4.user_dict["set1"]])

        self.assertTrue(isinstance(service4.user_dict["frozenset1"], frozenset))
        self.assertEquals(2, len(service4.user_dict["frozenset1"]))
        self.assertTrue("Test6" in [item.user_dict for item in service4.user_dict["frozenset1"]])
        self.assertTrue("Test7" in [item.user_dict for item in service4.user_dict["frozenset1"]])

        self.assertTrue(isinstance(service4.user_dict["set2"], set))
        self.assertEquals(1, len(service4.user_dict["set2"]))
        self.assertTrue("Test8" in [item.user_dict for item in service4.user_dict["set2"]])

        self.assertTrue(isinstance(service4.user_dict["frozenset2"], frozenset))
        self.assertEquals(1, len(service4.user_dict["frozenset2"]))
        self.assertTrue("Test9" in [item.user_dict for item in service4.user_dict["frozenset2"]])

        self.assertEquals("Test10", service4.user_dict["value"])

class XMLConfigConstructorBasedTestCase(unittest.TestCase):
    """This test case exercises the constructors for XMLConfig"""

    def testUsingConstructorWithObjectReference(self):
        ctx = ApplicationContext(XMLConfig("support/contextXMLConfigWithConstructorArgs.xml"))

        controller = ctx.get_object("controller-list")
        self.assertTrue(isinstance(controller.executors, list))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

        controller = ctx.get_object("controller-set")
        self.assertTrue(isinstance(controller.executors, set))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

        controller = ctx.get_object("controller-dict")
        self.assertTrue(isinstance(controller.executors, dict))
        self.assertEquals(2, len(controller.executors))
        for key in controller.executors:
            self.assertTrue(isinstance(controller.executors[key], testSupportClasses.Executor))

        controller = ctx.get_object("controller-frozenset")
        self.assertTrue(isinstance(controller.executors, frozenset))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

        controller = ctx.get_object("controller-tuple")
        self.assertTrue(isinstance(controller.executors, tuple))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

class YamlConfigConstructorBasedTestCase(unittest.TestCase):
    """This test case exercises the constructors for XMLConfig"""

    def testUsingConstructorWithObjectReference(self):
        ctx = ApplicationContext(YamlConfig("support/contextYamlConfigWithConstructorArgs.yaml"))

        controller = ctx.get_object("controller-list")
        self.assertTrue(isinstance(controller.executors, list))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

        controller = ctx.get_object("controller-set")
        self.assertTrue(isinstance(controller.executors, set))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

        controller = ctx.get_object("controller-dict")
        self.assertTrue(isinstance(controller.executors, dict))
        self.assertEquals(2, len(controller.executors))
        for key in controller.executors:
            self.assertTrue(isinstance(controller.executors[key], testSupportClasses.Executor))

        controller = ctx.get_object("controller-frozenset")
        self.assertTrue(isinstance(controller.executors, frozenset))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

        controller = ctx.get_object("controller-tuple")
        self.assertTrue(isinstance(controller.executors, tuple))
        self.assertEquals(2, len(controller.executors))
        for executor in controller.executors:
            self.assertTrue(isinstance(executor, testSupportClasses.Executor))

class ObjectPostProcessorsTestCase(unittest.TestCase):
    """This test case exercises object post processors"""

    def testSimpleObjectPostProcessorXml(self):
         ctx = ApplicationContext(XMLConfig("support/contextObjectPostProcessing.xml"))
         processor = ctx.get_object("postProcessor")
         self.assertTrue(isinstance(processor, ObjectPostProcessor))
         self.assertFalse(hasattr(processor, "processedBefore"))
         self.assertFalse(hasattr(processor, "processedAfter"))
         obj = ctx.get_object("value")
         self.assertTrue(hasattr(obj, "processedBefore"))
         self.assertTrue(hasattr(obj, "processedAfter"))

    def testSimpleObjectPostProcessorYaml(self):
         ctx = ApplicationContext(YamlConfig("support/contextObjectPostProcessing.yaml"))
         processor = ctx.get_object("postProcessor")
         self.assertTrue(isinstance(processor, ObjectPostProcessor))
         self.assertFalse(hasattr(processor, "processedBefore"))
         self.assertFalse(hasattr(processor, "processedAfter"))
         obj = ctx.get_object("value")
         self.assertTrue(hasattr(obj, "processedBefore"))
         self.assertTrue(hasattr(obj, "processedAfter"))

class DisposableObjectTestCase(MockTestCase):
    """This test case exercises the DisposableObject behaviour."""
    
    def _get_sample_config(self, disposable_object):
        
        class SampleConfig(PythonConfig):
            def __init__(self):
                super(SampleConfig, self).__init__()
                
            @Object
            def my_disposable_object(self):
                return disposable_object
                
        return SampleConfig()
                
    
    def testDefaultDestroyMethod(self):
        
        class DisposableObjectWithDefaultDestroyMethod(Mock, DisposableObject):
            """ A DisposableObject with a default destroy method. Note the 
            AttributeError in __getattribute__, it's needed because pmock would 
            otherwise happily return a mock 'destroy_method' regardless of 
            whether one had been actually defined.
            """
            
            def destroy(self):
                self.destroy_called = True
            
            def __getattr__(self, attr_name):
                return object.__getattribute__(self, attr_name)
            
            def __getattribute__(self, attr_name):
                
                if attr_name == "destroy_method":
                    raise AttributeError()
                    
                return object.__getattribute__(self, attr_name)
        
        disposable_object = DisposableObjectWithDefaultDestroyMethod()
        
        disposable_object.stubs().after_properties_set()
        disposable_object.stubs().method("set_app_context")
        
        ctx = ApplicationContext(self._get_sample_config(disposable_object))
        my_disposable_object = ctx.get_object("my_disposable_object")
        
        ctx.shutdown_hook()

        # Will raise AttributeError if 'destroy' hasn't been called.
        self.assertTrue(my_disposable_object.destroy_called)
        
    
    def testCustomDestroyMethod(self):
        
        class DisposableObjectWithCustomDestroyMethod(Mock, DisposableObject):
            """ A DisposableObject with a custom destroy method, its name is 
            returned by __getattribute__, again, to prevent pmock from 
            returning a mock object.
            """
            
            def custom_destroy(self):
                self.custom_destroy_called = True
                
            def __getattr__(self, attr_name):
                return object.__getattribute__(self, attr_name)
            
            def __getattribute__(self, attr_name):
                
                if attr_name == "destroy_method":
                    return "custom_destroy"
                    
                return object.__getattribute__(self, attr_name)
        
        disposable_object = DisposableObjectWithCustomDestroyMethod()
        
        disposable_object.stubs().after_properties_set()
        disposable_object.stubs().method("set_app_context")

        ctx = ApplicationContext(self._get_sample_config(disposable_object))
        my_disposable_object = ctx.get_object("my_disposable_object")
        
        ctx.shutdown_hook()

        # Will raise AttributeError if 'custom_destroy' hasn't been called.
        self.assertTrue(my_disposable_object.custom_destroy_called)
        
    def testShutdownHookRegisterdWithAtExit(self):
        
        class Dummy(DisposableObject):
            def destroy(self):
                pass
        
        ctx = ApplicationContext(self._get_sample_config(Dummy()))
        
        seen_shutdown_hook = False
        
        # We need to iterate through all registered atexit handlers, our handler
        # will be will among the other handlers registered in previous tests.
        # Note: we're using a private atexit API here.
        for handler_info in atexit._exithandlers:
            func = handler_info[0]
            if func == ctx.shutdown_hook:
                seen_shutdown_hook = True
        
        self.assertTrue(seen_shutdown_hook)
