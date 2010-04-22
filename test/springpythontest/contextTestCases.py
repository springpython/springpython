# -*- coding: utf-8 -*-

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
import random
import unittest
from decimal import Decimal
from StringIO import StringIO

from springpython.context import DisposableObject
from springpython.context import ApplicationContext
from springpython.context import ObjectPostProcessor
from springpython.config import PythonConfig
from springpython.config import PyContainerConfig
from springpython.config import SpringJavaConfig
from springpython.config import Object
from springpython.config import XMLConfig, xml_mappings
from springpython.config import YamlConfig, yaml_mappings
from springpython.config import Object, ObjectDef
from springpython.factory import PythonObjectFactory
from springpython.remoting.pyro import PyroProxyFactory
from springpython.security.userdetails import InMemoryUserDetailsService
from springpythontest.support import testSupportClasses
from springpython.context.scope import SINGLETON, PROTOTYPE
from springpython.container import AbstractObjectException, InvalidObjectScope

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
        self.assertFalse(movieAppContainer.object_defs[u"MovieLister"].lazy_init)
        self.assertTrue(movieAppContainer.object_defs[u"MovieFinder"].lazy_init)
        self.assertTrue(movieAppContainer.object_defs[u"SingletonString"].lazy_init)
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

        self.assertTrue(ctx.object_defs[u"SingletonString"].lazy_init)
        
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
        self.assertFalse(movieAppContainer.object_defs[u"MovieLister"].lazy_init)
        self.assertTrue(movieAppContainer.object_defs[u"MovieFinder"].lazy_init)
        self.assertTrue(movieAppContainer.object_defs[u"SingletonString"].lazy_init)
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
                
class YamlConfigTypesCustomizing(unittest.TestCase):
    """ Exercises the behaviour of customizations of types.
    """
    
    def test_default_mapping_ok(self):
        container = ApplicationContext(YamlConfig("support/contextYamlBuiltinTypes.yaml"))
        
        self.assertEqual(12, len(container.objects))
        
        my_string = container.get_object("MyString")
        my_unicode = container.get_object("MyUnicode")
        my_int = container.get_object("MyInt")
        my_long = container.get_object("MyLong")
        my_float = container.get_object("MyFloat")
        my_decimal = container.get_object("MyDecimal")
        my_boolean = container.get_object("MyBoolean")
        my_complex = container.get_object("MyComplex")
        my_list = container.get_object("MyList")
        my_tuple = container.get_object("MyTuple")
        my_dict = container.get_object("MyDict")
        my_ref = container.get_object("MyRef")
        
        self.assertEqual(my_string, "My string")
        self.assertEqual(my_unicode, u'Zażółć gęślą jaźń')
        self.assertEqual(my_int, 10)
        self.assertEqual(my_long, 100000000000000000000000)
        self.assertEqual(my_float, 3.14)
        self.assertEqual(my_decimal, Decimal("12.34"))
        self.assertEqual(my_boolean, False)
        self.assertEqual(my_complex, complex(10,0))
        self.assertEqual(my_list, [1, 2, 3, 4])
        self.assertEqual(my_tuple, ("a", "b", "c"))
        self.assertEqual(my_dict, {1: "a", 2: "b", 3: "c"})
        self.assertEqual(my_ref, Decimal("12.34"))
        
    def test_default_mapping_error_no_type_defined(self):
        # Will raise KeyError: 'class'
        try:
            ApplicationContext(YamlConfig("support/contextYamlBuiltinTypesErrorNoTypeDefined.yaml"))
        except KeyError, e:
            # Meaning there was no 'class' key found.
            self.assertEqual(e.message, "class")
        else:
            self.fail("KeyError should've been raised")
            
    def test_default_mappings_dictionary_contents(self):
        self.assertEqual(yaml_mappings, {'tuple': 'types.TupleType',
                         'int': 'types.IntType', 'float': 'types.FloatType',
                         'unicode': 'types.UnicodeType',
                         'decimal': 'decimal.Decimal', 'list': 'types.ListType',
                         'long': 'types.LongType', 'complex': 'types.ComplexType',
                         'bool': 'types.BooleanType', 'str': 'types.StringType',
                         'dict': 'types.DictType'})
        
    def test_custom_mappings(self):
        yaml_mappings.update({"interest_rate": "springpythontest.support.interest_rate.InterestRate"})
        container = ApplicationContext(YamlConfig("support/contextYamlCustomMappings.yaml"))
        
        self.assertEqual(1, len(container.objects))
        base_interest_rate = container.get_object("base_interest_rate")
        self.assertEqual("7.35", base_interest_rate.value) 
        
        del yaml_mappings["interest_rate"]

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

