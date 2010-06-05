The IoC container
=================

Inversion Of Control (IoC), also known as
`dependency injection <http://en.wikipedia.org/wiki/Dependency_injection>`_
is more of an architectural concept than a simple coding pattern.

The idea is to decouple classes that depend on each other from inheriting other
dependencies, and instead link them only at the interfacing level. This requires
some sort of 3rd party software module to instantiate the concrete objects
and "inject" them into the class that needs to call them.

In Spring, there are certain classes whose instances form the backbone of your
application and that are managed by the Spring IoC container. While Spring
Java calls them beans, Spring Python and Spring for .NET call them *objects*.
An object is simply a class instance that was instantiated, assembled and
otherwise managed by a Spring IoC container instead of directly by your code;
other than that, there is nothing special about a object. It is in all other
respects one of probably many objects in your application. These objects, and
the dependencies between them, are reflected in the configuration meta-data
used by a container.

.. note::

    In early 2004, Martin Fowler asked the readers of his site: when talking
    about Inversion of Control: *"the question is, what aspect of control are
    [they] inverting?"*. Fowler then suggested renaming the principle (or at
    least giving it a more self-explanatory name), and started to use the term
    *Dependency Injection*. His article then continued to explain the ideas
    underpinning the Inversion of Control (IoC) and Dependency Injection
    (DI) principle.

    If you need a decent insight into IoC and DI, please do refer to said
    article : http://martinfowler.com/articles/injection.html.

The following diagram demonstrates a key Spring concept: building useful
services on top of simple objects, configured through a container's set
of blueprints, provides powerful services that are easier to maintain.

.. image:: gfx/spring_triangle.png

External dependencies
+++++++++++++++++++++

XML-based IoC configuration formats use ElementTree which is a part of Python's
stantard library in Python 2.5 and newer. If you use Python 2.4 you can
download ElementTree from here. YamlConfig requires installation of PyYAML
which may be found `here <http://pypi.python.org/pypi/elementtree>`_.
No additional dependencies needs be installed if you choose PythonConfig.

Container
+++++++++

A container is an object you create in your code that receives the definitions
for objects from various sources. Your code goes to the container to request
the object, and the container then does everything it needs to create an instance of that.

Depending on the scope of the object definition, the container may create
a new instance right there on the spot, or it may fetch a reference to a
singleton instance that was created previously. If this is the first time
a singleton-scoped object is requested, is created, stored, and then returned
to you. For a prototype-scoped object, EVERY TIME you request an object, a
new instance is created and NOT stored in the singleton cache.

Containers depend on various object factories to do the heavy lifting of
construction, and then itself will set any additional properties. There is
also the possibility of additional behavior outside of object creation, which
can be defined by extending the *ObjectContainer* class.

The reason it is called a container is the idea that you are going to a
central place to get your top level object. While it is also possible to
get all your other objects, the core concept of
`dependency injection <http://en.wikipedia.org/wiki/Dependency_injection>`_ is
that below your top-most object, all the other dependencies have been injected
and thus not require container access. That is what we mean when we say most
of your code does NOT have to be Spring Python-aware.

.. note::

    Pay special note that there is no fixed requirement that a container
    actually be in a certain location. While the current solution is memory
    based, meaning your objects will be lost when your application shuts down,
    there is always the possibility of implementing some type of distributed,
    persistent object container. For example, it is within the realm of
    possibilities to implement a container that utilizes a back-end database
    to "contain" things or utilizes some distributed memory cache spread between nodes.

ObjectContainer vs. ApplicationContext
--------------------------------------

The name of the container is *ObjectContainer*. Its job is to pull in object
meta-data from various sources, and then call on related object factories to
create the objects. In fact, this container is capable of receiving object
definitions from multiple sources, each of differing types such as XML, YAML,
Python code, and other future formats.

The following block of code shows an example of creating an object container,
and then pulling an object out of the container.::

    # TODO: Use YUI here

    from springpython.context import ApplicationContext
    from springpython.config import XMLConfig

    container = ApplicationContext(XMLConfig("app-context.xml"))
    service = container.get_object("sampleService")

The first thing you may notice is the fact that *ApplicationContext* was used
instead of *ObjectContainer*. *ApplicationContext* is a subclass of *ObjectContainer*,
and is typically used because it also performs additional pre- and post-creational
logic.

For example, any object that implements *ApplicationContextAware* will have an
additional app_context attribute added, populated with a copy of the
*ApplicationContext*. If your object's class extends *ObjectPostProcessor* and
defines a *post_process_after_initialization*, the ApplicationContext will run
that method against every instance of that object.

