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

import cherrypy
import logging
import os
import noxml
from springpython.security.context import SecurityContextHolder

if __name__ == '__main__':
    """This allows the script to be run as a tiny webserver, allowing quick testing and development.
    For more scalable performance, integration with Apache web server would be a good choice."""

    # This turns on debugging, so you can see everything Spring Python is doing in the background
    # while executing the sample application.

    logger = logging.getLogger("springpython")
    loggingLevel = logging.DEBUG
    logger.setLevel(loggingLevel)
    ch = logging.StreamHandler()
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s") 
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # This sample is just like petclinic-xml.py, only the wiring and order of dependency is resolved through decorators
    # and function calls. All the core pieces work just the same and are reusable, giving
    # you the flexibility and freedom to code it as you want.

    applicationContext = noxml.PetClinicClientAndServer()
    
    # Everything below is identical between petclinic.py and petclinic-noxml.py
    
    SecurityContextHolder.setStrategy(SecurityContextHolder.MODE_THREADLOCAL)
    
    #cherrypy.server = MiddlewareServer()
    
    cherrypy.config.update({
                            "global": {
                                "server.socket_port": 8001,
                                "tools.staticdir.root": os.getcwd(),
                                "wsgi.pipeline": [applicationContext.getComponent(componentId = "filterChainProxy")],
                                "tools.wsgiapp.on": True,
                                "tools.wsgiapp.app": applicationContext.getComponent(componentId = "filterChainProxy")
                             }
                            })
 
    cherrypy.tree.mount(applicationContext.getComponent(componentId = "root"), config = {
                            "/images": {
                                "tools.staticdir.on" : True,
                                "tools.staticdir.dir": "images"
                            },
                            "/html": {
                                "tools.staticdir.on" : True,
                                "tools.staticdir.dir": "html"
                            }
                        })
                        
    cherrypy.tree.mount(applicationContext.getComponent(componentId = "loginForm"), "/login", config = {
                            "/images": {
                                "tools.staticdir.on" : True,
                                "tools.staticdir.dir": "images"
                            }
                        })
                        
    cherrypy.quickstart()

