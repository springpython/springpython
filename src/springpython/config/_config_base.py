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
import re
import types
import inspect
import logging

from springpython.context import scope
from decorator import decorator, partial
from springpython.context import ApplicationContextAware
from springpython.factory import PythonObjectFactory
from springpython.factory import ReflectiveObjectFactory
from springpython.container import InvalidObjectScope

def get_string(value):
    """This function is used to parse text that could either be ASCII or unicode."""
    try:
        return str(value)
    except UnicodeEncodeError:
        return unicode(value)
        
class ObjectDef(object):
    """
    ObjectDef is a format-neutral way of storing object definition information. It includes
    a handle for the actual ObjectFactory that should be used to utilize this information when
    creating an instance of a object.
    """
    def __init__(self, id, props=None, factory=None, scope=scope.SINGLETON,
                 lazy_init=False, abstract=False, parent=None):
        super(ObjectDef, self).__init__()
        self.id = id
        self.factory = factory
        if props is None:
            self.props = []
        else:
            self.props = props
        self.scope = scope
        self.lazy_init = lazy_init
        self.abstract = abstract
        self.parent = parent
        self.pos_constr = []
        self.named_constr = {}

    def __str__(self):
        return "id=%s props=%s scope=%s factory=%s" % (self.id, self.props, self.scope, self.factory)

class ReferenceDef(object):
    """
    This class represents a definition that is referencing another object.
    """
    def __init__(self, name, ref):
        self.name = name
        self.ref = ref

    def prefetch(self, container):
        self.get_value(container)

    def get_value(self, container):
        return container.get_object(self.ref)

    def set_value(self, obj, container):
        setattr(obj, self.name, container.objects[self.ref])

    def __str__(self):
        return "name=%s ref=%s" % (self.name, self.ref)

class InnerObjectDef(object):
    """
    This class represents an inner object. It is optional whether or not the object
    has its own name.
    """
    def __init__(self, name, inner_comp):
        self.name = name
        self.inner_comp = inner_comp

    def prefetch(self, container):
        self.get_value(container)

    def get_value(self, container):
        return container.get_object(self.inner_comp.id)

    def set_value(self, obj, container):
        setattr(obj, self.name, self.get_value(container))

    def __str__(self):
        return "name=%s inner_comp=%s" % (self.name, self.inner_comp)

class ValueDef(object):
    """
    This class represents a property that holds a value. The value can be simple value, or
    it can be a complex container which internally holds references, inner objects, or
    any other type.
    """
    def __init__(self, name, value):
        self.name = name
        if value == "True":
            self.value = True
        elif value == "False":
            self.value= False
        else:
            self.value = value
        self.logger = logging.getLogger("springpython.config.ValueDef")

    def scan_value(self, container, value):
        if hasattr(value, "get_value"):
            return value.get_value(container)
        elif isinstance(value, tuple):
            new_list = [self.scan_value(container, item) for item in value]
            results = tuple(new_list)
            return results
        elif isinstance(value, list):
            new_list = [self.scan_value(container, item) for item in value]
            return new_list
        elif isinstance(value, set):
            results = set([self.scan_value(container, item) for item in value])
            return results
        elif isinstance(value, frozenset):
            results = frozenset([self.scan_value(container, item) for item in value])
            return results
        else:
            if value == "True":
                return True
            elif value == "False":
                return False
            else:
                return value

    def get_value(self, container):
        val = self._replace_refs_with_actuals(self.value, container)
        if val is None:
            return self.value
        else:
            return val

    def set_value(self, obj, container):
        setattr(obj, self.name, self.value)
        val = self._replace_refs_with_actuals(obj, container)

    def _replace_refs_with_actuals(self, obj, container):
        """Normal values do nothing for this step. However, sub-classes are defined for
        the various containers, like lists, set, dictionaries, etc., to handle iterating
        through and pre-fetching items."""
        pass

    def __str__(self):
        return "name=%s value=%s" % (self.name, self.value)

class DictDef(ValueDef):
    """Handles behavior for a dictionary-based value."""
    def __init__(self, name, value):
        super(DictDef, self).__init__(name, value)

    def _replace_refs_with_actuals(self, obj, container):
        for key in self.value.keys():
            if hasattr(self.value[key], "ref"):
                self.value[key] = container.get_object(self.value[key].ref)
            else:
                self.value[key] = self.scan_value(container, self.value[key])

