PythonConfig and @Object - decorator-driven configuration
=========================================================

By defining a class that extends *PythonConfig* and using the *@Object* decorator,
you can wire your application using pure Python code.::

    from springpython.config import PythonConfig
    from springpython.config import Object
    from springpython.context import scope

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

        @Object(lazy_init=True)    # scope.SINGLETON is the default
        def SingletonString(self):
            return StringHolder("There should only be one copy of this string")

        def NotExposed(self):
            pass

As part of this example, the method NotExposed is also shown. This indicates
that using *get_object* won't fetch that method, since it isn't considered an object.

By using pure Python, you don't have to deal with any XML. If you look closely,
you will notice that the container code below is only different in the line
actually creating the container. Everything else is the same as was in the
:doc:`XMLConfig <objects-xmlconfig>` & :doc:`YamlConfig <objects-yamlconfig>` examples.::

    from springpython.context import ApplicationContext

    container = ApplicationContext(MovieBasedApplicationContext())
    service = container.get_object("MovieLister")

Object definition inheritance
-----------------------------

PythonConfig's support for abstract objects is different to that of XMLConfig
or YamlConfig. With PythonConfig, the children object do not automatically
inherit nor override the parents' properties, they in fact receive the values
returned by their parents and it's up to them to decide, using Python code,
whether to use or to discard the values received.

A child object must have as many optional arguments as there are expected
to be returned by its parent.

Observe that in the following example the child definitions must define
an optional 'req' argument; in runtime they will be passed its value basing
on what their parent object will return. Note also that request is of
PROTOTYPE scope, if it were a SINGLETON then both get_customer_id_request
and get_customer_profile_request would receive the very same Request
instance which, in other circumstances, could be a desirable effect
but not in the example.::

    # stdlib
    import uuid4

    # .. skip Spring Python imports

    class Request(object):
        def __init__(self, nonce=None, user=None, password=None):
            self.nonce = nonce
            self.user = user
            self.password = password

        def __str__(self):
            return "<id=%s %s %s %s>" % (hex(id(self)), self.nonce, self.user, self.password)

    class TestAbstractContext(PythonConfig):

        @Object(scope.PROTOTYPE, abstract=True)
        def request(self):
            return Request()

        @Object(parent="request")
        def request_dev(self, req=None):
            req.user = "dev-user"
            req.password = "dev-password"

            return req

        @Object(parent="request")
        def request_test(self, req=None):
            req.user = "test-user"
            req.password = "test-password"

            return req

        @Object(parent="request_dev")
        def get_customer_id_request(self, req=None):
            req.nonce = uuid4().hex

            return req

        @Object(parent="request_test")
        def get_customer_profile_request(self, req=None):
            req.nonce = uuid4().hex

            return req

Same as with the other configuration modes, if you need to get an abstract
object from a container, use the .get_object's ignore_abstract parameter,
otherwise springpython.container.AbstractObjectException will be raised::

    # .. skip creating the context

    # No exception will be raised, even though 'request' is an abstract object
    request = ctx.get_object("request", ignore_abstract=True)

    # Will show the object
    print request

    # Will raise AbstractObjectException
    request = ctx.get_object("request")