If your singleton objects hold references to some external resources, e.g.
connections to a resource manager of some sort, you may also want to subclass
*springpython.context.DisposableObject* to have a means for the resources to get
released. Any singleton subclassing *DisposableObject* may
define a destroy method which is guaranteed to be executed on *ApplicationContext*
shutdown. An alternative to creating a destroy method is to define the
*destroy_method* attribute of an object which should be a name of the custom
method to be invoked on *ApplicationContext* shutdown. If an object defines
both destroy and destroy_method then the former will take precedence. It is
an error to extend *DisposableObject* without providing
either destory or destroy_method. If this occurs, an error will be written
to Spring Python logs when the container shuts down.

Scope of Objects / Lazy Initialization
--------------------------------------

Another key duty of the container is to also manage the scope of objects.
This means at what time that objects are created, where the instances are
stored, how long before they are destroyed, and whether or not to create them
when the container is first started up.

Currently, two scopes are supported: SINGLETON and PROTOTYPE. A singleton-scoped
object is cached in the container until application shutdown. A prototype-scoped
object is never stored, thus requiring the object factory to create a new
instance every time the object is requested from the container.

The default policy for the container is to make everything SINGLETON and also
eagerly fetch all objects when the container is first created. The scope for
each object can be individually overriden. Also, the initialization of each
object can be shifted to "lazy", whereby the object is not created until the
first time it is fetched or referenced by another object.


Configuration
-------------

Spring Python supports different formats for defining objects.

In the spirit of `Spring JavaConfig <http://www.springsource.org/javaconfig>`_
and `a blog posting <http://blog.springsource.com/2006/11/28/a-java-configuration-option-for-spring/>`_
by Rod Johnson, the :doc:`PythonConfig <objects-pythonconfig>` format has been defined. By extending
:doc:`PythonConfig <objects-pythonconfig>` and using
the @Object Python decorator, objects may be defined with pure Python code in a centralized class.

:doc:`XMLConfig <objects-xmlconfig>`
(:download:`see the XSD spec <xsd/spring-python-context-1.1.xsd>`) closely models
the original Spring Java version. It has support for
:ref:`referenced objects <objects-xmlconfig-referenced-objects>`,
:ref:`inner objects <objects-xmlconfig-inner-objects>`,
various :ref:`collections <objects-xmlconfig-collections>`
(lists, sets, frozen sets, tuples, dictionaries, and Java-style props), and values.

Spring Python also has a YAML-based parser called :doc:`YamlConfig <objects-yamlconfig>`.

Spring Python is ultimately about choice, which is why developers may extend
the *springpython.config.Config* class to define their own object definition scanner. By plugging
an instance of their scanner into *ApplicationContext*, definitions can result
in instantiated objects.

.. note::

    This project
    first began using the format defined by PyContainer, *a now inactive project*.
    The structure has been  :download:`captured into an XSD spec <xsd/spring-python-pycontainer-context-1.0.xsd>`.
    This format is primarily to support legacy apps that have already been built with Spring Python from
    its inception. There is no current priority to extend this format any further.
    Any new schema developments will be happening with XMLConfig  and YamlConfig.

You may be wondering, amidst all these choices, which one to pick? Here are
some suggestions based on your current solution space:

    * New projects are encouraged to pick either :doc:`PythonConfig <objects-pythonconfig>`,
      :doc:`XMLConfig <objects-xmlconfig>`, or :doc:`YamlConfig <objects-yamlconfig>`,
      based on your preference for pure Python code, XML, or YAML.

    * Projects migrating from Spring Java can use
      :ref:`objects-other-formats-springjavaconfig`
      to ease transition, with a long term goal of migrating to *XMLConfig*, and perhaps
      finally *PythonConfig*.

    * Apps already developed with Spring Python can use
      :ref:`PyContainerConfig <objects-other-formats-pycontainerconfig>` to keep
      running, but it is highly suggested you work towards *XMLConfig*.

    * Projects currently using *XMLConfig* should be pretty easy to migrate to
      *PythonConfig*, since it is basically a one-to-one translation. The pure Python
      configuration may turn out much more compact, especially if you are using
      lists, sets, dictionaries, and props.

    * It should also be relatively easy to migrate an *XMLConfig*-based configuration
      to *YamlConfig*. YAML tends to be more compact than XML, and some prefer not
      having to deal with the angle-bracket tax.

.. toctree::

    objects-xmlconfig.rst
    objects-yamlconfig.rst
    objects-pythonconfig.rst
    objects-other-formats.rst
    objects-more.rst