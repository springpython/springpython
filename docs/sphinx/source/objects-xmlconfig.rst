XMLConfig - Spring Python's native XML format
=============================================

.. highlight:: xml

*XMLConfig* is a class that scans object definitions stored in the XML
format defined for Spring Python. It looks very similar to Spring Java's 2.5
XSD spec, with some small changes.

The following is a simple definition of objects. Later sections will show other
options you have for wiring things together.::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                   http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="MovieLister" class="springpythontest.support.testSupportClasses.MovieLister" scope="prototype">
            <property name="finder" ref="MovieFinder"/>
            <property name="description"><ref object="SingletonString"/></property>
        </object>

        <object id="MovieFinder" class="springpythontest.support.testSupportClasses.ColonMovieFinder" scope="singleton">
            <property name="filename"><value>support/movies1.txt</value></property>
        </object>

        <object id="SingletonString" class="springpythontest.support.testSupportClasses.StringHolder" lazy-init="True">
            <property name="str" value="There should only be one copy of this string"></property>
        </object>
    </objects>

.. highlight:: python

The definitions stored in this file are fed to an *XMLConfig* instance which
scans it, and then sends the meta-data to the *ApplicationContext*. Then, when
the application code requests an object named MovieLister from the container,
the container utilizes an object factory to create the object and return it::

    from springpython.context import ApplicationContext
    from springpython.config import XMLConfig

    container = ApplicationContext(XMLConfig("app-context.xml"))
    service = container.get_object("MovieLister")

.. _objects-xmlconfig-referenced-objects:

Referenced Objects
------------------

A referenced object is where an object is needed, but instead of providing the
definition right there, there is, instead, a name, referring to another object
definition.

Object definitions can refer to other objects in many places including:
properties, constructor arguments, and objects embedded inside various
collections. This is the way to break things down into smaller pieces. It
also allows you more efficiently use memory and guarantee different objects
are linked to the same backend object.

.. highlight:: xml

The following fragment, pulled from the earlier example, shows two different
properties referencing other objects. It demonstrates the two ways to refer
to another object::

    <object id="MovieLister" class="springpythontest.support.testSupportClasses.MovieLister" scope="prototype">
        <property name="finder" ref="MovieFinder"/>
        <property name="description"><ref object="SingletonString"/></property>
    </object>

This means that instead of defining the object meant to be injected into the
*description* property right there, the container must look elsewhere amongst
its collection of object definitions for an object named *SingletonString*.

.. note::

    * **Referenced objects don't have to be in same configuration**

      When a referenced object is encountered, finding its definition is
      referred back to the container. This means ANY of the input sources
      provided to the container can hold this definition, REGARDLESS of format.

    * **Spring Python ONLY supports global references**

      While Spring Java has different levels of reference like parent, local,
      and global, Spring Python only supports global at this time.

In the following subsections, other types of object definitions are given.
Each will also include information about embedding reference objects.

.. _objects-xmlconfig-inner-objects:

Inner Objects
-------------

Inner objects are objects defined inside another structure, and not at the root
level of the XML document. The following shows an alternative configuration of
a *MovieLister*  where the *finder* uses a *named inner object*::

    <object id="MovieLister3" class="springpythontest.support.testSupportClasses.MovieLister">
        <property name="finder">
            <object id="named" class="springpythontest.support.testSupportClasses.ColonMovieFinder">
                <property name="filename"><value>support/movies1.txt</value></property>
            </object>
        </property>
        <property name="description"><ref object="SingletonString"/></property>
    </object>

The *ColonMovieFinder* is indeed an inner object because it was defined inside
the *MovieLister3* object. Objects defined at the top level have a container-level
name that matches their *id* value. In this case, asking the container for a copy
of *MovieLister3* will yield the top level object. However, named objects develop
a path-like name based on where they are located. In this case, the inner
*ColonMovieFinder* object will have a container-level name of
*MovieLister3.finder.named*.

Typically, neither your code nor other object definitions will have any need
to reference *MovieLister3.finder.named*, but there may be cases where you need
this. The *id* attribute of ColonMovieFinder can be left out (it is optional
for inner objects) like this::

    <object id="MovieLister2" class="springpythontest.support.testSupportClasses.MovieLister">
        <property name="finder">
            <object class="springpythontest.support.testSupportClasses.ColonMovieFinder">
                <property name="filename"><value>support/movies1.txt</value></property>
            </object>
        </property>
        <property name="description"><ref object="SingletonString"/></property>
    </object>

That is slightly more compact, and usually alright because you usually wouldn't
access this object from anywhere. However, if you must, the name in this case
is *MovieLister2.finder.<anonymous>* indicating an anonymous object.

