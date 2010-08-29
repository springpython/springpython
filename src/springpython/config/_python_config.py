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
try:
    import cElementTree as etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        from elementtree import ElementTree as etree

import re
import types
import inspect
import logging

from _config_base import *
from springpython.context import scope
from decorator import decorator, partial
from springpython.context import ApplicationContextAware
from springpython.factory import PythonObjectFactory
from springpython.factory import ReflectiveObjectFactory
from springpython.container import InvalidObjectScope

class PythonConfig(Config, ApplicationContextAware):
    """
    PythonConfig supports using pure python code to define objects.
    """

    def __init__(self):
        self.logger = logging.getLogger("springpython.config.PythonConfig")
        super(PythonConfig, self).__init__()

    def read_object_defs(self):
        self.logger.debug("==============================================================")
        objects = []
        self.logger.debug("Parsing %s" % self)
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name not in _pythonConfigMethods:
                try:
                    wrapper = method.im_func.func_globals["_call_"]

                    if wrapper.func_name.startswith("object"):
                        c = ObjectDef(id=name, factory=PythonObjectFactory(method, wrapper),
                                scope=wrapper.scope, lazy_init=wrapper.lazy_init,
                                abstract=wrapper.abstract, parent=wrapper.parent)
                        objects.append(c)
                except KeyError, e:
                    pass
        self.logger.debug("==============================================================")
        return objects

    def set_app_context(self, app_context):
        super(PythonConfig, self).set_app_context(app_context)
        try:
            _object_context[(self,)]["container"] = app_context
        except KeyError, e:
            _object_context[(self,)] = {"container": app_context}


_pythonConfigMethods = [name for (name, method) in inspect.getmembers(PythonConfig, inspect.ismethod)]

_object_context = {}

def _object_wrapper(f, scope, parent, log_func_name, *args, **kwargs):
    """
    This function checks if the object already exists in the container. If so,
    it will retrieve its results. Otherwise, it calls the function.

    For prototype objects, the function is basically a pass through,
    because everytime a prototype function is called, there should be no
    caching of results.

    Using the @decorator library greatly simplifies the implementation of this.
    """

    def _deco(f, scope, parent, log_func_name, *args, **kwargs):
        log = logging.getLogger("springpython.config.%s%s - %s%s" % (log_func_name,
                                    f, str(args), scope))
        if f.func_name != top_func:
            log.debug("This is NOT the top-level object %s, deferring to container." % top_func)
            container = _object_context[args]["container"]
            log.debug("Container = %s" % container)

            if parent:
                parent_result = container.get_object(parent, ignore_abstract=True)
                log.debug("This IS the top-level object, calling %s(%s)" \
                           % (f.func_name, parent_result))
                results = container.get_object(f.func_name)(parent_result)
            else:
                results = container.get_object(f.func_name)

            log.debug("Found %s inside the container" % results)
            return results
        else:
            if parent:
                container = _object_context[(args[0],)]["container"]
                parent_result = container.get_object(parent, ignore_abstract=True)
                log.debug("This IS the top-level object, calling %s(%s)" \
                           % (f.func_name, parent_result))
                results = f(container, parent_result)
            else:
                log.debug("This IS the top-level object, calling %s()." % f.func_name)
                results = f(*args, **kwargs)

            log.debug("Found %s" % results)
            return results

    return _deco(f, scope, parent, log_func_name, *args, **kwargs)

def Object(theScope=scope.SINGLETON, lazy_init=False, abstract=False, parent=None):
    """
    This function is a wrapper around the function which returns the real decorator.
    It decides, based on scope and lazy-init, which decorator to return.
    """
    if type(theScope) == types.FunctionType:
        return Object()(theScope)

    elif theScope == scope.SINGLETON:
        log_func_name = "objectSingleton"

    elif theScope == scope.PROTOTYPE:
        log_func_name = "objectPrototype"

    else:
        raise InvalidObjectScope("Don't know how to handle scope %s" % theScope)

    def object_wrapper(f, *args, **kwargs):
        return _object_wrapper(f, theScope, parent, log_func_name, *args, **kwargs)

    object_wrapper.lazy_init = lazy_init
    object_wrapper.abstract = abstract
    object_wrapper.parent = parent
    object_wrapper.scope = theScope

    return decorator(object_wrapper)
