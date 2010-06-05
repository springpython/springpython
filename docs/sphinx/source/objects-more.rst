More on IoC
===========

Object Factories
----------------

Spring Python offers two types of factories, *springpython.factory.ReflectiveObjectFactory*
and *springpython.factory.PythonObjectFactory*. These classes should rarely be used directly by
the developer. They are instead used by the different types of configuration
scanners.

Testable Code
-------------

One key value of using the IoC container is how you can isolate parts of
your code for better testing. Imagine you had the following configuration::

    from springpython.config import *
    from springpython.context import *

    class MovieBasedApplicationContext(PythonConfig):
        def __init__(self):
            super(MovieBasedApplicationContext, self).__init__()

        @Object(scope.PROTOTYPE)
        def MovieLister(self):
            lister = MovieLister()
            lister.finder = self.MovieFinder()
            lister.description = self.SingletonString()
            self.logger.debug("Description = %s" % lister.description)
            return lister

        @Object(scope.SINGLETON)
        def MovieFinder(self):
            return ColonMovieFinder(filename="support/movies1.txt")

        @Object    # scope.SINGLETON is the default
        def SingletonString(self):
            return StringHolder("There should only be one copy of this string")

To inject a test double for *MovieFinder*, your test code would only have to
extend the class and override the *MovieFinder* method, and replace it with your
stub or mock object. Now you have a nicely isolated instance of *MovieLister*::

    class MyTestableAppContext(MovieBasedApplicationContext):
        def __init__(self):
            super(MyTestableAppContext, self).__init__()

        @Object
        def MovieFinder(self):
            return MovieFinderStub()


Mixing Configuration Modes
--------------------------

Spring Python also supports providing object definitions from multiple sources,
and allowing them to reference each other. This section shows the same app
context, but split between two different sources.

.. highlight:: xml

First, the XML file containing the key object that gets pulled::

    <?xml version="1.0" encoding="UTF-8"?>
    <components xmlns="http://www.springframework.org/springpython/schema/pycontainer-components"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/pycontainer-components
                http://springpython.webfactional.com/schema/context/spring-python-pycontainer-context-1.0.xsd">

        <component id="MovieLister" class="springpythontest.support.testSupportClasses.MovieLister" scope="prototype">
            <property name="finder" local="MovieFinder"/>
            <property name="description" local="SingletonString"/>
        </component>

        <component id="SingletonString" class="springpythontest.support.testSupportClasses.StringHolder">
            <property name="str">"There should only be one copy of this string"</property>
        </component>
    </components>

.. highlight:: python

Notice that *MovieLister* is referencing *MovieFinder*, however that object is NOT
defined in this location. The definition is found elsewhere::

    class MixedApplicationContext(PythonConfig):
        def __init__(self):
            super(MixedApplicationContext, self).__init__()

        @Object(scope.SINGLETON)
        def MovieFinder(self):
            return ColonMovieFinder(filename="support/movies1.txt")

.. note::

    Object ref must match function name

    In this situation, an XML-based object is referencing Python code by the
    name MovieFinder. It is of paramount importance that the Python function
    have the same name as the referenced string.

With some simple code, this is all brought together when the container is created::

    from springpython.context import ApplicationContext
    from springpython.config import PyContainerConfig

    container = ApplicationContext([MixedApplicationContext(),
                                    PyContainerConfig("mixed-app-context.xml")])
    movieLister = container.get_object("MovieLister")

In this case, the XML-based object definition signals the container to look
elsewhere for a copy of the MovieFinder object, and it succeeds by finding it
in MixedApplicationContext.

It is possible to switch things around, but it requires a slight change::

    class MixedApplicationContext2(PythonConfig):
        def __init__(self):
            super(MixedApplicationContext2, self).__init__()

        @Object(scope.PROTOTYPE)
        def MovieLister(self):
            lister = MovieLister()
            lister.finder = self.app_context.get_object("MovieFinder")  # <-- only line that is different
            lister.description = self.SingletonString()
            self.logger.debug("Description = %s" % lister.description)
            return lister

        @Object    # scope.SINGLETON is the default
        def SingletonString(self):
            return StringHolder("There should only be one copy of this string")

.. highlight:: xml

::

    <?xml version="1.0" encoding="UTF-8"?>
    <components xmlns="http://www.springframework.org/springpython/schema/pycontainer-components"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/pycontainer-components
                http://springpython.webfactional.com/schema/context/spring-python-pycontainer-context-1.0.xsd">

        <component id="MovieFinder" class="springpythontest.support.testSupportClasses.ColonMovieFinder" scope="singleton">
            <property name="filename">"support/movies1.txt"</property>
        </component>

    </components>

