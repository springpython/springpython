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
import amara
import inspect
import logging
import re
import types
from decorator import decorator
from springpython.context import scope
from springpython.context import ApplicationContextAware
from springpython.factory import PythonObjectFactory
from springpython.factory import ReflectiveObjectFactory

class ObjectDef(object):
    """
    ObjectDef is a format-neutral way of storing object definition information. It includes
    a handle for the actual ObjectFactory that should be used to utilize this information when
    creating an instance of a object.
    """
    def __init__(self, id, props = None, factory = None, scope = scope.SINGLETON, lazy_init = False):
        super(ObjectDef, self).__init__()
        self.id = id
        self.factory = factory
        if props is None:
            self.props = []
        else:
            self.props = props
        self.scope = scope
        self.lazy_init = lazy_init
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
            self.logger.debug("Checking out %s, wondering if I need to do any replacement..." % str(self.value[i]))
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
                self.logger.debug("Item !!!%s!!! is NOT a ref, trying to replace with scanned value" % str(item))
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
                self.logger.debug("Item <<<%s>>> is NOT a ref, trying to replace with scanned value" % str(item))
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
        return new_frozen_set
 
class Config(object):
    """
    Config is an interface that defines how to read object definitions from an input source.
    """
    def read_object_defs(self):
        """Abstract method definition - should return an array of Object objects"""
        raise NotImplementedError()

class PyContainerConfig(Config):
    """
    PyContainerConfig supports the legacy XML dialect (PyContainer) of reading object definitions.
    """
    def __init__(self, config_location):
        if isinstance(config_location, list):
            self.config_location = config_location
        else:
            self.config_location = [config_location]
        self.logger = logging.getLogger("springpython.config.PyContainerConfig")

    def read_object_defs(self):
        self.logger.debug("==============================================================")
        objects = []
        for config in self.config_location:
            self.logger.debug("* Parsing %s" % config)
            doc = amara.parse(config)
            objects.extend([self._convert_component(component) for component in doc.components.component])
        self.logger.debug("==============================================================")
        return objects


    def _convert_component(self, component):
        "This function generates a object definition, then converts scope and property elements."
        c = ObjectDef(component.id, factory=ReflectiveObjectFactory(component.class_))
        if hasattr(component, "scope"):
            c.scope = scope.convert(component.scope)
        if hasattr(component, "property"):
            c.props = [self._convert_prop_def(p) for p in component.property]
        return c

    def _convert_prop_def(self, p):
        "This function translates object properties into useful dictionaries of information for the container."
        if hasattr(p, "local"):
            return ReferenceDef(p.name, p.local)
        elif hasattr(p, "list"):
            return ListDef(p.name, [ReferenceDef(p.name + ".list", prop_list.local) for prop_list in p.list])
        else:
            return ValueDef(p.name, eval(str(p).strip()))

