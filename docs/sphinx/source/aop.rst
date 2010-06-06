Aspect Oriented Programming
===========================

*Aspect oriented programming* (AOP) is a horizontal programming paradigm,
where some type of behavior is applied to several classes that don't share
the same vertical, object-oriented inheritance. In AOP, programmers implement
these *cross cutting concerns* by writing an *aspect* then applying it
conditionally based on a *join point*. This is referred to as applying *advice*.
This section shows how to use the AOP module of Spring Python.

External dependencies
---------------------

Spring Python's AOP itself doesn't require any special external libraries to
work however the IoC configuration format of your choice, unless you use
:doc:`PythonConfig <objects-pythonconfig>`, will likely need some. Refer to the
:doc:`IoC documentation <objects>` for more details.

Interceptors
------------

Spring Python implements AOP advice using *proxies* and *method interceptors*.
NOTE: Interceptors only apply to method calls. Any request for attributes are
passed directly to the target without AOP intervention.

Here is a sample service. Our goal is to wrap the results with "wrapped" tags,
without modifying the service's code::

    class SampleService:
        def method(self, data):
            return "You sent me '%s'" % data
        def doSomething(self):
            return "Okay, I'm doing something"

If we instantiate and call this service directly, the results are straightforward::

    service = SampleService()
    print service.method("something")

    "You sent me 'something'"

.. highlight:: xml

To configure the same thing using the IoC container, put the following text
into a file named app-context.xml::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                   http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="service" class="SampleService"/>

    </objects>

.. highlight:: python

To instantiate the IoC container, use the following code::

    from springpython.context import ApplicationContext
    from springpython.config import XMLConfig

    container = ApplicationContext(XMLConfig("app-context.xml"))
    service = container.get_object("service")

You can use either mechanism to define an instance of your service. Now, let's
write an interceptor that will catch any results, and wrap them with <Wrapped>
tags::

    from springpython.aop import *
    class WrappingInterceptor(MethodInterceptor):
        def invoke(self, invocation):
            results = "<Wrapped>" + invocation.proceed() + "</Wrapped>"
            return results

*invoke(self, invocation)* is a dispatching method defined abstractly in the
*MethodInterceptor* base class. *invocation* holds the target method name, any
input arguments, and also the callable target function. In this case, we aren't
interested in the method name or the arguments. So we call the actual function
using *invocation.proceed()*, and than catch its results. Then we can manipulate
these results, and return them back to the caller.

In order to apply this advice to a service, a stand-in proxy must be created
and given to the client. One way to create this is by creating a *ProxyFactory*.
The factory is used to identify the target service that is being intercepted.
It is used to create the dynamic proxy object to give back to the client.

You can use the Spring Python APIs to directly create this proxied service::

    from springpython.aop import *
    factory = ProxyFactory()
    factory.target = SampleService()
    factory.interceptors.append(WrappingInterceptor())
    service = factory.getProxy()

.. highlight:: xml

Or, you can insert this definition into your app-context.xml file::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                   http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="targetService" class="SampleService"/>

        <object id="serviceFactory" class="springpython.aop.ProxyFactory">
            <property name="target" ref="targetService"/>
            <property name="interceptors">
                <object class="WrappingInterceptor"/>
            </property>
        </object>

    </objects>

.. highlight:: python

If you notice, the original Spring Python "service" object has been renamed as
"targetService", and there is, instead, another object called "serviceFactory"
which is a Spring AOP ProxyFactory. It points to the target service and also
has an interceptor plugged in. In this case, the interceptor is defined as an
inner object, not having a name of its own, indicating it is not meant to be
referenced outside the IoC container. When you get a hold of this, you can
request a proxy::

    from springpython.context import ApplicationContext
    from springpython.config import XMLConfig

    container = ApplicationContext(XMLConfig("app-context.xml"))
    serviceFactory = container.get_object("serviceFactory")
    service = serviceFactory.getProxy()

Now, the client can call *service*, and all function calls will be routed to
*SampleService* with one simple detour through *WrappingInterceptor*::

    print service.method("something")

    "<Wrapped>You sent me 'something'</Wrapped>"

Notice how I didn't have to edit the original service at all? I didn't even
have to introduce Spring Python into that module. Thanks to the power of
Python's dynamic nature, Spring Python AOP gives you the power to wrap your
own source code as well as other 3rd party modules.

Proxy Factory Objects
---------------------

