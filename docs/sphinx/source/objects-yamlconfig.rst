YamlConfig - Spring Python's YAML format
========================================

.. highlight:: yaml

*YamlConfig* is a class that scans object definitions stored in a
`YAML 1.1 <http://www.yaml.org/>`_ format using the `PyYAML <http://pyyaml.org/>`_
project.

The following is a simple definition of objects, including scope and lazy-init.
Later sections will show other options you have for wiring things together::

    objects:
        - object: MovieLister
          class: springpythontest.support.testSupportClasses.MovieLister
          scope: prototype
          properties:
              finder: {ref: MovieFinder}
              description: {ref: SingletonString}

        - object: MovieFinder
          class: springpythontest.support.testSupportClasses.ColonMovieFinder
          scope: singleton
          lazy-init: True
          properties:
              filename: support/movies1.txt

        - object: SingletonString
          class: springpythontest.support.testSupportClasses.StringHolder
          lazy-init: True
          properties:
              str: There should only be one copy of this string

.. highlight:: python

The definitions stored in this file are fed to an *YamlConfig* instance which
scans it, and then sends the meta-data to the *ApplicationContext*. Then, when
the application code requests an object named *MovieLister* from the container,
the container utilizes an object factory to create the object and return it::

    from springpython.context import ApplicationContext
    from springpython.config import YamlConfig

    container = ApplicationContext(YamlConfig("app-context.yml"))
    service = container.get_object("MovieLister")

.. _objects-yamlconfig-referenced-objects:

Referenced Objects
------------------

A referenced object is where an object is needed, but instead of providing
the definition right there, there is, instead, a name, referring to another
object definition.

Object definitions can refer to other objects in many places including:
properties, constructor arguments, and objects embedded inside various
:ref:`collections <objects-yamlconfig-collections>`. This is the way to break things down into smaller pieces.
It also allows you more efficiently use memory and guarantee different objects
are linked to the same backend object.

.. highlight:: yaml

The following fragment, pulled from the earlier example, shows two different
properties referencing other objects. It demonstrates the two ways to refer
to another object::

    object: MovieLister
    class: springpythontest.support.testSupportClasses.MovieLister
    scope: prototype
    properties:
        finder: {ref: MovieFinder}
        description: {ref: SingletonString}

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

Inner Objects
-------------

Inner objects are objects defined inside another structure, and not at the
root level of the YAML document. The following shows an alternative
configuration of a *MovieLister* where the finder uses a *named inner object*::

    object: MovieLister3
    class: springpythontest.support.testSupportClasses.MovieLister
    properties:
        finder:
            object: named
            class: springpythontest.support.testSupportClasses.ColonMovieFinder
            properties:
                filename: support/movies1.txt
        description: {ref: SingletonString}

The *ColonMovieFinder* is indeed an inner object because it was defined inside
the *MovieLister3* object. Objects defined at the top level have a container-level
name that matches their id value. In this case, asking the container for a copy
of *MovieLister3* will yield the top level object. However, named objects develop
a path-like name based on where they are located. In this case, the inner
*ColonMovieFinder* object will have a container-level name of *MovieLister3.finder.named*.

Typically, neither your code nor other object definitions will have any need
to reference *MovieLister3.finder.named*, but there may be cases where you need
this. The value of the object key of *ColonMovieFinder* can be left out (it is
optional for inner objects) like this::

    object: MovieLister2
    class: springpythontest.support.testSupportClasses.MovieLister
    properties:
        finder:
            object:
            class: springpythontest.support.testSupportClasses.ColonMovieFinder
            properties:
                filename: support/movies1.txt
        description: {ref: SingletonString}

That is slightly more compact, and usually alright because you usually wouldn't
access this object from anywhere. However, if you must, the name in this case
is *MovieLister2.finder.<anonymous>* indicating an anonymous object.

It is important to realize that inner objects have all the same privileges
as top-level objects, meaning that they can also utilize
:ref:`reference objects <objects-yamlconfig-referenced-objects>`,
:ref:`collections <objects-yamlconfig-collections>`, and inner objects themselves.

.. _objects-yamlconfig-collections:

Collections
-----------