class SpringJavaConfig(Config):
    """
    SpringJavaConfig supports current Spring Java format of XML bean definitions.
    """
    def __init__(self, config_location):
        if isinstance(config_location, list):
            self.config_location = config_location
        else:
            self.config_location = [config_location]
        self.logger = logging.getLogger("springpython.config.SpringJavaConfig")
        
        # By making this an instance-based property (instead of function local), inner object
        # definitions can add themselves to the list in the midst of parsing an input.
        self.objects = []

    def read_object_defs(self):
        self.logger.debug("==============================================================")
        # Reset, in case the file is re-read
        self.objects = []
        for config in self.config_location:
            self.logger.debug("* Parsing %s" % config)
            doc = amara.parse(config)
            self.objects.extend([self._convert_bean(bean) for bean in doc.beans.bean])
        self.logger.debug("==============================================================")
        return self.objects

    def _convert_bean(self, bean, prefix=""):
        "This function generates a object definition, then converts scope and property elements."
        if prefix != "":
            if hasattr(bean, "id"):
                bean.id = prefix + bean.id
            else:
                bean.id = prefix + "<anonymous>"
                
        c = ObjectDef(bean.id, factory=ReflectiveObjectFactory(bean.class_))
        
        if hasattr(bean, "scope"):
            c.scope = scope.convert(bean.scope)
        if hasattr(bean, "constructor_arg"):
            c.pos_constr = [self._convert_prop_def(bean, constr, bean.id + ".constr") for constr in bean.constructor_arg]
            self.logger.debug("Constructors = %s" % c.pos_constr)
        if hasattr(bean, "property"):
            c.props = [self._convert_prop_def(bean, p, p.name) for p in bean.property]
            
        return c

    def _convert_prop_def(self, bean, p, name):
        "This function translates object constructors/properties into useful collections of information for the container."
        if hasattr(p, "ref"):
            if hasattr(p.ref, "bean"):
                return ReferenceDef(name, p.ref.bean)
            else:
                return ReferenceDef(name, p.ref)
        elif hasattr(p, "value"):
            return ValueDef(name, str(p.value))
        elif hasattr(p, "map"):
            dict = {}
            for entry in p.map.entry:
                if hasattr(entry, "value"):
                    dict[str(entry.key.value)] = str(entry.value)
                elif hasattr(entry, "ref"):
                    dict[str(entry.key.value)] = ReferenceDef(str(entry.key.value), entry.ref.bean)
                else:
                    self.logger.debug("Don't know how to handle %s" % entry)
            return DictDef(name, dict)
        elif hasattr(p, "props"):
            dict = {}
            for prop in p.props.prop:
                dict[prop.key] = str(prop)
            return DictDef(name, dict)
        elif hasattr(p, "list"):
            list = []
            for element in p.list.xml_children:
                if isinstance(element, amara.bindery.element_base):
                    if element.localName == "value":
                        list.append(str(element))
                    elif element.localName == "ref":
                        list.append(ReferenceDef(name + ".list", element.bean))
                    else:
                        self.logger.debug("Don't know how to handle %s" % element.localName)
            return ListDef(name, list)
        elif hasattr(p, "set"):
            s = set()
            for element in p.set.xml_children:
                if isinstance(element, amara.bindery.element_base):
                    if element.localName == "value":
                        s.add(str(element))
                    elif element.localName == "ref":
                        s.add(ReferenceDef(name + ".set", element.bean))
                    else:
                        self.logger.debug("Don't know how to handle %s" % element.localName)
            return SetDef(name, s)
        elif hasattr(p, "bean"):
            inner_object_def = self._convert_bean(p.bean, prefix=bean.id + "." + name + ".")
            self.objects.append(inner_object_def)
            return InnerObjectDef(name, inner_object_def)