It is important to realize that inner objects have all the same privileges as
top-level objects, meaning that they can also utilize
:ref:`reference objects <objects-xmlconfig-referenced-objects>`,
:ref:`collections <objects-xmlconfig-collections>`, and inner objects themselves.

.. _objects-xmlconfig-collections:

Collections
-----------

Spring Java supports many types of collections, including lists, sets, frozen
sets, maps, tuples, and Java-style properties. Spring Python supports these
as well. The following configuration shows usage of *dict*, *list*, *props*, *set*,
*frozenset*, and *tuple*::

    <object id="ValueHolder" class="springpythontest.support.testSupportClasses.ValueHolder">
        <constructor-arg><ref object="SingletonString"/></constructor-arg>
        <property name="some_dict">
            <dict>
                <entry><key><value>Hello</value></key><value>World</value></entry>
                <entry><key><value>Spring</value></key><value>Python</value></entry>
                <entry><key><value>holder</value></key><ref object="SingletonString"/></entry>
                <entry><key><value>another copy</value></key><ref object="SingletonString"/></entry>
            </dict>
        </property>
        <property name="some_list">
            <list>
                <value>Hello, world!</value>
                <ref object="SingletonString"/>
                <value>Spring Python</value>
            </list>
        </property>
        <property name="some_props">
            <props>
                <prop key="administrator">administrator@example.org</prop>
                <prop key="support">support@example.org</prop>
                <prop key="development">development@example.org</prop>
            </props>
        </property>
        <property name="some_set">
            <set>
                <value>Hello, world!</value>
                <ref object="SingletonString"/>
                <value>Spring Python</value>
            </set>
        </property>
        <property name="some_frozen_set">
            <frozenset>
                <value>Hello, world!</value>
                <ref object="SingletonString"/>
                <value>Spring Python</value>
            </frozenset>
        </property>
        <property name="some_tuple">
            <tuple>
                <value>Hello, world!</value>
                <ref object="SingletonString"/>
                <value>Spring Python</value>
            </tuple>
        </property>
    </object>

* some_dict is a Python dictionary with four entries.
* some_list is a Python list with three entries.
* some_props is also a Python dictionary, containing three values.
* some_set is an instance of Python's `mutable set <http://docs.python.org/library/collections.html?highlight=mutableset#abcs-abstract-base-classes>`_.
* some_frozen_set is an instance of Python's `frozen set <http://docs.python.org/library/stdtypes.html?#frozenset>`_.
* some_tuple is a Python tuple with three values.

.. note::

    Java uses maps, Python uses dictionaries

    While java calls key-based structures maps, Python calls them dictionaries.
    For this reason, the code fragment shows a "dict" entry, which is
    one-to-one with Spring Java's "map" definition.

    Java also has a *Property* class. Spring Python translates this into a Python
    dictionary, making it more like an alternative to the configuring mechanism
    of dict.

.. _objects-xmlconfig-constructors:

Constructors
------------

Python functions can have both positional and named arguments. Positional
arguments get assembled into a tuple, and named arguments are assembled into
a dictionary, before being passed to a function call. Spring Python takes
advantage of that option when it comes to constructor calls. The following
block of configuration data shows defining positional constructors::

    <object id="AnotherSingletonString" class="springpythontest.support.testSupportClasses.StringHolder">
        <constructor-arg value="attributed value"/>
    </object>

    <object id="AThirdSingletonString" class="springpythontest.support.testSupportClasses.StringHolder">
        <constructor-arg><value>elemental value</value></constructor-arg>
    </object>

Spring Python will read these and then feed them to the class constructor in
the same order as shown here.

The following code configuration shows named constructor arguments. Spring
Python converts these into keyword arguments, meaning it doesn't matter what
order they are defined::

    <object id="MultiValueHolder" class="springpythontest.support.testSupportClasses.MultiValueHolder">
        <constructor-arg name="a"><value>alt a</value></constructor-arg>
        <constructor-arg name="b"><value>alt b</value></constructor-arg>
    </object>

    <object id="MultiValueHolder2" class="springpythontest.support.testSupportClasses.MultiValueHolder">
        <constructor-arg name="c"><value>alt c</value></constructor-arg>
        <constructor-arg name="b"><value>alt b</value></constructor-arg>
    </object>

This was copied from the code's test suite, where a test case is used to prove
that order doesn't matter. It is important to note that positional constructor
arguments are fed before named constructors, and that overriding a the same
constructor parameter both by position and by name is not allowed by Python,
and will in turn, generate a run-time error.

