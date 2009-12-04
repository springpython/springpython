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
from springpython.config import PyContainerConfig
from springpython.config import PythonConfig
from springpython.context import ApplicationContext
from springpython.security.context import SecurityContextHolder

port = 8003

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

    applicationContext = ApplicationContext(noxml.SpringWikiClientAndServer())
    filterChainProxy = applicationContext.get_object("filterChainProxy")

    SecurityContextHolder.setStrategy(SecurityContextHolder.MODE_GLOBAL)
    SecurityContextHolder.getContext()
    
    # Use a configuration file for server-specific settings.
    conf = {"/":                {"tools.staticdir.root": os.getcwd(),
                                 "tools.sessions.on": True,
                                 "tools.filterChainProxy.on": True},
            "/images":          {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "images"},
            "/html":            {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "html"},
            "/styles":          {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "css"},
            "/edit/images":     {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "images"},
            "/edit/html":       {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "html"},
            "/edit/styles":     {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "css"},
            "/history/images":  {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "images"},
            "/history/html":    {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "html"},
            "/history/styles":  {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "css"},
            "/delete/images":   {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "images"},
            "/delete/html":     {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "html"},
            "/delete/styles":   {"tools.staticdir.on": True,
                                 "tools.staticdir.dir": "css"}
            }

    cherrypy.config.update({'server.socket_port': port})

    app = applicationContext.get_object(name = "read")
    app.login = applicationContext.get_object(name = "loginForm")

    cherrypy.tree.mount(app, '/', config=conf)

    cherrypy.engine.start()
    cherrypy.engine.block()