class XMLConfig(Config):
    """
    XMLConfig supports current Spring Python format of XML object definitions.
    """
    def __init__(self, config_location):
        if isinstance(config_location, list):
            self.config_location = config_location
        else:
            self.config_location = [config_location]
        self.logger = logging.getLogger("springpython.config.XMLConfig")
        
        # By making this an instance-based property (instead of function local), inner object
        # definitions can add themselves to the list in the midst of parsing an input.
        self.objects = []

    def read_object_defs(self):
        self.logger.debug("==============================================================")
        # Reset, in case the file is re-read
        self.objects = []
        for config in self.config_location:
            self.logger.debug("* Parsing %s" % config)
            doc = amara.parse(config)
            self.objects.extend([self._convert_object(object) for object in doc.objects.object])
        self.logger.debug("==============================================================")
        return self.objects

    def _convert_object(self, object, prefix=""):
        "This function generates a object definition, then converts scope and property elements."
        if prefix != "":
            if hasattr(object, "id"):
                object.id = prefix + "." + object.id
            else:
                object.id = prefix + ".<anonymous>"
                
        c = ObjectDef(object.id, factory=ReflectiveObjectFactory(object.class_))
        
        if hasattr(object, "scope"):
            c.scope = scope.convert(object.scope)
        if hasattr(object, "constructor_arg"):
            c.pos_constr = [self._convert_prop_def(object, constr, object.id + ".constr") for constr in object.constructor_arg
                            if not hasattr(constr, "name")]
            c.named_constr = dict([(str(constr.name), self._convert_prop_def(object, constr, object.id + ".constr")) for constr in object.constructor_arg
                                   if hasattr(constr, "name")])
        if hasattr(object, "property"):
            c.props = [self._convert_prop_def(object, p, p.name) for p in object.property]
            
        return c
    
    def _convert_ref(self, ref_node, name):
        if hasattr(ref_node, "object"):
            return ReferenceDef(name, ref_node.object)
        else:
            return ReferenceDef(name, ref_node)
 
    def _convert_value(self, value, id, name):
        results = []
        for element in value.xml_children:
            if isinstance(element, amara.bindery.element_base):
                results.append(self._convert_value(element, id, name))
            else:
                if value.localName == "value":
                    return str(element)

        if value.localName == "tuple":
            self.logger.debug("Converting a tuple")
            results = self._convert_tuple(value, id, name).value
        elif value.localName == "list":
            self.logger.debug("Converting a list")
            results = self._convert_list(value, id, name).value
        elif value.localName == "dict":
            self.logger.debug("Converting a dict")
            results = self._convert_dict(value, id, name).value
        elif value.localName == "set":
            self.logger.debug("Converting a set")
            results = self._convert_set(value, id, name).value
        elif value.localName == "frozenset":
            self.logger.debug("Converting a frozenset")
            results = self._convert_frozen_set(value, id, name).value
        elif len(results) == 1:
            results = results[0]

        return results
    
    def _convert_dict(self, dict_node, id, name):
        dict = {}
        for entry in dict_node.entry:
            key = None
            for element in entry.xml_children:
                if isinstance(element, amara.bindery.element_base):
                    if element.localName == "key":
                        pass # key is required, and known to already be at entry.key, so no need to re-parse it here
                    elif element.localName == "value":
                        dict[str(entry.key.value)] = self._convert_value(element, id, "%s.dict['%s']" % (name, entry.key.value))
                    elif element.localName == "ref":
                        dict[str(entry.key.value)] = self._convert_ref(element, "%s.dict['%s']" % (name, entry.key.value))
                    elif element.localName == "object":
                        self.logger.debug("Parsing an inner object definition...")
                        dict[str(entry.key.value)] = self._convert_inner_object(element, id, "%s.dict['%s']" % (name, entry.key.value))
                    elif element.localName in ["list", "tuple", "set", "frozenset"]:
                        self.logger.debug("This dictionary entry has child elements of type %s." % element.localName)
                        dict[str(entry.key.value)] = self._convert_value(element, id, "%s.dict['%s']" % (name, entry.key.value))
                    else:
                        self.logger.debug("dict: Don't know how to handle %s" % element.localName)
        return DictDef(name, dict)

    def _convert_props(self, props_node, name):
        dict = {}
        for prop in props_node.prop:
            dict[prop.key] = str(prop)
        return DictDef(name, dict)

    def _convert_list(self, list_node, id, name):
        list = []
        for element in list_node.xml_children:
            if isinstance(element, amara.bindery.element_base):
                if element.localName == "value":
                    list.append(str(element))
                elif element.localName == "ref":
                    list.append(self._convert_ref(element, "%s.list[%s]" % (name, len(list))))
                elif element.localName == "object":
                    self.logger.debug("Parsing an inner object definition...")
                    list.append(self._convert_inner_object(element, id, "%s.list[%s]" % (name, len(list))))
                elif element.localName in ["dict", "tuple", "set", "frozenset", "list"]:
                    self.logger.debug("This list has child elements of type %s." % element.localName)
                    list.append(self._convert_value(element, id, "%s.list[%s]" % (name, len(list))))
                    self.logger.debug("List is now %s" % list)
                else:
                    self.logger.debug("list: Don't know how to handle %s" % element.localName)
        return ListDef(name, list)

    def _convert_tuple(self, tuple_node, id, name):
        list = []
        for element in tuple_node.xml_children:
            if isinstance(element, amara.bindery.element_base):
                if element.localName == "value":
                    list.append(str(element))
                elif element.localName == "ref":
                    list.append(self._convert_ref(element, "%s.tuple(%s}" % (name, len(list))))
                elif element.localName == "object":
                    self.logger.debug("Parsing an inner object definition...")
                    list.append(self._convert_inner_object(element, id, "%s.tuple(%s)" % (name, len(list))))
                elif element.localName in ["dict", "tuple", "set", "frozenset", "list"]:
                    self.logger.debug("This tuple has child elements of type %s." % element.localName)
                    list.append(self._convert_value(element, id, "%s.tuple(%s)" % (name, len(list))))
                else:
                    self.logger.debug("tuple: Don't know how to handle %s" % element.localName)
        return TupleDef(name, tuple(list))

    def _convert_set(self, set_node, id, name):
        s = set()
        for element in set_node.xml_children:
            if isinstance(element, amara.bindery.element_base):
                if element.localName == "value":
                    s.add(str(element))
                elif element.localName == "ref":
                    s.add(self._convert_ref(element, name + ".set"))
                elif element.localName == "object":
                    self.logger.debug("Parsing an inner object definition...")
                    s.add(self._convert_inner_object(element, id, "%s.set(%s)" % (name, len(s))))
                elif element.localName in ["dict", "tuple", "set", "frozenset", "list"]:
                    self.logger.debug("This set has child elements of type %s." % element.localName)
                    s.add(self._convert_value(element, id, "%s.set(%s)" % (name,len(s)))) 
                else:
                    self.logger.debug("set: Don't know how to handle %s" % element.localName)
        return SetDef(name, s)

    def _convert_frozen_set(self, frozen_set_node, id, name):
        item = self._convert_set(frozen_set_node, id, name)
        return FrozenSetDef(name, frozenset(item.value))

    def _convert_inner_object(self, object_node, id, name):
        inner_object_def = self._convert_object(object_node, prefix="%s.%s" % (id, name))
        self.objects.append(inner_object_def)
        return InnerObjectDef(name, inner_object_def)

    def _convert_prop_def(self, comp, p, name):
        "This function translates object properties into useful collections of information for the container."
        if hasattr(p, "ref"):
            return self._convert_ref(p.ref, name)
        elif hasattr(p, "value"):
            return ValueDef(name, str(p.value))
        elif hasattr(p, "dict"):
            return self._convert_dict(p.dict, comp.id, name)
        elif hasattr(p, "props"):
            return self._convert_props(p.props, name)
        elif hasattr(p, "list"):
            return self._convert_list(p.list, comp.id, name)
        elif hasattr(p, "tuple"):
            return self._convert_tuple(p.tuple, comp.id, name)
        elif hasattr(p, "set"):
            return self._convert_set(p.set, comp.id, name)
        elif hasattr(p, "frozenset"):
            self.logger.debug("Converting frozenset")
            return self._convert_frozen_set(p.frozenset, comp.id, name)
        elif hasattr(p, "object"):
            return self._convert_inner_object(p.object, comp.id, name)

