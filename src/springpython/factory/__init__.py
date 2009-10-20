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
import sys

class ObjectFactory(object):
    def create_object(self, constr, named_constr):
        raise NotImplementedError()

class ReflectiveObjectFactory(ObjectFactory):
    def __init__(self, module_and_class):
        self.logger = logging.getLogger("springpython.factory.ReflectiveObjectFactory")
        self.module_and_class = module_and_class

    def create_object(self, constr, named_constr):
        self.logger.debug("Creating an instance of %s" % self.module_and_class)
        parts = self.module_and_class.split(".")
        module_name = ".".join(parts[:-1])
        class_name = parts[-1]
        if module_name == "":
            return __import__(class_name)(*constr, **named_constr)
        else:
            __import__(module_name)
            cls = getattr(sys.modules[module_name], class_name)
            return cls(*constr, **named_constr)


    def __str__(self):
        return "ReflectiveObjectFactory(%s)" % self.module_and_class

class PythonObjectFactory(ObjectFactory):
    def __init__(self, method, wrapper):
        self.logger = logging.getLogger("springpython.factory.PythonObjectFactory")
        self.method = method
        self.wrapper = wrapper

    def create_object(self, constr, named_constr):
        self.logger.debug("Creating an instance of %s" % self.method.func_name)
        
        # Setting wrapper's top_func can NOT be done earlier than this method call,
        # because it is tied to a wrapper decorator, which may not have yet been
        # generated.
        self.wrapper.func_globals["top_func"] = self.method.func_name
        
        # Because @object-based objects use direct code to specify arguments, and NOT
        # external configuration data, this factory doesn't care about the incoming arguments.
        
        return self.method()

    def __str__(self):
        return "PythonObjectFactory(%s)" % self.method