class XMLConfigTypesMappingsTestCase(unittest.TestCase):
    """This test case exercises the types mappings for XMLConfig"""
    
    def test_types_mappings(self):
        self.assertEqual({'complex': 'types.ComplexType', 
            'bool': 'types.BooleanType', 'unicode': 'types.UnicodeType',
            'str': 'types.StringType', 'int': 'types.IntType',
            'decimal': 'decimal.Decimal', 'float': 'types.FloatType',
            'long': 'types.LongType'}, xml_mappings)
        
        ctx = ApplicationContext(XMLConfig("support/contextXMLConfigTypesMappings.xml"))
        self.assertEqual(8, len(ctx.objects))
        
        my_string = ctx.get_object("MyString")
        my_unicode = ctx.get_object("MyUnicode")
        my_int = ctx.get_object("MyInt")
        my_long = ctx.get_object("MyLong")
        my_float = ctx.get_object("MyFloat")
        my_decimal = ctx.get_object("MyDecimal")
        my_bool = ctx.get_object("MyBool")
        my_complex = ctx.get_object("MyComplex")
        
        self.assertEqual(my_string, "My string")
        self.assertEqual(my_unicode, u"Zażółć gęślą jaźń")
        self.assertEqual(my_int, 10)
        self.assertEqual(my_long, 100000000000000000000000)
        self.assertEqual(my_float, 3.14)
        self.assertEqual(my_decimal, Decimal("12.34"))
        self.assertEqual(my_bool, False)
        self.assertEqual(my_complex, 10+0j)

class XMLConfigMixedXSDVersionsTestCase(unittest.TestCase):
    """ Exercises the XMLConfig behaviour when given XML config files of
    different XSD versions.
    """
    def test_mixed_xsd_versions(self):
        config_files = ["support/contextXMLConfigXSD10.xml", "support/contextXMLConfigXSD11.xml"]
        ctx = ApplicationContext(XMLConfig(config_files))
        
        self.assertEqual(2, len(ctx.objects))
        
        my_string_10 = ctx.get_object("MyString10")
        my_string_11 = ctx.get_object("MyString11")
        
        self.assertEqual(my_string_10, "My string XSD 1.0")
        self.assertEqual(my_string_11, "My string XSD 1.1")

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
            
class PyroFactoryTestCase(unittest.TestCase):
    def testPyroFactoryDoesntGetApply(self):
        class MyPythonConfig(PythonConfig):
            @Object
            def my_pyrofactory(config_self): # let lambda access parent test self
                ppf = PyroProxyFactory()
                # small hack to make the thing testable
                ppf.__dict__["after_properties_set"] = lambda: self.fail(
                    "after_properties_set mustn't be called on "
                    "PyroProxyFactory objects.")
                return ppf
        
        ctx = ApplicationContext(MyPythonConfig())


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
        