Spring Java supports many types of collections, including lists, sets, frozen
sets, maps, tuples, and java-style properties. Spring Python supports these as
well. The following configuration shows usage of *dict*, *list*, *set*, *frozenset*,
and *tuple*::

    object: ValueHolder
    class: springpythontest.support.testSupportClasses.ValueHolder
    constructor-args:
        - {ref: SingletonString}
    properties:
        some_dict:
              Hello: World
              Spring: Python
              holder: {ref: SingletonString}
              another copy: {ref: SingletonString}
        some_list:
            - Hello, world!
            - ref: SingletonString
            - Spring Python
        some_props:
            administrator: administrator@example.org
            support: support@example.org
            development: development@example.org
        some_set:
            set:
                - Hello, world!
                - ref: SingletonString
                - Spring Python
        some_frozen_set:
            frozenset:
                - Hello, world!
                - ref: SingletonString
                - Spring Python
        some_tuple:
            tuple:
                - Hello, world!
                - ref: SingletonString
                - Spring Python

* some_dict is a Python dictionary with four entries.
* some_list is a Python list with three entries.
* some_props is also a Python dictionary, containing three values.
* some_set is an instance of Python's `mutable set <http://docs.python.org/library/collections.html?highlight=mutableset#abcs-abstract-base-classes>`_.
* some_frozen_set is an instance of Python's `frozen set <http://docs.python.org/library/stdtypes.html?#frozenset>`_.
* some_tuple is a Python tuple with three values.

.. note::

    Java uses maps, Python uses dictionaries

    While Java calls key-based structures maps, Python calls them dictionaries.
    For this reason, the code fragment shows a "dict" entry, which is
    one-to-one with Spring Java's "map" definition.

    Java also has a *Property* class. Since YAML already supports a key/value
    structure as-is, *YamlConfig* does not have a separate structural definition.

Support for Python builtin types and mappings of other types onto YAML syntax
-----------------------------------------------------------------------------

Objects of commonly used Python builtin types may be tersely expressed in
YamlConfig. Supported types are *str*, *unicode*, *int*, *long*, *float*,
*decimal.Decimal*, *bool*, *complex*, *dict*, *list* and *tuple*.

Here's a sample YamlConfig featuring their usage. Note that with the exception
of *decimal.Decimal*, names of the YAML attributes are the same as the names of
Python types::

    objects:
        - object:  MyString
          str: My string

        - object:  MyUnicode
          unicode: Zażółć gęślą jaźń

        - object:  MyInt
          int: 10

        - object:  MyLong
          long: 100000000000000000000000

        - object:  MyFloat
          float: 3.14

        - object:  MyDecimal
          decimal: 12.34

        - object:  MyBoolean
          bool: False

        - object:  MyComplex
          complex: 10+0j

        - object:  MyList
          list: [1, 2, 3, 4]

        - object:  MyTuple
          tuple: ["a", "b", "c"]

        - object: MyDict
          dict:
            1: "a"
            2: "b"
            3: "c"

        - object: MyRef
          decimal:
            ref: MyDecimal

Under the hood, while parsing the YAML files, Spring Python will translate
the definitions such as the one above into the following one::

    objects:
        - object:  MyString
          class: types.StringType
          constructor-args: ["My string"]

        - object:  MyUnicode
          class: types.UnicodeType
          constructor-args: ["Zażółć gęślą jaźń"]

        - object:  MyInt
          class: types.IntType
          constructor-args: [10]

        - object:  MyLong
          class: types.LongType
          constructor-args: [100000000000000000000000]

        - object:  MyFloat
          class: types.FloatType
          constructor-args: [3.14]

        - object:  MyDecimal
          class: decimal.Decimal
          constructor-args: ["12.34"]

        - object: MyBoolean
          class: types.BooleanType
          constructor-args: [False]

        - object: MyComplex
          class: types.ComplexType
          constructor-args: [10+0j]

        - object: MyList
          class: types.ListType
          constructor-args: [[1,2,3,4]]

        - object: MyTuple
          class: types.TupleType
          constructor-args: [["a", "b", "c"]]

        - object: MyDict
          class: types.DictType
          constructor-args: [{1: "a", 2: "b", 3: "c"}]

        - object: MyRef
          class: decimal.Decimal
          constructor-args: [{ref: MyDecimal}]

Configuration of how YAML elements are mapped onto Python types is stored in
the *springpython.config.yaml_mappings* dictionary which can be easily
customized to fulfill one's needs. The dictionary's keys are names of the YAML
elements and its values are the coresponding Python types, written as strings
in the form of *"package_name.module_name.class_name"*  - note that the
*"package_name.module_name."* part is required, it needs to be a fully
qualified name.

.. highlight:: python

