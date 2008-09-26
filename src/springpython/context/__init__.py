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
import inspect
import logging
import types
from springpython.context import scope
from springpython.context.decorator import decorator
from springpython.context.pycontainer import PyContainer

class InvalidConfigLocation(Exception):
    pass

class InvalidComponentScope(Exception):
    pass

class ApplicationContext(object):
    """
    ApplicationContext is a marker interface, used to identify constructs
    that can serve the role as an IoC container.
    """
    def get_component(self, componentId):
        """Abstract interface method"""
        raise NotImplementedError()


# This cache stored singletons on a per-context basis. Each context is a sub-dictionary, which each sub-entry
# based on function name.
singletonCache = {}

def component(theScope = scope.SINGLETON):
    """
    This function is a wrapper around the real decorator. It decides, based on scope
    and lazy-init, which decorator to return.
    Default scope is SINGLETON.
    """
    componentLogger = logging.getLogger("springpython.context.component")
    
    @decorator
    def componentPrototype(f, *args, **kwargs):
        """
        This is basically a pass through, because everytime a prototype function
        is called, there should be no caching of results.
        
        Using the @decorator library greatly simplifies the implementation of this.
        """
        return f(*args, **kwargs)

    @decorator
    def componentSingleton(f, *args, **kwargs):
        """
        This function uses the incoming stringified arguments as a contextual key to
        fetching/storing cached results based on function name.
        
        Using the @decorator library greatly simplifies the implemention of this.
        """
        results = None
        componentSingletonLogger = logging.getLogger("springpython.context.componentSingleton")
        try:
            results = singletonCache[args][f.func_name]
            componentSingletonLogger.debug("Found %s in singleton cache" % f.func_name)
        except KeyError:
            results = f(*args, **kwargs)
            try:
                singletonCache[args][f.func_name] = results
                componentSingletonLogger.debug("Adding %s in singleton cache" % f.func_name)
            except KeyError:
                singletonCache[args] = {f.func_name: results}
                componentSingletonLogger.debug("Creating context to store %s in singleton cache" % f.func_name)
        return results

    logging.getLogger("springpython.context.component").debug("The component decorator was just called with scope = %s" % theScope)
    if type(theScope) == types.FunctionType:
        return component()(theScope)
    elif theScope == scope.SINGLETON:
        return componentSingleton
    elif theScope == scope.PROTOTYPE:
        return componentPrototype
    else:
        raise InvalidComponentScope("Don't know how to handle scope %s" % theScope)
        
class ComponentNotFound(Exception):
    pass

class DecoratorBasedApplicationContext(ApplicationContext):
    def __init__(self):
        self.logger = logging.getLogger("springpython.context.DecoratorBasedApplicationContext")
        self.components = []

        # Grab all the components that 
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name not in decoratorBasedApplicationContextMethods:
                self.logger.debug("Eagerly fetching %s" % name)
                self.components.append(self.get_component(name))

        # Scan for any post_process_after_initialization components
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name not in decoratorBasedApplicationContextMethods:
                component = method()
                if hasattr(component, "post_process_after_initialization"):
                    self.logger.debug("Component " + name + " appears to have post_process_after_initialization, so I'm calling it")
                    getattr(component, "post_process_after_initialization")(self)
        
    def get_component(self, componentId):
        return getattr(self, componentId)()

decoratorBasedApplicationContextMethods = [name for (name, method) in inspect.getmembers(DecoratorBasedApplicationContext, inspect.ismethod)]

class XmlApplicationContext(ApplicationContext):
    """
    The XmlApplicationContext is based on Spring's interface to the IoC container.
    Under the hood, it is using PyContainer, which is cited in the NOTICE file.
    PyContainer is contained in the subpackage "pycontainer", including its original
    license and credited authors.
    
    This works very similarly to Java's ClassPathXmlApplicationContext, except the
    term "component" is substituted everywhere Java uses the term "bean", which
    the one exception being this was an interface definition in Java. 
    """
    def __init__(self, configLocation):        
        self.__pyContainer = PyContainer(config = configLocation)
        self.componentIds = self.__pyContainer.descriptions.keys()
        for componentId in self.componentIds:
            component = self.get_component(componentId)
            if hasattr(component, "applicationContext"):
                component.applicationContext = self

            # In case this is wrapping a Pyro method, you can't call the method
            # directly, or it might try to forward the request to a remote software.
            if "post_process_after_initialization" in component.__dict__:
                print "Component " + componentId + " appears to have post_process_after_initialization, so I'm calling it"
                component.__dict__["post_process_after_initialization"]()

    def get_component(self, componentId):
        return self.__pyContainer.getInstance(componentId)

    def dispose(self):
        """This is usually not needed. However, sometimes using Pyro requires a forced shutdown of the IoC container."""
        del(self.__pyContainer)

class ApplicationContextAware(object):
    def __init__(self):
        self.applicationContext = None
        
class ComponentPostProcessor(object):
    def post_process_after_initialization(self):
        raise NotImplementedError()
    
class ComponentNameAutoProxyCreator(ApplicationContextAware, ComponentPostProcessor):
    """
    This component will iterate over a list of components, and automatically apply
    a list of advisors to every callable method. This is useful when default advice
    needs to be applied widely with minimal configuration.
    """
    def __init__(self, componentNames = [], interceptorNames = []):
        ApplicationContextAware.__init__(self)
        ComponentPostProcessor.__init__(self)
        self.componentNames = componentNames
        self.interceptorNames = interceptorNames
        