class AppContextObjectsObjectsDefsTestCase(MockTestCase):
    """This test case exercises the application contexts' .objects and
    .object_defs behaviour."""
    
    def _get_querying_context(self):
        
        class MyClass(object):
            pass
        
        class MySubclass(MyClass):
            pass
        
        class SampleContext(PythonConfig):
            def __init__(self):
                super(SampleContext, self).__init__()
                
            @Object
            def http_port(self):
                return 18000
            
            @Object
            def https_port(self):
                return self._get_https_port()
            
            def _get_https_port(self):
                return self.http_port() + 443
                
            @Object
            def my_class_object1(self):
                return MyClass()
                
            @Object
            def my_class_object2(self):
                return MyClass()
                
            @Object
            def my_subclass_object1(self):
                return MySubclass()
                
            @Object
            def my_subclass_object2(self):
                return MySubclass()
                
            @Object
            def my_subclass_object3(self):
                return MySubclass()
                
        return ApplicationContext(SampleContext()), MyClass, MySubclass
        
    def _get_modifying_context(self):

        class SampleContext2(PythonConfig):
            def __init__(self):
                super(SampleContext2, self).__init__()
                
        return ApplicationContext(SampleContext2())
    
    def testQuerying(self):
        ctx, MyClass, MySubclass, = self._get_querying_context()
        
        class_instances = ctx.get_objects_by_type(MyClass)
        subclass_instances = ctx.get_objects_by_type(MyClass, False)
        int_instances = ctx.get_objects_by_type(int)
        
        self.assertTrue(isinstance(class_instances, dict))
        self.assertTrue(isinstance(subclass_instances, dict))
        self.assertTrue(isinstance(int_instances, dict))
        
        self.assertEquals(5, len(class_instances))
        self.assertEquals(3, len(subclass_instances))
        self.assertEquals(2, len(int_instances))
        
        for name, instance in class_instances.items():
            self.assertTrue(isinstance(instance, MyClass))
            
        for name, instance in subclass_instances.items():
            self.assertTrue(isinstance(instance, MyClass) and type(instance) is not MyClass)
            
        for name, instance in int_instances.items():
            self.assertTrue(isinstance(instance, int))
            
        self.assertTrue("http_port" in ctx.objects)
        self.assertTrue("http_port" in ctx.objects)
        self.assertFalse("ftp_port" in ctx.object_defs)
        self.assertEqual(7, len(ctx.objects))
        
        for name in ctx.objects:
            self.assertTrue(isinstance(name, basestring))
            
        for name in ctx.object_defs:
            self.assertTrue(isinstance(name, basestring))
            
    def testModifying(self):
        ctx = self._get_modifying_context()
        
        class Foo(object):
            pass
                
        class Bar(object):
            pass
        
        @Object(PROTOTYPE)
        def foo():
            """ Returns a new instance of Foo on each call.
            """
            return Foo()
            
        @Object # SINGLETON is the default.
        def bar():
            """ Returns a singleton Bar every time accessed.
            """
            return Bar()
            
        # A reference to the function wrapping the actual 'foo' function.
        foo_wrapper = foo.func_globals["_call_"]
        
        # Create an object definition, note that we're telling to return
        foo_object_def = ObjectDef(id="foo",
            factory=PythonObjectFactory(foo, foo_wrapper), scope=PROTOTYPE,
            lazy_init=foo_wrapper.lazy_init)
        
        # A reference to the function wrapping the actual 'bar' function.
        bar_wrapper = foo.func_globals["_call_"]
        
        bar_object_def = ObjectDef(id="foo",
            factory=PythonObjectFactory(bar, bar_wrapper), scope=SINGLETON,
            lazy_init=bar_wrapper.lazy_init)
        
        # No definitions at this point
        self.assertEqual({}, ctx.object_defs)
        
        ctx.object_defs["foo"] = foo_object_def
        ctx.object_defs["bar"] = bar_object_def
        
        # Two object defs have just been added.
        self.assertEqual(2, len(ctx.object_defs))
        
        for x in range(3):
            foo_instance = ctx.get_object("foo")
            self.assertTrue(isinstance(foo_instance, Foo))
        
        # Will leak the 'bar_instance' for later use.
        for x in range(3):
            bar_instance = ctx.get_object("bar")
            self.assertTrue(isinstance(bar_instance, Bar))
            
        # 'foo' object is a PROTOTYPE and 'bar' is a SINGLETON so there must've
        # been exactly one object created so far.
        self.assertEqual(1, len(ctx.objects))
        
        obj = ctx.objects[ctx.objects.keys()[0]]
        self.assertTrue(obj is bar_instance)
        
