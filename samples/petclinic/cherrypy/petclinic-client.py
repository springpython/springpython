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
import logging
import os
import cherrypy
import noxml
from cherrypy._cpwsgi import wsgiApp
from cherrypy._cpwsgiserver import CherryPyWSGIServer
from cherrypy._cpserver import Server

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

    applicationContext = noxml.PetClinicClientOnly()
    
    # CherryPy always starts with cherrypy.root when trying to map request URIs
    # to objects. In this case, it is being assigned an object that was created in the
    # IoC container, allowing the web server components to be totally decoupled from the
    # view component.
    cherrypy.root = applicationContext.getComponent(componentId = "view")
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