class ListDef(ValueDef):
    """Handles behavior for a list-based value."""
    def __init__(self, name, value):
        super(ListDef, self).__init__(name, value)
        self.logger = logging.getLogger("springpython.config.ListDef")

    def _replace_refs_with_actuals(self, obj, container):
        for i in range(0, len(self.value)):
            self.logger.debug("Checking out %s, wondering if I need to do any replacement..." % get_string(self.value[i]))
            if hasattr(self.value[i], "ref"):
                self.value[i] = container.get_object(self.value[i].ref)
            else:
                self.value[i] = self.scan_value(container, self.value[i])

class TupleDef(ValueDef):
    """Handles behavior for a tuple-based value."""

    def __init__(self, name, value):
        super(TupleDef, self).__init__(name, value)

    def _replace_refs_with_actuals(self, obj, container):
        new_value = list(self.value)
        for i in range(0, len(new_value)):
            if hasattr(new_value[i], "ref"):
                new_value[i] = container.get_object(new_value[i].ref)
            else:
                new_value[i] = self.scan_value(container, new_value[i])
        try:
            setattr(obj, self.name, tuple(new_value))
        except AttributeError:
            pass
        return tuple(new_value)

class SetDef(ValueDef):
    """Handles behavior for a set-based value."""
    def __init__(self, name, value):
        super(SetDef, self).__init__(name, value)
        self.logger = logging.getLogger("springpython.config.SetDef")

    def _replace_refs_with_actuals(self, obj, container):
        self.logger.debug("Replacing refs with actuals...")
        self.logger.debug("set before changes = %s" % self.value)
        new_set = set()
        for item in self.value:
            if hasattr(item, "ref"):
                self.logger.debug("Item !!!%s!!! is a ref, trying to replace with actual object !!!%s!!!" % (item, item.ref))
                #self.value.remove(item)
                #self.value.add(container.get_object(item.ref))
                newly_fetched_value = container.get_object(item.ref)
                new_set.add(newly_fetched_value)
                self.logger.debug("Item !!!%s!!! was removed, and newly fetched value !!!%s!!! was added." % (item, newly_fetched_value))
                #new_set.add(container.get_object(item.ref))
            else:
                self.logger.debug("Item !!!%s!!! is NOT a ref, trying to replace with scanned value" % get_string(item))
                #self.value.remove(item)
                #self.value.add(self.scan_value(container, item))
                newly_scanned_value = self.scan_value(container, item)
                new_set.add(newly_scanned_value)
                self.logger.debug("Item !!!%s!!! was removed, and newly scanned value !!!%s!!! was added." % (item, newly_scanned_value))
                #new_set.add(self.scan_value(container, item))
        #self.value = new_set
        self.logger.debug("set after changes = %s" % new_set)
        #return self.value
        try:
            setattr(obj, self.name, new_set)
        except AttributeError:
            pass
        return new_set

class FrozenSetDef(ValueDef):
    """Handles behavior for a frozen-set-based value."""
    def __init__(self, name, value):
        super(FrozenSetDef, self).__init__(name, value)
        self.logger = logging.getLogger("springpython.config.FrozenSetDef")

    def _replace_refs_with_actuals(self, obj, container):
        self.logger.debug("Replacing refs with actuals...")
        self.logger.debug("set before changes = %s" % self.value)
        new_set = set()
        for item in self.value:
            if hasattr(item, "ref"):
                self.logger.debug("Item <<<%s>>> is a ref, trying to replace with actual object <<<%s>>>" % (item, item.ref))
                #new_set.remove(item)
                #debug begin
                newly_fetched_value = container.get_object(item.ref)
                new_set.add(newly_fetched_value)
                self.logger.debug("Item <<<%s>>> was removed, and newly fetched value <<<%s>>> was added." % (item, newly_fetched_value))
                #debug end
                #new_set.add(container.get_object(item.ref))
            else:
                self.logger.debug("Item <<<%s>>> is NOT a ref, trying to replace with scanned value" % get_string(item))
                #new_set.remove(item)
                #debug begin
                newly_scanned_value = self.scan_value(container, item)
                new_set.add(newly_scanned_value)
                self.logger.debug("Item <<<%s>>> was removed, and newly scanned value <<<%s>>> was added." % (item, newly_scanned_value))
                #debug end
                #new_set.add(self.scan_value(container, item))
        #self.logger.debug("Newly built set = %s" % new_set)
        #self.value = frozenset(new_set)
        new_frozen_set = frozenset(new_set)
        self.logger.debug("set after changes = %s" % new_frozen_set)
        #return self.value
        try:
            setattr(obj, self.name, new_frozen_set)
        except AttributeError:
            pass
        except TypeError:
            pass
        return new_frozen_set

class Config(object):
    """
    Config is an interface that defines how to read object definitions from an input source.
    """
    def read_object_defs(self):
        """Abstract method definition - should return an array of Object objects"""
        raise NotImplementedError()

