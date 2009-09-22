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

import atexit
import logging

from springpython.util import get_last_traceback
from springpython.container import ObjectContainer
from springpython.remoting.pyro import PyroProxyFactory

class ApplicationContext(ObjectContainer):
    """
    ApplicationContext IS a ObjectContainer. It also has the ability to define the lifecycle of
    objects.
    """
    def __init__(self, config = None):
        super(ApplicationContext, self).__init__(config)
        
        atexit.register(self.shutdown_hook)
        
        self.logger = logging.getLogger("springpython.context.ApplicationContext")
        self.types_to_avoid = [PyroProxyFactory]
        
        for object_def in self.object_defs.values():
            self._apply(object_def)
            
        for configuration in self.configs:
            self._apply(configuration)

        for object_def in self.object_defs.values():
            if not object_def.lazy_init and object_def.id not in self.objects:
                self.logger.debug("Eagerly fetching %s" % object_def.id)
                self.get_object(object_def.id)

        post_processors = [object for object in self.objects.values() if isinstance(object, ObjectPostProcessor)]

        for obj_name, obj in self.objects.iteritems():
            if not isinstance(obj, ObjectPostProcessor):
                for post_processor in post_processors:
                    self.objects[obj_name] = post_processor.post_process_before_initialization(obj, obj_name)


        for object in self.objects.values():
            self._apply(object)

        for obj_name, obj in self.objects.iteritems():
            if not isinstance(obj, ObjectPostProcessor):
                for post_processor in post_processors:
                    self.objects[obj_name] = post_processor.post_process_after_initialization(obj, obj_name)
            
    def _apply(self, obj):
        if len([True for type_to_avoid in self.types_to_avoid if isinstance(obj, type_to_avoid)]) == 0: 
            if hasattr(obj, "after_properties_set"):
               obj.after_properties_set()
            #if hasattr(obj, "post_process_after_initialization"):
            #    obj.post_process_after_initialization(self)
            if hasattr(obj, "set_app_context"):
                obj.set_app_context(self)
                
    def shutdown_hook(self):
        self.logger.debug("Invoking the destroy_method on registered objects")
        
        for obj_name, obj in self.objects.iteritems():
            if isinstance(obj, DisposableObject):
                try:
                    if hasattr(obj, "destroy_method"):
                        destroy_method_name = getattr(obj, "destroy_method")
                    else:
                        destroy_method_name = "destroy"
                        
                    destroy_method = getattr(obj, destroy_method_name)
                    
                except Exception, e:
                    self.logger.error("Could not destroy object '%s', exception '%s'" % (obj_name, get_last_traceback(e)))
                    
                else:
                    if callable(destroy_method):
                        try:
                            self.logger.debug("About to destroy object '%s'" % obj_name)
                            destroy_method()
                            self.logger.debug("Successfully destroyed object '%s'" % obj_name)
                        except Exception, e:
                            self.logger.error("Could not destroy object '%s', exception '%s'" % (obj_name, get_last_traceback(e)))
                    else:
                        self.logger.error("Could not destroy object '%s', " \
                            "the 'destroy_method' attribute it defines is not callable, " \
                            "its type is '%r', value is '%r'" % (obj_name, type(destroy_method), destroy_method))
                        
        self.logger.debug("Successfully invoked the destroy_method on registered objects")
            

class ObjectPostProcessor(object):
    def post_process_before_initialization(self, obj, obj_name):
        return obj
    def post_process_after_initialization(self, obj, obj_name):
        return obj

class ApplicationContextAware(object):
    def __init__(self):
        self.app_context = None
        
    def set_app_context(self, app_context):
        self.app_context = app_context

class ObjectNameAutoProxyCreator(ApplicationContextAware, ObjectPostProcessor):
    """
    This object will iterate over a list of objects, and automatically apply
    a list of advisors to every callable method. This is useful when default advice
    needs to be applied widely with minimal configuration.
    """
    def __init__(self, objectNames = [], interceptorNames = []):
        super(ObjectNameAutoProxyCreator, self).__init__()
        self.objectNames = objectNames
        self.interceptorNames = interceptorNames

class DisposableObject(object):
    """ This allows definition of a method which is invoked when the 
    container's shutting down to release the resources held by an object.
    """
    def destroy(self):
        raise NotImplementedError("Should be overridden by subclasses")
