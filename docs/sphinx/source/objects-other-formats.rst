Other configuration formats
===========================

.. _objects-other-formats-pycontainerconfig:

PyContainerConfig - Spring Python's original XML format
-------------------------------------------------------

*PyContainerConfig* is a class that scans object definitions stored in the format
defined by PyContainer, which was the original XML format used by Spring Python to define objects.

.. warning::

    PyContainer's format is deprecated

    PyContainer's format and the original parser was useful for getting this
    project started. However, it has shown its age by not being easy to revise
    nor extend. So this format is being retired. This parser is solely provided
    to help sustain existing Spring Python apps until they can migrate to
    the :doc:`PythonConfig <objects-pythonconfig>`, :doc:`XMLConfig <objects-xmlconfig>`
    or the :doc:`YamlConfig <objects-yamlconfig>` format.

.. highlight:: xml

An important thing to note is that PyContainer used the term *component*, while
Spring Python uses *object*. In order to support this legacy format, *component*
will show up in *PyContainerConfig*-based configurations::

    <?xml version="1.0" encoding="UTF-8"?>
    <components xmlns="http://www.springframework.org/springpython/schema/pycontainer-components"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/pycontainer-components
                http://springpython.webfactional.com/schema/context/spring-python-pycontainer-context-1.0.xsd">

        <component id="MovieLister" class="springpythontest.support.testSupportClasses.MovieLister" scope="prototype">
            <property name="finder" local="MovieFinder"/>
            <property name="description" local="SingletonString"/>
        </component>

        <component id="MovieFinder" class="springpythontest.support.testSupportClasses.ColonMovieFinder" scope="singleton">
            <property name="filename">"support/movies1.txt"</property>
        </component>

        <component id="SingletonString" class="springpythontest.support.testSupportClasses.StringHolder">
            <property name="str">"There should only be one copy of this string"</property>
        </component>
    </components>

.. highlight:: python

The definitions stored in this file are fed in to a *PyContainerConfig* which
scans it, and then sends the meta-data to the *ApplicationContext*. Then, when
the application code requests an object named "MovieLister" from the container,
the container utilizes an object factory to create an object and return it::

    from springpython.context import ApplicationContext
    from springpython.config import PyContainerConfig

    container = ApplicationContext(PyContainerConfig("app-context.xml"))
    service = container.get_object("MovieLister")


.. _objects-other-formats-springjavaconfig:

SpringJavaConfig
----------------

.. highlight:: xml

The *SpringJavaConfig* is a class that scans object definitions stored in the
format defined by the Spring Framework's original java version. This makes it
even easier to migrate parts of an existing Spring Java application onto the
Python platform.

.. note::

    This is about configuring Python objects NOT Java objects

    It is important to point out that this has nothing to do with configuring
    Java-backed beans from Spring Python, or somehow injecting Java-backed beans
    magically into a Python object. This is PURELY for configuring Python-backed
    objects using a format that was originally designed for pure Java beans.

    When ideas like "converting Java to Python" are mentioned, it is meant that
    re-writing certain parts of your app in Python would require a similar IoC
    configuration, however, for the Java and Python parts to integrate, you
    must utilize interoperable solutions like web service or other
    :doc:`remoting <remoting>` technologies.

::

    <?xml version="1.0" encoding="UTF-8"?>
    <beans xmlns="http://www.springframework.org/schema/beans"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/schema/beans
               http://www.springframework.org/schema/beans/spring-beans-2.5.xsd">

        <bean id="MovieLister" class="springpythontest.support.testSupportClasses.MovieLister" scope="prototype">
            <property name="finder" ref="MovieFinder"/>
            <property name="description"><ref bean="SingletonString"/></property>
        </bean>

        <bean id="MovieFinder" class="springpythontest.support.testSupportClasses.ColonMovieFinder" scope="singleton">
            <property name="filename"><value>support/movies1.txt</value></property>
        </bean>

        <bean id="SingletonString" class="springpythontest.support.testSupportClasses.StringHolder">
            <property name="str" value="There should only be one copy of this string"></property>
        </bean>
    </beans>

.. highlight:: python

The definitions stored in this file are fed in to a *SpringJavaConfig*  which
scans it, and then sends the meta-data to the *ApplicationContext*. Then, when
the application code requests an object named "MovieLister" from the container,
the container utilizes an object factory to create an object and return it::

    from springpython.context import ApplicationContext
    from springpython.config import SpringJavaConfig

    container = ApplicationContext(SpringJavaConfig("app-context.xml"))
    service = container.get_object("MovieLister")

Again, the only difference in your code is using *SpringJavaConfig* instead of
*PyContainerConfig* on one line. Everything is the same, since it is all inside
the *ApplicationContext*.


.. note::

    What parts of Spring Java configuration are supported?

    It is important to note that only spring-beans-2.5 has been tested at this
    point in time. It is possible that older versions of the XSD spec may also work.

    Spring Java's other names spaces, like *tx* and *aop*, probably DON'T work. They
    haven't been tested, and there is no special code that will utilize their
    feature set.

    How much of Spring Java will be supported? That is an open question, best
    discussed on `Spring Python's community forum <http://forum.springsource.org/forumdisplay.php?f=45>`_.
    Basically, this is meant to ease current Java developers into Spring Python and/or
    provide a means to split up objects to support porting parts of your application
    into Python. There isn't any current intention of providing full blown support.