It is also valuable to know that you can mix this up and use both.

Values
------

For those of you that used Spring Python before XMLConfig, you may have noticed
that expressing values isn't as succinct as the old format. A good example of
the old :ref:`PyContainer <objects-other-formats-pycontainerconfig>` format would be::

    <component id="user_details_service" class="springpython.security.userdetails.InMemoryUserDetailsService">
        <property name="user_dict">
            {
                "basichiblueuser"  : ("password1", ["ROLE_BASIC", "ASSIGNED_BLUE",   "LEVEL_HI"], True),
                "basichiorangeuser": ("password2", ["ROLE_BASIC", "ASSIGNED_ORANGE", "LEVEL_HI"], True),
                "otherhiblueuser"  : ("password3", ["ROLE_OTHER", "ASSIGNED_BLUE",   "LEVEL_HI"], True),
                "otherhiorangeuser": ("password4", ["ROLE_OTHER", "ASSIGNED_ORANGE", "LEVEL_HI"], True),
                "basicloblueuser"  : ("password5", ["ROLE_BASIC", "ASSIGNED_BLUE",   "LEVEL_LO"], True),
                "basicloorangeuser": ("password6", ["ROLE_BASIC", "ASSIGNED_ORANGE", "LEVEL_LO"], True),
                "otherloblueuser"  : ("password7", ["ROLE_OTHER", "ASSIGNED_BLUE",   "LEVEL_LO"], True),
                "otherloorangeuser": ("password8", ["ROLE_OTHER", "ASSIGNED_ORANGE", "LEVEL_LO"], True)
            }
        </property>
    </component>

.. note::

    Why do I see components and not objects?

    In the beginning, PyContainer was used and it tagged the managed instances
    as components. After replacing PyContainer with a more sophisticated IoC
    container, the instances are now referred to as objects, however, to
    maintain this legacy format, you will see component tags inside
    *PyContainerConfig*-based definitions.

While this is very succinct for expressing definitions using as much Python
as possible, that format makes it very hard to embed referenced objects and
inner objects, since PyContainerConfig uses Python's
`eval <http://docs.python.org/library/functions.html#eval>`_ method to convert
the material.

The following configuration block shows how to configure the same thing for
XMLConfig::

    <object id="user_details_service" class="springpython.security.userdetails.InMemoryUserDetailsService">
        <property name="user_dict">
            <dict>
                <entry>
                    <key><value>basichiblueuser</value></key>
                    <value><tuple>
                        <value>password1</value>
                        <list><value>ROLE_BASIC</value><value>ASSIGNED_BLUE</value><value>LEVEL_HI</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
                <entry>
                    <key><value>basichiorangeuser</value></key>
                    <value><tuple>
                        <value>password2</value>
                        <list><value>ROLE_BASIC</value><value>ASSIGNED_ORANGE</value><value>LEVEL_HI</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
                <entry>
                    <key><value>otherhiblueuser</value></key>
                    <value><tuple>
                        <value>password3</value>
                        <list><value>ROLE_OTHER</value><value>ASSIGNED_BLUE</value><value>LEVEL_HI</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
                <entry>
                    <key><value>otherhiorangeuser</value></key>
                    <value><tuple>
                        <value>password4</value>
                        <list><value>ROLE_OTHER</value><value>ASSIGNED_ORANGE</value><value>LEVEL_HI</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
                <entry>
                    <key><value>basicloblueuser</value></key>
                    <value><tuple>
                        <value>password5</value>
                        <list><value>ROLE_BASIC</value><value>ASSIGNED_BLUE</value><value>LEVEL_LO</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
                <entry>
                    <key><value>basicloorangeuser</value></key>
                    <value><tuple>
                        <value>password6</value>
                        <list><value>ROLE_BASIC</value><value>ASSIGNED_ORANGE</value><value>LEVEL_LO</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
                <entry>
                    <key><value>otherloblueuser</value></key>
                    <value><tuple>
                        <value>password7</value>
                        <list><value>ROLE_OTHER</value><value>ASSIGNED_BLUE</value><value>LEVEL_LO</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
                <entry>
                    <key><value>otherloorangeuser</value></key>
                    <value><tuple>
                        <value>password8</value>
                        <list><value>ROLE_OTHER</value><value>ASSIGNED_ORANGE</value><value>LEVEL_LO</value></list>
                        <value>True</value>
                    </tuple></value>
                </entry>
            </dict>
        </property>
    </object>

