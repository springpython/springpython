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

import logging
from springpython.context import scope

class ObjectContainer(object):
    """
    ObjectContainer is a container which uses multiple Config objects to read sources of
    object definitions. When a object is requested from this container, it may optionally
    pull the object from a scoped cache. If there is no stored copy of the object, it
    uses the scanned definition and its associated ObjectFactory to create an instance. It
    can then optionally store it in a scoped cache for future usage (e.g. singleton).
    
    Object definitions are stored in the container in a neutral format, decoupling the
    container entirely from the original source location. This means that XML, python code,
    and other formats may all contain definitions. By the time they
    reach this container, it doesn't matter what their original format was when a object
    instance is needed. NOTE: This explicitly means that one object in one source
    can refer to another object in another source OF ANY FORMAT as a property.
    """
    def __init__(self, config = None):
        self.logger = logging.getLogger("springpython.container.ObjectContainer")

        if config is None:
            self.configs = []
        elif isinstance(config, list):
            self.configs = config
        else:
            self.configs = [config]

        self.object_defs = {}
    
        for configuration in self.configs:
            self.logger.debug("=== Scanning configuration %s for object definitions ===" % configuration)
            for object_def in configuration.read_object_defs():
                if object_def.id not in self.object_defs:
                    self.logger.debug("%s object definition does not exist. Adding to list of definitions." % object_def.id)
                else:
                    self.logger.debug("Overriding previous definition of %s" % object_def.id)
                self.object_defs[object_def.id] = object_def

        self.logger.debug("=== Done reading object definitions. ===")

        self.objects = {}

    def get_object(self, name, ignore_abstract=False):
        """
        This function attempts to find the object in the singleton cache. If not found, 
        delegates to _create_object in order to hunt for the definition, and request a
        object factory to generate one.
        """
        try:
            object_def = self.object_defs[name]
            if object_def.abstract and not ignore_abstract:
                raise AbstractObjectException("Object [%s] is an abstract one." % name)
                
            return self.objects[name]
            
        except KeyError, e:
            self.logger.debug("Did NOT find object '%s' in the singleton storage." % name)
            try:
                object_def = self.object_defs[name]
                if object_def.abstract and not ignore_abstract:
                    raise AbstractObjectException("Object [%s] is an abstract one." % name)
                
                comp = self._create_object(object_def)
                
                # Evaluate any scopes, and store appropriately.
                if self.object_defs[name].scope == scope.SINGLETON:
                    self.objects[name] = comp
                    self.logger.debug("Stored object '%s' in container's singleton storage" % name)
                elif self.object_defs[name].scope == scope.PROTOTYPE:
                    pass
                else:
                    raise InvalidObjectScope("Don't know how to handle scope %s" % self.object_defs[name].scope)
                
                return comp
            except KeyError, e:
                self.logger.error("Object '%s' has no definition!" % name)
                raise e
            
    def _get_constructors_pos(self, object_def):
        """
        This function iterates over the positional constructors, and assembles their values into a list.
        In this situation, the order as read from the XML should be the order expected by the class
        definition.
        """
        return tuple([constr.get_value(self) for constr in object_def.pos_constr
                      if hasattr(constr, "get_value")])

    def _get_constructors_kw(self, kwargs):
        """
        This function iterates over the named constructors, and assembles their values into a list.
        In this situation, each argument is associated with a name, and due to unicode format provided
        by the XML parser, requires conversion into a new dictionary.
        """
        return dict([(key, kwargs[key].get_value(self)) for key in kwargs
                     if hasattr(kwargs[key], "get_value")])


    def _create_object(self, object_def):
        """
        If the object isn't stored in any scoped cache, and must instead be created, this method
        takes all the steps to read the object's definition, res it up, and store it in the appropriate
        scoped cache.
        """
        self.logger.debug("Creating an instance of %s" % object_def)
        
        [constr.prefetch(self) for constr in object_def.pos_constr if hasattr(constr, "prefetch")]
        [constr.prefetch(self) for constr in object_def.named_constr.values() if hasattr(constr, "prefetch")]
        [prop.prefetch(self) for prop in object_def.props if hasattr(prop, "prefetch")]
        
        # Res up an instance of the object, with ONLY constructor-based properties set.
        obj = object_def.factory.create_object(self._get_constructors_pos(object_def),
                                               self._get_constructors_kw(object_def.named_constr))

        # Fill in the other property values.
        [prop.set_value(obj, self) for prop in object_def.props if hasattr(prop, "set_value")]
        
        return obj
        
        
class AbstractObjectException(Exception):
    """ Raised when the user's code tries to get an abstract object from
    the container.
    """
    
class InvalidObjectScope(Exception):
    pass
