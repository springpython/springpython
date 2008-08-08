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

import cherrypy
import logging
import os
import re
from cherrypy._cpwsgi import wsgiApp
from cherrypy._cpwsgiserver import CherryPyWSGIServer
from cherrypy._cpserver import Server
from springpython.context import XmlApplicationContext
from springpython.security.context import SecurityContext
from springpython.security.context import SecurityContextHolder

class WSGIServerWithMiddleware(object):
    def __init__(self, middleware):
        self.middleware = middleware
    def __call__(self):
        return CherryPyWSGIServer(("", 8001), self.middleware[0])

class MiddlewareServer(Server):
    def start(self, middleware):
        Server.start(self, initOnly=False, serverClass=WSGIServerWithMiddleware(middleware))

if __name__ == '__main__':
    """This allows the script to be run as a tiny webserver, allowing quick testing and development.
    For more scalable performance, integration with Apache web server would be a good choice."""

    logger = logging.getLogger("springpython")
    loggingLevel = logging.DEBUG
    logger.setLevel(loggingLevel)
    ch = logging.StreamHandler()
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s") 
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # This sample loads the IoC container from an XML file. The XML-based application context
    # automatically resolves all dependencies and order of instantiation for you. 

    applicationContext = XmlApplicationContext(configLocation = "applicationContext.xml")

    # Everything below is identical between petclinic.py and petclinic-noxml.py
    
    SecurityContextHolder.setStrategy(SecurityContextHolder.MODE_THREADLOCAL)

    # CherryPy always starts with cherrypy.root when trying to map request URIs
    # to objects. In this case, it is being assigned an object that was created in the
    # IoC container, allowing the web server components to be totally decoupled from the
    # view component.
    cherrypy.root = applicationContext.getComponent(componentId = "root")
    cherrypy.root.login = applicationContext.getComponent(componentId = "loginForm")

    cherrypy.server = MiddlewareServer()

    # Configure cherrypy programmatically.
    cherrypy.config.update({
                            "global": {
                                       "server.socket_port": 8001
                            },
                            "/": {
                                  "static_filter.root": os.getcwd()
                            },
                            "/images": {
                                "static_filter.on": True,
                                "static_filter.dir": "images"
                            },
                            "/html": {
                                "static_filter.on": True,
                                "static_filter.dir": "html"
                            },
                            "/styles": {
                                "static_filter.on": True,
                                "static_filter.dir": "css"
                            },
                            "/scripts": {
                                "static_filter.on": True,
                                "static_filter.dir": "js"
                            },
                            "/login/images": {
                                "static_filter.on": True,
                                "static_filter.dir": "images"
                            }
                        })

    middleware = applicationContext.getComponent(componentId = "filterChainProxy")
    middleware.application = wsgiApp
    
    # Start the CherryPy server.
    cherrypy.server.start(middleware=[middleware])