Let's assume that in your configuration you're frequently creating objects
of type *interest_rate.InterestRateFrequency*, here's how you can save yourself
a lot of typing by customizing the mappings dictionary. First, on Python side,
create an *InterestRate* class, such as::

    class InterestRate(object):
        def __init__(self, value=None):
            self.value = value

.. highlight:: yaml

which will allow you to create such a YAML context::

    objects:
        - object: base_interest_rate
          interest_rate: "7.35"

.. highlight:: python

then, before creating the context, update the mappings dictionary as needed
and next you'll be able to access the base_interest_rate  object as if it had
been defined using the standard syntax::

    from springpython.context import ApplicationContext
    from springpython.config import YamlConfig, yaml_mappings

    yaml_mappings.update({"interest_rate": "interest_rate.InterestRate"})

    # .. create the context now
    container = ApplicationContext(YamlConfig("./app-ctx.yaml"))

    # .. fetch the object
    base_interest_rate = container.get_object("base_interest_rate")

    # .. will show "7.35", as defined in the "./app-ctx.yaml" config
    print base_interest_rate.value


Constructors
------------

.. highlight:: yaml

Python functions can have both positional and named arguments. Positional
arguments get assembled into a tuple, and named arguments are assembled into
a dictionary, before being passed to a function call. Spring Python takes
advantage of that option when it comes to constructor calls. The following
block of configuration data shows defining positional constructors::

    object: AnotherSingletonString
    class: springpythontest.support.testSupportClasses.StringHolder
    constructor-args:
        - position 1's constructor value

Spring Python will read these and then feed them to the class constructor in
the same order as shown here.

The following code configuration shows named constructor arguments. Spring
Python converts these into keyword arguments, meaning it doesn't matter what
order they are defined::

    object: MultiValueHolder
    class: springpythontest.support.testSupportClasses.MultiValueHolder
    constructor-args:
        a: alt a
        b: alt b

This was copied from the code's test suite, where a test case is used to prove
that order doesn't matter. It is important to note that positional constructor
arguments are fed before named constructors, and that overriding a the same
constructor parameter both by position and by name is not allowed by Python,
and will in turn, generate a run-time error.

It is also valuable to know that you can mix this up and use both.

Object definition inheritance
-----------------------------

Just like XMLConfig, YamlConfig allows for wiring the objects definitions into
hierarchies of abstract and children objects, thus this section is in most
parts a repetition of what's documented :ref:`here <objects-xmlconfig-inheritance>`.

Definitions may be stacked up into hierarchies of abstract parents and their
children objects. A child object not only inherits all the properties and
constructor arguments from its parent but it can also easily override any
of the inherited values. This can save a lot of typing when configuring
non-trivial application contexts which would otherwise need to repeat the
same configuration properties over many objects definitions.

An abstract object is identified by having an *abstract* attribute equal to
True and the child ones are those which have a *parent* attribute set to ID
of an object from which the properties or constructor arguments should be
inherited. Child objects must not specify the *class* attribute, its value
is taken from their parents.

An object may be both a child and an abstract one.

Here's a hypothetical configuration of a set of services exposed by a server.
Note how you can easily change the CRM environment you're invoking by merely
changing the concrete service's (get_customer_id or get_customer_profile)
parent ID::

    objects:
        - object: service
          class: springpythontest.support.testSupportClasses.Service
          abstract: True
          scope: singleton
          lazy-init: True
          properties:
            ip: 192.168.1.153

        - object: crm_service_dev
          abstract: True
          parent: service
          properties:
            port: "3392"

        - object: crm_service_test
          abstract: True
          parent: service
          properties:
            port: "3393"

        - object: get_customer_id
          parent: crm_service_dev
          properties:
            path: /soap/invoke/get_customer_id

        - object: get_customer_profile
          parent: crm_service_test
          properties:
            path: /soap/invoke/get_customer_profile

Here's how you can override inherited properties; both get_customer_id and
get_customer_profile object definitions will inherit the path property however
the actual objects returned by the container will use local, overridden,
values of the property::

    objects:
        - object: service
          class: foo.Service
          abstract: True
          scope: singleton
          lazy-init: True
          properties:
            ip: 192.168.1.153
            port: "3392"
            path: /DOES-NOT-EXIST

        - object: get_customer_id
          parent: service
          properties:
            path: /soap/invoke/get_customer_id

        - object: get_customer_profile
          parent: service
          properties:
            path: /soap/invoke/get_customer_profile