class AbstractObjectsTestCase(MockTestCase):
    """Test cases related to handling of abstract container managed objects.
    """
    
    def _get_python_config(self):
        
        class Request(object):
            def __init__(self, nounce=None, user=None, password=None):
                self.nounce = nounce
                self.user = user
                self.password = password
        
            def __str__(self):
                return "<id=%s %s %s %s>" % (hex(id(self)), self.nounce, self.user, self.password)
                
        class CRMService(object):
            def __init__(self, ip=None, port=None, path=None):
                self.ip = ip
                self.port = port
                
            def invoke(self, request):
                return "CRM OK %s" % request.nounce
                
            def __str__(self):
                return "<id=%s %s %s>" % (hex(id(self)), self.ip, self.port)
                
        class IVRService(object):
            def __init__(self, instance=None):
                self.instance = instance
                
            def invoke(self, request):
                return "IVR OK %s" % request.nounce
                
            def __str__(self):
                return "<id=%s %s>" % (hex(id(self)), self.instance)
        
        class TestAbstractContext(PythonConfig):
        
            @Object(PROTOTYPE, lazy_init=True, abstract=True)
            def request(self):
                request = Request()
                request.nounce = "".join([random.choice("1234567890") for x in range(16)])
        
                return request
        
            @Object(PROTOTYPE, parent="request")
            def crm_request(self, request=None):
                request.user = "foo"
                request.password = "bar"
        
                return request
        
            @Object(PROTOTYPE, parent="request")
            def ivr_request(self, request=None):
                request.user = "baz"
                request.password = "frobble"
        
                return request
                
            @Object(abstract=True)
            def crm_service(self):
                service = CRMService()
                service.ip = "192.168.1.145"
                service.port = 2627
                
                return service
                
            @Object(parent="crm_service")
            def get_customer_id(self, service=None):
                request = self.get_object("crm_request")
                
                return service.invoke(request)
                
            @Object(PROTOTYPE, parent="crm_service")
            def get_customer_profile(self, service=None):
                request = self.get_object("crm_request")
                
                return service.invoke(request)
                
            @Object(PROTOTYPE, abstract=True)
            def ivr_service(self):
                service = CRMService()
                service.ip = "192.168.1.145"
                service.port = 2627
                
                return service
                
            @Object(PROTOTYPE, parent="ivr_service")
            def get_customer_location(self, service=None):
                request = self.get_object("ivr_request")
                
                return service.invoke(request)
                
            @Object(parent="ivr_service")
            def get_customer_complaints(self, service=None):
                request = self.get_object("ivr_request")
                
                return service.invoke(request)
                
        return TestAbstractContext
    
    def testPythonConfigAbstractObjects(self):
        ctx_class = self._get_python_config()
        container = ApplicationContext(ctx_class())
        
        # Use a variety of scopes to ensure the proper handling of abstract
        # objects doesn't depend on their scopes.
        
        # request => PROTOTYPE
        # crm_request => PROTOTYPE
        # ivr_request => PROTOTYPE
        
        # crm_service => SINGLETON
        # get_customer_id => SINGLETON
        # get_customer_profile => PROTOTYPE
        
        # ivr_service => PROTOTYPE
        # get_customer_location => PROTOTYPE
        # get_customer_complaints => SINGLETON
        
        # get_object's 'ignore_abstract' is False by default.
        self.assertRaises(AbstractObjectException, container.get_object, "request")
        self.assertRaises(AbstractObjectException, container.get_object, "crm_service")
        self.assertRaises(AbstractObjectException, container.get_object, "ivr_service")
        
        # Won't raise AbstractObjectException because the 'ignore_abstract' flag is True.
        request = container.get_object("request", True)
        crm_service = container.get_object("crm_service", True)
        ivr_service = container.get_object("ivr_service", True)
        
        self.assertEquals(16, len(request.nounce))
        self.assertTrue(str.isdigit(request.nounce))
        self.assertEquals(None, request.user)
        self.assertEquals(None, request.password)
        
        crm_request = container.get_object("crm_request")
        ivr_request = container.get_object("ivr_request")
        
        self.assertEquals(16, len(crm_request.nounce))
        self.assertTrue(str.isdigit(crm_request.nounce))
        self.assertEquals("foo", crm_request.user)
        self.assertEquals("bar", crm_request.password)
        
        self.assertEquals(16, len(ivr_request.nounce))
        self.assertTrue(str.isdigit(ivr_request.nounce))
        self.assertEquals("baz", ivr_request.user)
        self.assertEquals("frobble", ivr_request.password)
        
        self.assertNotEquals(crm_request.nounce, ivr_request.nounce)

        # Abstract objects may be lazily-initialized or not, and that shouldn't
        # get in the way of how they're handled, AbstractObjectException shouldn't
        # be raised in either case.
        
        get_customer_id = container.get_object("get_customer_id")
        get_customer_profile = container.get_object("get_customer_profile")
        
        get_customer_location = container.get_object("get_customer_location")
        get_customer_complaints = container.get_object("get_customer_complaints")
        
    def testXMLAndYamlConfigAbstractObjects(self):
        
        #
        # There are various combinations and corner cases that need be tested
        # here, depending on whether an application context uses properties only,
        # properties and constructor arguments or constructor args solely. What
        # also needs be taken into account is if there are any abstract objects
        # and if so, how many levels of inheritance are there.
        #
        # 1 - uses properties only
        #
        # 2 - uses properties and named constructor arguments
        #
        # 3 - uses properties, named and positional arguments
        #
        # 4 - used for testing of how positional arguments are being handled
        #     (doesn't use properties nor named arguments)
        #
        # Note that some assertions are identical for both XML and Yaml config
        # modes. From the user's standpoint, the only difference is that XMLConfig
        # allows for defining both positional and named arguments whereas with
        # Yaml config one needs to choose either positional or named constructor
        # parameters.
        #
        
        #
        # Properties only
        #
        
        xml_ctx1 = ApplicationContext(XMLConfig("support/contextXMLConfigAbstract1.xml"))
        yaml_ctx1 = ApplicationContext(YamlConfig("support/contextYamlAbstract1.yaml"))
        
        for ctx in(xml_ctx1, yaml_ctx1):
        
            # There should be only two objects defined, the abstract one which
            # is also lazily-initialized shouldn't have been added
            # to the container.
            self.assertEquals(2, len(ctx.objects))
            
            # All object definitions, no matter abstract or concrete ones,
            # should have been added though.
            self.assertEquals(4, len(ctx.object_defs))
            self.assertEquals(["crm_service", "get_customer_id1", "get_customer_id2", "service"], 
                                sorted(ctx.object_defs.keys()))
            
            get_customer_id1 = ctx.get_object("get_customer_id1")
            self.assertEquals("192.168.1.153", get_customer_id1.ip)
            self.assertEquals("3392", get_customer_id1.port)
            self.assertEquals("/soap/invoke/get-customer-id1", get_customer_id1.path)
            
            get_customer_id2 = ctx.get_object("get_customer_id2")
            self.assertEquals("192.168.1.153", get_customer_id2.ip)
            self.assertEquals("3392", get_customer_id2.port)
            self.assertEquals("/soap/invoke/get-customer-id2", get_customer_id2.path)
            
            get_customer_id1_def = ctx.object_defs["get_customer_id1"]
            self.assertEquals(False, get_customer_id1_def.abstract)
            self.assertEquals(SINGLETON, get_customer_id1_def.scope)
            self.assertEquals("crm_service", get_customer_id1_def.parent)
            
            get_customer_id2_def = ctx.object_defs["get_customer_id2"]
            self.assertEquals(False, get_customer_id2_def.abstract)
            self.assertEquals(PROTOTYPE, get_customer_id2_def.scope)
            self.assertEquals("crm_service", get_customer_id2_def.parent)
            
            # Abstract objects must not be added to the container.
            self.assertRaises(KeyError, ctx.get_object, "foo_root1")
            self.assertRaises(KeyError, ctx.get_object, "foo_root2")
        
        #
        # Properties and named constructor arguments
        #
        
        xml_ctx2 = ApplicationContext(XMLConfig("support/contextXMLConfigAbstract2.xml"))
        yaml_ctx2 = ApplicationContext(YamlConfig("support/contextYamlAbstract2.yaml"))
        
        for ctx in(xml_ctx2, yaml_ctx2):
        
            foo_child1 = ctx.get_object("foo_child1")
            self.assertEquals("aaa", foo_child1.a)
            self.assertEquals("bbb", foo_child1.b)
            self.assertEquals(None, foo_child1.c)
            self.assertEquals(None, foo_child1.d)
            self.assertEquals(None, foo_child1.e)
            self.assertEquals(None, foo_child1.f)
            self.assertEquals(None, foo_child1.g)
            
            foo_child2 = ctx.get_object("foo_child2")
            self.assertEquals("aaa", foo_child2.a)
            self.assertEquals("bbb", foo_child2.b)
            self.assertEquals("ccc", foo_child2.c)
            self.assertEquals(None, foo_child2.d)
            self.assertEquals(None, foo_child2.e)
            self.assertEquals(None, foo_child2.f)
            self.assertEquals(None, foo_child2.g)
            
            foo_child3 = ctx.get_object("foo_child3")
            self.assertEquals("aaa", foo_child3.a)
            self.assertEquals("bbbb", foo_child3.b)
            self.assertEquals("cccc", foo_child3.c)
            self.assertEquals("dddd", foo_child3.d)
            self.assertEquals("eeee", foo_child3.e)
            self.assertEquals(None, foo_child3.f)
            self.assertEquals(None, foo_child3.g)
            
            foo_child4 = ctx.get_object("foo_child4")
            self.assertEquals("aaa", foo_child4.a)
            self.assertEquals("bbbb", foo_child4.b)
            self.assertEquals("cccc", foo_child4.c)
            self.assertEquals("dddd", foo_child4.d)
            self.assertEquals(None, foo_child4.e)
            self.assertEquals("ffff", foo_child4.f)
            self.assertEquals("MyString", foo_child4.g)
         
        # 
        # Properties, named and positional arguments
        #

        xml_ctx3 = ApplicationContext(XMLConfig("support/contextXMLConfigAbstract3.xml"))
        
        foo_root3 = xml_ctx3.get_object("foo_root3", True)
        self.assertEquals("first_pos_arg_in_foo_root3", foo_root3.a)
        self.assertEquals(None, foo_root3.b)
        self.assertEquals("cccccc_foo_root3", foo_root3.c)
        self.assertEquals("dddddd", foo_root3.d)
        self.assertEquals(None, foo_root3.e)
        self.assertEquals(None, foo_root3.f)
        self.assertEquals(None, foo_root3.g)
        
        foo_root4 = xml_ctx3.get_object("foo_root4", True)
        self.assertEquals("MyString", foo_root4.a)
        self.assertEquals(None, foo_root4.b)
        self.assertEquals("cccccc_foo_root4", foo_root4.c)
        self.assertEquals("dddddd", foo_root4.d)
        self.assertEquals(None, foo_root4.e)
        self.assertEquals("ffffff", foo_root4.f)
        self.assertEquals("MyString", foo_root4.g)
        
        foo_child5 = xml_ctx3.get_object("foo_child5")
        self.assertEquals("MyString", foo_child5.a)
        self.assertEquals(None, foo_child5.b)
        self.assertEquals("cccccc_foo_child5", foo_child5.c)
        self.assertEquals("dddddd_foo_child5", foo_child5.d)
        self.assertEquals(None, foo_child5.e)
        self.assertEquals("ffffff", foo_child5.f)
        self.assertEquals("gggggg_foo_child5", foo_child5.g)
        
        #
        # Properties, named and positional arguments
        #
        
        yaml_ctx3 = ApplicationContext(YamlConfig("support/contextYamlAbstract3.yaml"))
        
        foo_root_yaml3 = yaml_ctx3.get_object("foo_root_yaml3", True)
        self.assertEquals("aaaaaa", foo_root_yaml3.a)
        self.assertEquals("MyString", foo_root_yaml3.b)
        self.assertEquals(None, foo_root_yaml3.c)
        self.assertEquals("dddddd", foo_root_yaml3.d)
        self.assertEquals(None, foo_root_yaml3.e)
        self.assertEquals(None, foo_root_yaml3.f)
        self.assertEquals(None, foo_root_yaml3.g)
        
        foo_root_yaml4 = yaml_ctx3.get_object("foo_root_yaml4", True)
        self.assertEquals("aaaaaa_foo_root_yaml4", foo_root_yaml4.a)
        self.assertEquals("bbbbbb", foo_root_yaml4.b)
        self.assertEquals("MyString", foo_root_yaml4.c)
        self.assertEquals("dddddd", foo_root_yaml4.d)
        self.assertEquals("eeeeee_foo_root_yaml4", foo_root_yaml4.e)
        self.assertEquals(None, foo_root_yaml4.f)
        self.assertEquals(None, foo_root_yaml4.g)
        
        #
        # Positional arguments only
        #
        
        xml_ctx4 = ApplicationContext(XMLConfig("support/contextXMLConfigAbstract4.xml"))
        yaml_ctx4 = ApplicationContext(YamlConfig("support/contextYamlAbstract4.yaml"))
        
        for ctx in(xml_ctx4, yaml_ctx4):
            
            foo_root_pos1 = ctx.get_object("foo_root_pos1", True)
            self.assertEquals("a_foo_root_pos1", foo_root_pos1.a)
            self.assertEquals("b_foo_root_pos1", foo_root_pos1.b)
            self.assertEquals("MyString", foo_root_pos1.c)
            self.assertEquals("d_foo_root_pos1", foo_root_pos1.d)
            self.assertEquals("e_foo_root_pos1", foo_root_pos1.e)
            self.assertEquals("f_foo_root_pos1", foo_root_pos1.f)
            self.assertEquals("g_foo_root_pos1", foo_root_pos1.g)
            
            foo_parent_pos2 = ctx.get_object("foo_parent_pos2", True)
            self.assertEquals("a_foo_parent_pos2", foo_parent_pos2.a)
            self.assertEquals("b_foo_parent_pos2", foo_parent_pos2.b)
            self.assertEquals("c_foo_parent_pos2", foo_parent_pos2.c)
            self.assertEquals("d_foo_parent_pos2", foo_parent_pos2.d)
            self.assertEquals("e_foo_parent_pos2", foo_parent_pos2.e)
            self.assertEquals("f_foo_root_pos1", foo_parent_pos2.f)
            self.assertEquals("g_foo_root_pos1", foo_parent_pos2.g)
            
            foo_parent_pos3 = ctx.get_object("foo_parent_pos3", True)
            self.assertEquals("a_foo_parent_pos3", foo_parent_pos3.a)
            self.assertEquals("MyString", foo_parent_pos3.b)
            self.assertEquals("c_foo_parent_pos2", foo_parent_pos3.c)
            self.assertEquals("d_foo_parent_pos2", foo_parent_pos3.d)
            self.assertEquals("e_foo_parent_pos2", foo_parent_pos3.e)
            self.assertEquals("f_foo_root_pos1", foo_parent_pos3.f)
            self.assertEquals("g_foo_root_pos1", foo_parent_pos3.g)
            
            foo_parent_pos4 = ctx.get_object("foo_parent_pos4", True)
            self.assertEquals("a_foo_parent_pos4", foo_parent_pos4.a)
            self.assertEquals("b_foo_parent_pos4", foo_parent_pos4.b)
            self.assertEquals("c_foo_parent_pos4", foo_parent_pos4.c)
            self.assertEquals("d_foo_parent_pos2", foo_parent_pos4.d)
            self.assertEquals("e_foo_parent_pos2", foo_parent_pos4.e)
            self.assertEquals("f_foo_root_pos1", foo_parent_pos4.f)
            self.assertEquals("g_foo_root_pos1", foo_parent_pos4.g)
            
            foo_child_pos5 = ctx.get_object("foo_child_pos5", True)
            self.assertEquals("a_foo_child_pos5", foo_child_pos5.a)
            self.assertEquals("b_foo_child_pos5", foo_child_pos5.b)
            self.assertEquals("c_foo_parent_pos4", foo_child_pos5.c)
            self.assertEquals("d_foo_parent_pos2", foo_child_pos5.d)
            self.assertEquals("e_foo_parent_pos2", foo_child_pos5.e)
            self.assertEquals("f_foo_root_pos1", foo_child_pos5.f)
            self.assertEquals("g_foo_root_pos1", foo_child_pos5.g)
        
        
class ScopesTestCase(MockTestCase):
    """Test cases related to proper handling of scopes of objects.
    """
    
    def test_scope(self):
        
        class TestContext(PythonConfig):
            
            @Object(PROTOTYPE)
            def prototype(self):
                pass
            
            @Object(SINGLETON)
            def singleton(self):
                pass
            
        invalid = """
class InvalidScopeContainingContext(PythonConfig):
    @Object("FOOBAR")
    def invalid(self):
        pass"""
          
        # If we pass this line then only correct scopes will have been used
        # in TestContext.
        container = ApplicationContext(TestContext())
        
        for object_def in container.object_defs:
            if object_def == "singleton":
                self.assertEquals(SINGLETON, container.object_defs[object_def].scope)
            elif object_def == "prototype":
                self.assertEquals(PROTOTYPE, container.object_defs[object_def].scope)
            else:
                self.fail("Unexpected object_def [%s]" % object_def)
        
        _globals, _locals = {}, {}
        
        _globals["PythonConfig"] = PythonConfig
        _globals["Object"] = Object
        
        def should_raise_invalid_object_scope():
            exec invalid in _globals, _locals
            
        self.assertRaises(InvalidObjectScope, should_raise_invalid_object_scope)