The earlier usage of a *ProxyFactory* is useful, but often times we only need the
factory to create one proxy. There is a shortcut called *ProxyFactoryObject*::

    from springpython.aop import *

    service = ProxyFactoryObject()
    service.target = SampleService()
    service.interceptors = [WrappingInterceptor()]
    print service.method(" proxy factory object")

    "You sent me a 'proxy factory object'"

.. highlight:: xml

To configure the same thing using the IoC container, put the following text
into a file named *app-context.xml*::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                   http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="targetService" class="SampleService"/>

        <object id="service" class="springpython.aop.ProxyFactoryObject">
            <property name="target" ref="targetService"/>
            <property name="interceptors">
                <object class="WrappingInterceptor"/>
            </property>
        </object>

    </objects>

.. highlight:: python

In this case, the *ProxyFactoryObject* acts as both a proxy and a factory. As a
proxy, it behaves just like the target service would, and it also provides the
ability to wrap the service with aspects. It saved us a step of coding, but
more importantly, the *ProxyFactoryObject* took on the persona of being our
service right from the beginning.

To be more pythonic, Spring Python also allows you to initialize everything
at once::

    from springpython.aop import *

    service = ProxyFactoryObject(target = SampleService(), interceptors = [WrappingInterceptor()])

Pointcuts
---------

Sometimes we only want to apply advice to certain methods. This requires
definition of a *join point*. Join points are composed of rules referred to as
point cuts.

In this case, we want to only apply our *WrappingInterceptor* to methods that
start with "do"::

    from springpython.aop import *

    pointcutAdvisor = RegexpMethodPointcutAdvisor(advice = [WrappingInterceptor()], patterns = [".*do.*"])
    service = ProxyFactoryObject(target = SampleService(), interceptors = pointcutAdvisor)
    print service.method("nothing changed here")

    "You sent me 'nothing changed here'"

    print service.doSomething()

    "<Wrapped>Okay, I'm doing something</Wrapped"

.. note::

    The power of RegexpMethodPointAdvisor

    *RegexpMethodPointAdvisor* is a powerful object in Spring Python that acts as
    *pointcut*, a *join point*, and a *method interceptor*. It fetches the fullpath
    of the target's module, class, and method name, and then checks to see if
    it matches any of the patterns in the *patterns* list using Python's regular
    expression module.

By plugging this into a *ProxyFactoryObject* as an interceptor, it evaluates
whether to route method calls through the advice, or directly to the target service.

Interceptor Chain
-----------------

You may have noticed by now that the WrappingInterceptor is being specified
inside a Python list. That is because you can apply more than one piece of
advice. When an interceptor calls invocation.proceed(), it is actually calling
the next interceptor in the chain, until it gets to the end. Then it calls the
actual target service. When the target method returns back, everything
backtracks back out the set of nested interceptors.


Spring Python is coded to intelligently detect if you are assigning a single
interceptor to the interceptors property, or a list. A single interceptor gets
converted into a list of one. So, you can do either of the following::

    service = ProxyFactoryObject()
    service.interceptors = WrappingInterceptor()

or::

    service = ProxyFactoryObject()
    factory.interceptors = [WrappingInterceptor()]

It produces the same thing.

Coding AOP with Pure Python
----------------------------

There is a long history of Spring being based on XML. However, Spring Python
offers an easy to use alternative: :doc:`a pure Python decorator-based PythonConfig <objects-pythonconfig>`.
Imagine you had set up a simple context like this::

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

From an AOP perspective, it is easy to intercept *MovieFinder* and wrap it with
some advice. Because you have already exposed it as an injection point with
this pure-Python IoC container, you just need to make this change::

    from springpython.aop import *
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

        # By renaming the original service to this...
        def targetMovieFinder(self):
            return ColonMovieFinder(filename="support/movies1.txt")

        #...we can substitute a proxy that will wrap it with an interceptor
        @Object(scope.SINGLETON)
        def MovieFinder(self):
            return ProxyFactoryObject(target=self.targetMovieFinder(),
                                     interceptors=MyInterceptor())


        @Object # scope.SINGLETON is the default
        def SingletonString(self):
            return StringHolder("There should only be one copy of this string")

    class MyInterceptor(MethodInterceptor):
        def invoke(self, invocation):
            results = "<Wrapped>" + invocation.proceed() + "</Wrapped>"
            return results

Now, everything that was referring to the original *ColonMovieFinder* instance,
is instead pointing to a wrapping interceptor. The caller and callee involved
don't know anything about it, keeping your code isolated and clean.

.. note::

    Shouldn't you decouple the interceptor from the IoC configuration?

    It is usually good practice to split up configuration from actual business
    code. These two were put together in the same file for demonstration purposes.