"""
    Copyright 2006-2008 Greg L. Turnquist, All Rights Reserved
 
    This file is part of PetClinic.
 
    PetClinic is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
 
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
 
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
THIS IS A WORK IN PROGRESS. It probably does NOT work. This has been checked in to the
repository to allow collaboration between different locations and different developers.
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
    #logger.addHandler(ch)
 
    # This sample is just like petclinic-xml.py, only the wiring and order of dependency is resolved through decorators
    # and function calls. All the core pieces work just the same and are reusable, giving
    # you the flexibility and freedom to code it as you want.
 
    applicationContext = noxml.PetClinicClientAndServer()
 
    # Everything below is identical between petclinic.py and petclinic-noxml.py
 
    SecurityContextHolder.setStrategy(SecurityContextHolder.MODE_THREADLOCAL)
 
    class ApplicationContextWSGIWrapper(object):
        def __init__(self, nextapp):
            self.component = applicationContext.getComponent(componentId='filterChainProxy2')
            self.component.application = nextapp
 
        def __call__(self, environ, start_response):
            return self.component(environ, start_response)
 
    cherrypy.config.update({
                            "global": {
                                "server.socket_port": 8001,
                                "tools.staticdir.root": os.getcwd()
                                }
                            })
 
    rootApp = cherrypy.tree.mount(applicationContext.getComponent(componentId = "root"), "/", config = {
                            "/images": {
                                "tools.staticdir.on" : True,
                                "tools.staticdir.dir": "images"
                            },
                            "/html": {
                                "tools.staticdir.on" : True,
                                "tools.staticdir.dir": "html"
                            }
                        })
    rootApp.wsgiapp.pipeline.append(('filters', ApplicationContextWSGIWrapper))
 
    cherrypy.tree.mount(applicationContext.getComponent(componentId = "loginForm"), "/login", config = {
                            "/images": {
                                "tools.staticdir.on" : True,
                                "tools.staticdir.dir": "images"
                            }
                        })
 
    cherrypy.engine.start()
    cherrypy.engine.block()