Of course this is more verbose than the previous block. However, it opens the
door to having a much higher level of detail::

    <object id="user_details_service2" class="springpython.security.userdetails.InMemoryUserDetailsService">
        <property name="user_dict">
            <list>
                <value>Hello, world!</value>
                <dict>
                    <entry>
                        <key><value>yes</value></key>
                        <value>This is working</value>
                    </entry>
                    <entry>
                        <key><value>no</value></key>
                        <value>Maybe it's not?</value>
                    </entry>
                </dict>
                <tuple>
                    <value>Hello, from Spring Python!</value>
                    <value>Spring Python</value>
                    <dict>
                        <entry>
                            <key><value>yes</value></key>
                            <value>This is working</value>
                        </entry>
                        <entry>
                            <key><value>no</value></key>
                            <value>Maybe it's not?</value>
                        </entry>
                    </dict>
                    <list>
                        <value>This is a list element inside a tuple.</value>
                        <value>And so is this :)</value>
                    </list>
                </tuple>
                <set>
                    <value>1</value>
                    <value>2</value>
                    <value>1</value>
                </set>
                <frozenset>
                    <value>a</value>
                    <value>b</value>
                    <value>a</value>
                </frozenset>
            </list>
        </property>
    </object>


XMLConfig and basic Python types
--------------------------------

Objects of most commonly used Python types - *str*, *unicode*, *int*, *long*, *float*,
*decimal.Decimal*, *bool* and *complex*  - may be expressed in XMLConfig using a
shorthand syntax which allows for a following XMLConfig file::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <str id="MyString">My string</str>
        <unicode id="MyUnicode">Zażółć gęślą jaźń</unicode>
        <int id="MyInt">10</int>
        <long id="MyLong">100000000000000000000000</long>
        <float id="MyFloat">3.14</float>
        <decimal id="MyDecimal">12.34</decimal>
        <bool id="MyBool">False</bool>
        <complex id="MyComplex">10+0j</complex>

    </objects>

_objects-xmlconfig-inheritance

Object definition inheritance
-----------------------------

XMLConfig's definitions may be stacked up into hierarchies of abstract parents
and their children objects. A child object not only inherits all the properties
and constructor arguments from its parent but it can also easily override any
of the inherited values. This can save a lot of typing when configuring
non-trivial application contexts which would otherwise need to repeat the
same configuration properties over many objects definitions.

An abstract object is identified by having an *abstract="True"* attribute and
the child ones are those which have a *parent* attribute set to ID of an object
from which the properties or constructor arguments should be inherited. Child
objects must not specify the *class* attribute, its value is taken from their
parents.

An object may be both a child and an abstract one.

Here's a hypothetical configuration of a set of services exposed by a server.
Note how you can easily change the CRM environment you're invoking by merely
changing the concrete service's (get_customer_id or get_customer_profile)
parent ID::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="service" class="springpythontest.support.testSupportClasses.Service" scope="singleton" abstract="True" lazy-init="True">
            <property name="ip"><value>192.168.1.153</value></property>
        </object>

        <object id="crm_service_dev" parent="service" abstract="True">
            <property name="port"><value>3392</value></property>
        </object>

        <object id="crm_service_test" parent="service" abstract="True">
            <property name="port"><value>3393</value></property>
        </object>

        <object id="get_customer_id" parent="crm_service_dev">
            <property name="path"><value>/soap/invoke/get_customer_id</value></property>
        </object>

        <object id="get_customer_profile" parent="crm_service_test">
            <property name="path"><value>/soap/invoke/get_customer_profile</value></property>
        </object>

    </objects>

Here's how you can override inherited properties; both get_customer_id and
get_customer_profile object definitions will inherit the path property however
the actual objects returned by the container will use local, overridden,
values of the property::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="service" class="springpythontest.support.testSupportClasses.Service" scope="singleton" abstract="True" lazy-init="True">
            <property name="ip"><value>192.168.1.153</value></property>
            <property name="port"><value>3392</value></property>
            <property name="path"><value>/DOES-NOT-EXIST</value></property>
        </object>

        <object id="get_customer_id" parent="service">
            <property name="path"><value>/soap/invoke/get_customer_id</value></property>
        </object>

        <object id="get_customer_profile" parent="service">
            <property name="path"><value>/soap/invoke/get_customer_profile</value></property>
        </object>

    </objects>

.. highlight:: python

If you need to get an abstract object from a container, use the .get_object's
*ignore_abstract* parameter, otherwise *springpython.container.AbstractObjectException*
will be raised. Observe the difference::

    # .. skip creating the context

    # No exception will be raised, even though 'service' is an abstract object
    service = ctx.get_object("service", ignore_abstract=True)

    # Will show the object
    print service

    # Will raise AbstractObjectException
    service = ctx.get_object("service")
