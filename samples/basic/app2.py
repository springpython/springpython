# -*- coding: utf-8 -*-
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

"""
NOTE: This is a test application being used to help migrate Spring Python 
to support CherryPy version 3.1. Hopefully, it will become a standard part
of the application samples.
"""

import cherrypy

from springpython.security.providers import AuthenticationManager
from springpython.security.providers.dao import DaoAuthenticationProvider
from springpython.security.userdetails import InMemoryUserDetailsService
from springpython.security.cherrypy31 import AuthenticationFilter, ContextSessionFilter, SecurityFilter
from springpython.security.context import SecurityContextHolder, SecurityContext

def initialize_spring():
    # Global is probably not a very good idea...
    SecurityContextHolder.setStrategy(SecurityContextHolder.MODE_GLOBAL)
    SecurityContextHolder.getContext()

def filter_chainer(filters):
    for f in filters:
        f.run()

def make_session_filter():
    contextSessionFilter = ContextSessionFilter()
    cherrypy.tools.sessionFilter = cherrypy.Tool('before_handler', filter_chainer, priority=74)
    return contextSessionFilter

def make_auth_manager():
    userDetailsService = InMemoryUserDetailsService({"admin": ("test", ["ADMIN"], True)})
    return AuthenticationManager([DaoAuthenticationProvider(userDetailsService)])

def make_authentication_filter(manager):
    authFilter = AuthenticationFilter(authManager=manager)
    cherrypy.tools.authFilter = cherrypy.Tool('before_handler', filter_chainer, priority=75)
    return authFilter

def make_security_filter(manager):
    securityFilter = SecurityFilter(authManager=manager)
    cherrypy.tools.securityFilter = cherrypy.Tool('before_handler', filter_chainer, priority=75)
    return securityFilter

initialize_spring()

manager = make_auth_manager()

session_filter = make_session_filter()
auth_filter = make_authentication_filter(manager)
security_filter = make_security_filter(manager)


def filterProxyChainer(filters):
    def outter(func):
        def inner(*args, **kwargs):
            for f in filters:
                f.run()
            return func(*args, **kwargs)
        return inner
    return outter
    

class BasicApplication(object):

    @cherrypy.expose
    def index(self):
        return """<html>
<head><title>Basic Spring Python demo</title></head>
<body>
Hello there. Please login below:
<form action="/login" method="post">
<label for="username">Username:</label>
<input type="text" name="username" id="username" />
<label for="password">Password:</label>
<input type="password" name="password" id="password" />
<input type="submit" />
</form>
</body>
</html>"""

    @cherrypy.expose
    @filterProxyChainer(filters=[session_filter, auth_filter])
    def login(self, username, password):
        # if we got here it means we are authenticated
        raise cherrypy.HTTPRedirect('/admin')

class AdminApplication(object):
    @cherrypy.expose
    @filterProxyChainer(filters=[session_filter, security_filter])
    def index(self):
        return "You are in a restricted area."

if __name__ == '__main__':
    conf = {'/': {'tools.sessions.on': True,}}
    admin_conf = {'/': {'tools.sessions.on': True}}
    
    cherrypy.tree.mount(BasicApplication(), '/', config=conf)
    cherrypy.tree.mount(AdminApplication(), '/admin', config=admin_conf)

    cherrypy.engine.start()
    cherrypy.engine.block()
    
