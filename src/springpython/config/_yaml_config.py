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
import collections

from _config_base import *
from springpython.context import scope
from decorator import decorator, partial
from springpython.context import ApplicationContextAware
from springpython.factory import PythonObjectFactory
from springpython.factory import ReflectiveObjectFactory
from springpython.container import InvalidObjectScope

yaml_mappings = {
    "str":"types.StringType", "unicode":"types.UnicodeType",
    "int":"types.IntType", "long":"types.LongType",
    "float":"types.FloatType", "decimal":"decimal.Decimal",
    "bool":"types.BooleanType", "complex":"types.ComplexType",
    "list":"types.ListType", "tuple":"types.TupleType",
    "dict":"types.DictType",
}

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

            # A dictionary of abstract objects, keyed by their IDs, used in
            # traversing the hierarchies of parents; built upfront here for
            # convenience.
            self.abstract_objects = {}
            for object in doc["objects"]:
                if "abstract" in object:
                    self.abstract_objects[object["object"]] = object

            for object in doc["objects"]:
                self._print_obj(object)
                self.objects.append(self._convert_object(object))

        self.logger.debug("==============================================================")
        self.logger.debug("objects = %s" % self.objects)
        return self.objects

    def _map_custom_class(self, obj, mappings):
        """ Enrich the object's attributes and make it look to the rest of
        YamlConfig as if the object had all of them right in the definition.
        """
        for class_name in mappings:
            if class_name in obj:
                self.logger.debug("Found a matching type: %s -> %s" % (obj["object"],
                    class_name))

                obj["class"] = mappings[class_name]
                obj["constructor-args"] = [obj[class_name]]
                break
        else:
            self.logger.warning("No matching type found for object %s" % obj)

    def _convert_child_object(self, leaf, child, pos_constr,
                              named_constr, props):

        parent = self.abstract_objects[child["parent"]]

        # At this point we only build up the lists of parameters but we don't create
        # the object yet because the current parent object may still have its
        # own parent.

        # Positional constructors

        parent_pos_constrs = self._get_pos_constr(parent)

        # Make sure there are as many child positional parameters as there
        # are in the parent's list.

        len_pos_constr = len(pos_constr)
        len_parent_pos_constrs = len(parent_pos_constrs)

        if len_pos_constr < len_parent_pos_constrs:
            pos_constr.extend([None] * (len_parent_pos_constrs - len_pos_constr))

        for idx, parent_pos_constr in enumerate(parent_pos_constrs):
            if not pos_constr[idx]:
                pos_constr[idx] = parent_pos_constr

        # Named constructors
        child_named_constrs = named_constr
        parent_named_constrs = self._get_named_constr(parent)

        for parent_named_constr in parent_named_constrs:
            if parent_named_constr not in child_named_constrs:
                named_constr[parent_named_constr] = parent_named_constrs[parent_named_constr]

        # Properties
        child_props = [prop.name for prop in props]
        parent_props = self._get_props(parent)

        for parent_prop in parent_props:
            if parent_prop.name not in child_props:
                props.append(parent_prop)

        if "parent" in parent:
            # Continue traversing up the parent objects
            return self._convert_child_object(leaf, parent, pos_constr, named_constr, props)
        else:
            # Now we know we can create an object out of all the accumulated values.
            
            # The object's class is its topmost parent's class.
            class_ = parent["class"]
            id, factory, lazy_init, abstract, parent, scope_ = self._get_basic_object_data(leaf, class_)

            c = self._create_object(id, factory, lazy_init, abstract, parent,
                           scope_, pos_constr, named_constr, props)

            return c

    def _get_pos_constr(self, object):
        """ Returns a list of all positional constructor arguments of an object.
        """
        if "constructor-args" in object and isinstance(object["constructor-args"], list):
            return [self._convert_prop_def(object, constr, object["object"]) for constr in object["constructor-args"]]
        return []

    def _get_named_constr(self, object):
        """ Returns a dictionary of all named constructor arguments of an object.
        """
        if "constructor-args" in object and isinstance(object["constructor-args"], dict):
            return dict([(name, self._convert_prop_def(object, constr, object["object"]))
                            for (name, constr) in object["constructor-args"].items()])
        return {}

    def _get_props(self, object):
        """ Returns a list of all properties defined by an object.
        """
        if "properties" in object:
            return [self._convert_prop_def(object, p, name) for (name, p) in object["properties"].items()]
        return []

    def _create_object(self, id, factory, lazy_init, abstract, parent,
                           scope, pos_constr, named_constr, props):
        """ A helper function which creates an object out of the supplied
        arguments.
        """

        c = ObjectDef(id=id, factory=factory, lazy_init=lazy_init,
            abstract=abstract, parent=parent)

        c.scope = scope
        c.pos_constr = pos_constr
        c.named_constr = named_constr
        c.props = props

        self.logger.debug("object: props = %s" % c.props)
        self.logger.debug("object: There are %s props" % len(c.props))

        return c

    def _get_basic_object_data(self, object, class_):
        """ A convenience method which creates basic object's data so that
        the code is not repeated.
        """

        if "scope" in object:
            scope_ = scope.convert(object["scope"])
        else:
            scope_ = scope.SINGLETON

        return(object["object"],  ReflectiveObjectFactory(class_),
            object.get("lazy-init", False), object.get("abstract", False),
               object.get("parent"), scope_)

    def _convert_object(self, object, prefix=""):
        "This function generates a object definition, then converts scope and property elements."
        if prefix != "":
            if "object" in object and object["object"] is not None:
                object["object"] = prefix + "." + object["object"]
            else:
                object["object"] = prefix + ".<anonymous>"
        
        if not "class" in object and "parent" not in object:
            self._map_custom_class(object, yaml_mappings)
        
        pos_constr = self._get_pos_constr(object)
        named_constr = self._get_named_constr(object)
        props = self._get_props(object)
        
        if "parent" in object:
            return self._convert_child_object(object, object, pos_constr, named_constr, props)
        else:
            id, factory, lazy_init, abstract, parent, scope_ = self._get_basic_object_data(object, object.get("class"))

            return self._create_object(id, factory, lazy_init, abstract, parent,
                                       scope_, pos_constr, named_constr, props)

    def _print_obj(self, obj, level=0):
        self.logger.debug("%sobject = %s" % ("\t"*level, obj["object"]))
        self.logger.debug("%sclass = %s" % ("\t"*(level+1), obj.get("class")))

        if "scope" in obj:
            self.logger.debug("%sscope = %s" % ("\t"*(level+1), obj["scope"]))
        else:
            self.logger.debug("%sscope = singleton (default)" % ("\t"*(level+1)))

        if "properties" in obj:
            self.logger.debug("%sproperties:" % ("\t"*(level+1)))
            for prop in obj["properties"].keys():
                if isinstance(obj["properties"][prop], collections.Iterable) and "object" in obj["properties"][prop]:
                    self.logger.debug("%s%s = ..." % ("\t"*(level+2), prop))
                    self._print_obj(obj["properties"][prop], level+3)
                else:
                    self.logger.debug("%s%s = %s" % ("\t"*(level+2), prop, obj["properties"][prop]))
        self.logger.debug("")

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
                    d[k] = self._convert_tuple(v["tuple"], id, "%s.dict['%s']" % (name, k))
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
            return ValueDef(name, p)
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