class YamlConfig(Config):
    """
    YamlConfig provides an alternative YAML-based version of objects.
    """
    def __init__(self, config_location):
        if isinstance(config_location, list):
            self.config_location = config_location
        else:
            self.config_location = [config_location]
        self.logger = logging.getLogger("springpython.config.YamlConfig")
        
        # By making this an instance-based property (instead of function local), inner object
        # definitions can add themselves to the list in the midst of parsing an input.
        self.objects = []

    def read_object_defs(self):
        import yaml

        self.logger.debug("==============================================================")
        # Reset, in case the file is re-read
        self.objects = []
        for config in self.config_location:
            self.logger.debug("* Parsing %s" % config)
            stream = file(config)
            doc = yaml.load(stream)
            self.logger.debug(doc)
            for object in doc["objects"]:
                self._print_obj(object)
            self.objects.extend([self._convert_object(object) for object in doc["objects"]])
        self.logger.debug("==============================================================")
        self.logger.debug("objects = %s" % self.objects)
        return self.objects

    def _print_obj(self, obj, level=0):
        self.logger.debug("%sobject id = %s" % ("\t"*level, obj["object"]))
        self.logger.debug("%sclass = %s" % ("\t"*(level+1), obj["class"]))

        if "scope" in obj:
            self.logger.debug("%sscope = %s" % ("\t"*(level+1), obj["scope"]))
        else:
            self.logger.debug("%sscope = singleton (default)" % ("\t"*(level+1)))

        if "properties" in obj:
            self.logger.debug("%sproperties:" % ("\t"*(level+1)))
            for prop in obj["properties"].keys():
                if "object" in obj["properties"][prop]:
                    self.logger.debug("%s%s = ..." % ("\t"*(level+2), prop))
                    self._print_obj(obj["properties"][prop], level+3)
                else:
                    self.logger.debug("%s%s = %s" % ("\t"*(level+2), prop, obj["properties"][prop]))
        self.logger.debug("")

    def _convert_object(self, object, prefix=""):
        "This function generates a object definition, then converts scope and property elements."
        if prefix != "":
            if "object" in object and object["object"] is not None:
                object["object"] = prefix + "." + object["object"]
            else:
                object["object"] = prefix + ".<anonymous>"
                
        c = ObjectDef(object["object"], factory=ReflectiveObjectFactory(object["class"]))
        
        if "scope" in object:
            c.scope = scope.convert(object["scope"])
        if "constructor-args" in object:
             if isinstance(object["constructor-args"], list):
                 c.pos_constr = [self._convert_prop_def(object, constr, object["object"]) for constr in object["constructor-args"]]
             if isinstance(object["constructor-args"], dict):
                 c.named_constr = dict([(name, self._convert_prop_def(object, constr, object["object"])) for (name, constr) in object["constructor-args"].items()])
        if "properties" in object:
            c.props = [self._convert_prop_def(object, p, name) for (name, p) in object["properties"].items()]
            
        return c

    def _convert_ref(self, ref_node, name):
        self.logger.debug("ref: Parsing %s, %s" % (ref_node, name))
        if "object" in ref_node:
            return ReferenceDef(name, ref_node["object"])
        else:
            return ReferenceDef(name, ref_node)
 
    def _convert_value(self, value, id, name):
        results = []

        if isinstance(value, dict):
            if "tuple" in value:
                self.logger.debug("value: Converting tuple")
                return self._convert_tuple(value["tuple"], id, name)
            elif "list" in value:
                self.logger.debug("value: Converting list")
                return self._convert_list(value["list"], id, name)
            elif "dict" in value:
                self.logger.debug("value: Converting dict")
                return self._convert_dict(value["dict"], id, name)
            elif "set" in value:
                self.logger.debug("value: Converting set")
                return self._convert_set(value["set"], id, name)
            elif "frozenset" in value:
                self.logger.debug("value: Converting frozenset")
                return self._convert_frozen_set(value["frozenset"], id, name)
        else:
            self.logger.debug("value: Plain ole value = %s" % value)
            return value

        return results
    
    def _convert_dict(self, dict_node, id, name):
        d = {}
        for (k, v) in dict_node.items():
            if isinstance(v, dict):
                self.logger.debug("dict: You have a special type stored at %s" % k)
                if "ref" in v:
                    self.logger.debug("dict/ref: k,v = %s,%s" % (k, v))
                    d[k] = self._convert_ref(v["ref"], "%s.dict['%s']" % (name, k))
                    self.logger.debug("dict: Stored %s => %s" % (k, d[k]))
                elif "tuple" in v:
                    self.logger.debug("dict: Converting a tuple...")
                    d[k] = self._convert_tuple(v["tuple"], "%s.dict['%s']" % ( name, k))
                else:
                    self.logger.debug("dict: Don't know how to handle type %s" % v)
            else:
                self.logger.debug("dict: %s is NOT a dict, so going to convert as a value." % v)
                d[k] = self._convert_value(v, id, "%s.dict['%s']" % (name, k))
        return DictDef(name, d)

    def _convert_props(self, props_node, name):
        dict = {}
        for prop in props_node.prop:
            dict[prop.key] = str(prop)
        return DictDef(name, dict)

    def _convert_list(self, list_node, id, name):
        list = []
        for item in list_node:
            self.logger.debug("list: Adding %s to list..." % item)
            if isinstance(item, dict):
                if "ref" in item:
                    list.append(self._convert_ref(item["ref"], "%s.list[%s]" % (name, len(list))))
                elif "object" in item:
                    list.append(self._convert_inner_object(item, id, "%s.list[%s]" % (name, len(list))))
                elif len(set(["dict", "tuple", "set", "frozenset", "list"]) & set(item)) > 0:
                    list.append(self._convert_value(item, id, "%s.list[%s]" % (name, len(list))))
                else:
                    self.logger.debug("list: Don't know how to handle %s" % item.keys())
            else:
                list.append(item)
        return ListDef(name, list)

    def _convert_tuple(self, tuple_node, id, name):
        list = []
        self.logger.debug("tuple: tuple_node = %s, id = %s, name = %s" % (tuple_node, id, name))
        for item in tuple_node:
            if isinstance(item, dict):
                if "ref" in item:
                    list.append(self._convert_ref(item["ref"], name + ".tuple"))
                elif "object" in item:
                    list.append(self._convert_inner_object(item, id, "%s.tuple[%s]" % (name, len(list))))
                elif len(set(["dict", "tuple", "set", "frozenset", "list"]) & set(item)) > 0:
                    list.append(self._convert_value(item, id, "%s.tuple[%s]" % (name, len(list))))
                else:
                    self.logger.debug("tuple: Don't know how to handle %s" % item)
            else:
                list.append(item)
        return TupleDef(name, tuple(list))

    def _convert_set(self, set_node, id, name):
        s = set()
        self.logger.debug("set: set_node = %s, id = %s, name = %s" % (set_node, id, name))
        for item in set_node:
            if isinstance(item, dict):
                if "ref" in item:
                    s.add(self._convert_ref(item["ref"], name + ".set"))
                elif "object" in item:
                    s.add(self._convert_inner_object(item, id, "%s.set[%s]" % (name, len(s))))
                elif len(set(["dict", "tuple", "set", "frozenset", "list"]) & set(item)) > 0:
                    s.add(self._convert_value(item, id, "%s.set[%s]" % (name, len(s))))
                else:
                    self.logger.debug("set: Don't know how to handle %s" % item)
            else:
                s.add(item)
        return SetDef(name, s)

    def _convert_frozen_set(self, frozen_set_node, id, name):
        item = self._convert_set(frozen_set_node, id, name)
        self.logger.debug("frozenset: Just got back converted set %s" % item)
        self.logger.debug("frozenset: value is %s, which will be turned into %s" % (item.value, frozenset(item.value)))
        return FrozenSetDef(name, frozenset(item.value))

    def _convert_inner_object(self, object_node, id, name):
        self.logger.debug("inner object: Converting %s" % object_node)
        inner_object_def = self._convert_object(object_node, prefix="%s.%s" % (id, name))
        self.objects.append(inner_object_def)
        return InnerObjectDef(name, inner_object_def)

    def _convert_prop_def(self, comp, p, name):
        "This function translates object properties into useful collections of information for the container."
        self.logger.debug("prop_def: Trying to read property %s -> %s" % (name, p))
        if isinstance(p, dict):
            if "ref" in p:
                self.logger.debug("prop_def: >>>>>>>>>>>>Call _convert_ref(%s, %s)" % (p["ref"], name))
                return self._convert_ref(p["ref"], name)
            elif "tuple" in p:
                self.logger.debug("prop_def: Call _convert_tuple(%s,%s,%s)" % (p["tuple"], comp["object"], name))
                return self._convert_tuple(p["tuple"], comp["object"], name)
            elif "set" in p:
                self.logger.debug("prop_def: Call _convert_set(%s,%s,%s)" % (p["set"], comp["object"], name))
                return self._convert_set(p["set"], comp["object"], name)
            elif "frozenset" in p:
                self.logger.debug("prop_def: Call _convert_frozen_set(%s,%s,%s)" % (p["frozenset"], comp["object"], name))
                return self._convert_frozen_set(p["frozenset"], comp["object"], name)
            elif "object" in p:
                self.logger.debug("prop_def: Call _convert_inner_object(%s,%s,%s)" % (p, comp["object"], name))
                return self._convert_inner_object(p, comp["object"], name)
            else:
                #self.logger.debug("prop_def: Don't know how to handle %s" % p)
                return self._convert_dict(p, comp["object"], name)
        elif isinstance(p, list):
            return self._convert_list(p, comp["object"], name)
        else:
            return ValueDef(name, str(p))
        return None

        if hasattr(p, "ref"):
            return self._convert_ref(p.ref, name)
        elif hasattr(p, "value"):
            return ValueDef(name, str(p.value))
        elif hasattr(p, "dict"):
            return self._convert_dict(p.dict, comp.id, name)
        elif hasattr(p, "props"):
            return self._convert_props(p.props, name)
        elif hasattr(p, "list"):
            return self._convert_list(p.list, comp.id, name)
        elif hasattr(p, "tuple"):
            return self._convert_tuple(p.tuple, comp.id, name)
        elif hasattr(p, "set"):
            return self._convert_set(p.set, comp.id, name)
        elif hasattr(p, "frozenset"):
            self.logger.debug("Converting frozenset")
            return self._convert_frozen_set(p.frozenset, comp.id, name)
        elif hasattr(p, "object"):
            return self._convert_inner_object(p.object, comp.id, name)

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
                        if wrapper.func_name == "objectPrototype":
                            c = ObjectDef(id=name, factory=PythonObjectFactory(method, wrapper), scope=scope.PROTOTYPE, lazy_init=wrapper.lazy_init)
                        else:
                            c = ObjectDef(id=name, factory=PythonObjectFactory(method, wrapper), lazy_init=wrapper.lazy_init)
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