An XML-based object definition can refer to a @Object  by name, however,
the Python code has to change its direct function call to a container lookup,
otherwise it will fail.

.. note::

    PythonConfig is ApplicationContextAware

    In order to perform a *get_object*, the configuration needs a handle on the
    surrounding container. The base class *PythonConfig* provides this, so that you
    can easily look for any object (local or not) by using *self.app_context.get_object("name")*.

Querying and modifying the ApplicationContext in runtime
--------------------------------------------------------

*ApplicationContext* instances expose two attributes and an utility method which
let you learn about their current state and dynamically alter them in runtime.

* *object_defs* is a dictionary of objects definitions, that is, the templates
  based upon which the container will create appropriate objects, e.g. your singletons,

* *objects* is a dictionary of already created objects stored for later use,

* *get_objects_by_type(type, include_type=True)* returns those ApplicationContext's
  objects which are instances of a given type or of its subclasses.
  If *include_type* is False then only instances of the type's *subclasses* will
  be returned.

.. highlight:: python

Here's an example showing how you can easily query a context to find out what
definitions and objects it holds. The context itself is stored using
:doc:`PythonConfig <objects-pythonconfig>` in the *sample_context.py* module and
*demo.py* contains the code which examines the context::

    #
    # sample_context.py
    #

    from springpython.config import Object
    from springpython.context import scope
    from springpython.config import PythonConfig

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

::

    #
    # demo.py
    #

    # Spring Python
    from springpython.context import ApplicationContext

    # Our sample code.
    from sample_context import SampleContext, MyClass, MySubclass

    # Create the context.
    ctx = ApplicationContext(SampleContext())

    # Do we have an 'http_port' object?
    print "http_port" in ctx.objects

    # Does the context have a definition of an 'ftp_port' object?
    print "ftp_port" in ctx.object_defs

    # How many objects are there? Observe the result is 7, that's because one of
    # the methods - _get_https_port - is not managed by the container.
    print len(ctx.objects)

    # List the names of all objects defined.
    print ctx.object_defs.keys()

    # Returns all instances of MyClass and of its subclasses.
    print ctx.get_objects_by_type(MyClass)

    # Returns all instances of MyClass' subclasses only.
    print ctx.get_objects_by_type(MyClass, False)

    # Returns all integer objects.
    print ctx.get_objects_by_type(int)

The .object_defs dictionary stores instances of *springpython.config.ObjectDef*
class, these are the objects you need to inject into the container to later
successfully access them as if they were added prior to the application's start.
An *ObjectDef* allows one to specify the very same set of parameters an *@Object*
decorator does. The next examples shows how to insert two definitions into a
context, one will be a prototype - a new instance of *Foo*  will be created on
each request, the second one will be a singleton - only one instance of *Bar*
will ever be created and stored in a cache of singletons. This time the example
employs the Python's standard library *logging* module to better show in the
*DEBUG* mode what is going on under the hood::

    #
    # sample_context2.py
    #


    # Spring Python
    from springpython.config import PythonConfig

    class SampleContext2(PythonConfig):
        def __init__(self):
            super(SampleContext2, self).__init__()

::

    #
    # demo2.py
    #

    # stdlib
    import logging

    # Spring Python
    from springpython.config import Object, ObjectDef
    from springpython.context import ApplicationContext
    from springpython.factory import PythonObjectFactory
    from springpython.context.scope import SINGLETON, PROTOTYPE

    # Our sample code.
    from sample_context2 import SampleContext2

    # Configure logging.
    log_format = "%(msecs)d - %(levelname)s - %(name)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_format)

    class Foo(object):
        def run(self):
            return "Foo!"

    class Bar(object):
        def run(self):
            return "Bar!"

    # Create the context - part 1. in the logs.
    ctx = ApplicationContext(SampleContext2())

    # Definitions of objects that will be dynamically injected into container.

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
    foo_object_def = ObjectDef(id="foo", factory=PythonObjectFactory(foo, foo_wrapper), scope=PROTOTYPE, lazy_init=foo_wrapper.lazy_init)

    # A reference to the function wrapping the actual 'bar' function.
    bar_wrapper = foo.func_globals["_call_"]

    bar_object_def = ObjectDef(id="foo", factory=PythonObjectFactory(bar, bar_wrapper), scope=SINGLETON, lazy_init=bar_wrapper.lazy_init)

    ctx.object_defs["foo"] = foo_object_def
    ctx.object_defs["bar"] = bar_object_def

    # Access "foo" - part 2. in the logs.
    for x in range(3):
        foo_instance = ctx.get_object("foo")

    # Access "bar" - part 3. in the logs.
    for x in range(3):
        bar_instance = ctx.get_object("bar")