def Object(theScope = scope.SINGLETON, lazy_init = False):
    """
    This function is a wrapper around the real decorator. It decides, based on scope
    and lazy-init, which decorator to return.
    """
    if type(theScope) == types.FunctionType:
        return Object()(theScope)
    elif theScope == scope.SINGLETON:
        def objectSingleton(f, *args, **kwargs):
            """
            This function checks if the object already exists in the container. If so, it will retrieve its results.
            Otherwise, it calls the function.

            Using the @decorator library greatly simplifies the implementation of this.
            """
            log = logging.getLogger("springpython.config.objectSingleton%s - %s%s" % (f, str(args), theScope))
            if f.func_name != top_func:
                log.debug("This is NOT the top-level object %s, deferring to container." % top_func)
                container = _object_context[args]["container"]
                log.debug("Container = %s" % container)
                results = container.get_object(f.func_name)
                log.debug("Found %s inside the container" % results)
                return results
            else:
                log.debug("This IS the top-level object, calling %s()." % f.func_name)
                results = f(*args, **kwargs)
                log.debug("Found %s" % results)
                return results
        objectSingleton.lazy_init = lazy_init
        return decorator(objectSingleton)
    elif theScope == scope.PROTOTYPE:
        def objectPrototype(f, *args, **kwargs):
            """
            This is basically a pass through, because everytime a prototype function
            is called, there should be no caching of results.
            
            Using the @decorator library greatly simplifies the implementation of this.
            """
            
            log = logging.getLogger("springpython.config.objectPrototype%s - %s%s" % (f, str(args), theScope))
            if f.func_name != top_func:
                log.debug("This is NOT the top-level object %s, deferring to container." % top_func)
                container = _object_context[args]["container"]
                log.debug("Container = %s" % container)
                results = container.get_object(f.func_name)
                log.debug("Found %s inside the container" % results)
                return results
            else:
                log.debug("This IS the top-level object, calling %s()." % f.func_name)
                results = f(*args, **kwargs)
                log.debug("Found %s" % results)
                return results
        objectPrototype.lazy_init = lazy_init
        return decorator(objectPrototype)
    else:
        raise InvalidObjectScope("Don't know how to handle scope %s" % theScope)
        
class InvalidObjectScope(Exception):
    pass