Here's how it shows in the logs. For clarity, the log has been divided into
three parts. Part 1. reads the object definitions from SampleContext2, as we
see, nothing has been read from it as it's still been empty at this point. After
adding definitions to the .object_defs dictionary, we're now at parts 2. and 3.
- in 2. the 'foo' object, a prototype one, is being created three times,
as expected. In part 3. the singleton 'bar' object is created and stored in
a singleton cache once only even though we're accessing it three times in our code.

::

    # Part 1.

    100 - DEBUG - springpython.config.PythonConfig - ==============================================================
    100 - DEBUG - springpython.config.PythonConfig - Parsing <sample_context2.SampleContext2 object at 0x17e70d0>
    101 - DEBUG - springpython.config.PythonConfig - ==============================================================
    101 - DEBUG - springpython.container.ObjectContainer - === Done reading object definitions. ===

    # Part 2.

    102 - DEBUG - springpython.context.ApplicationContext - Did NOT find object 'foo' in the singleton storage.
    102 - DEBUG - springpython.context.ApplicationContext - Creating an instance of id=foo props=[] scope=scope.PROTOTYPE factory=PythonObjectFactory(<function foo at 0x184c2a8>)
    102 - DEBUG - springpython.factory.PythonObjectFactory - Creating an instance of foo
    102 - DEBUG - springpython.config.objectPrototype<function foo at 0x7f6d15db0a28> - ()scope.PROTOTYPE - This IS the top-level object, calling foo().
    102 - DEBUG - springpython.config.objectPrototype<function foo at 0x7f6d15db0a28> - ()scope.PROTOTYPE - Found <__main__.Foo object at 0x184b650>

    102 - DEBUG - springpython.context.ApplicationContext - Did NOT find object 'foo' in the singleton storage.
    102 - DEBUG - springpython.context.ApplicationContext - Creating an instance of id=foo props=[] scope=scope.PROTOTYPE factory=PythonObjectFactory(<function foo at 0x184c2a8>)
    102 - DEBUG - springpython.factory.PythonObjectFactory - Creating an instance of foo
    103 - DEBUG - springpython.config.objectPrototype<function foo at 0x7f6d15db0a28> - ()scope.PROTOTYPE - This IS the top-level object, calling foo().
    103 - DEBUG - springpython.config.objectPrototype<function foo at 0x7f6d15db0a28> - ()scope.PROTOTYPE - Found <__main__.Foo object at 0x184b690>

    103 - DEBUG - springpython.context.ApplicationContext - Did NOT find object 'foo' in the singleton storage.
    103 - DEBUG - springpython.context.ApplicationContext - Creating an instance of id=foo props=[] scope=scope.PROTOTYPE factory=PythonObjectFactory(<function foo at 0x184c2a8>)
    103 - DEBUG - springpython.factory.PythonObjectFactory - Creating an instance of foo
    103 - DEBUG - springpython.config.objectPrototype<function foo at 0x7f6d15db0a28> - ()scope.PROTOTYPE - This IS the top-level object, calling foo().
    103 - DEBUG - springpython.config.objectPrototype<function foo at 0x7f6d15db0a28> - ()scope.PROTOTYPE - Found <__main__.Foo object at 0x184b650>

    # Part 3.

    103 - DEBUG - springpython.context.ApplicationContext - Did NOT find object 'bar' in the singleton storage.
    103 - DEBUG - springpython.context.ApplicationContext - Creating an instance of id=foo props=[] scope=scope.SINGLETON factory=PythonObjectFactory(<function bar at 0x184c578>)
    103 - DEBUG - springpython.factory.PythonObjectFactory - Creating an instance of bar
    104 - DEBUG - springpython.config.objectSingleton<function bar at 0x17e5aa0> - ()scope.SINGLETON - This IS the top-level object, calling bar().
    104 - DEBUG - springpython.config.objectSingleton<function bar at 0x17e5aa0> - ()scope.SINGLETON - Found <__main__.Bar object at 0x184b690>
    104 - DEBUG - springpython.context.ApplicationContext - Stored object 'bar' in container's singleton storage

Please note that what has been shown above applies to runtime only, adding object
definitions to the container doesn't mean the changes will be in any way
serialized to the file system, they are transient and will be lost when the
application will be shutting down. Another thing to keep in mind is that you'll
be modifying a raw Python dictionary and if your application is multi-threaded,
you'll have to serialize the access from concurrent threads yourself.