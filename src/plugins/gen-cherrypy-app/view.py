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
import inspect
import logging
import re
from springpython.security import AuthenticationException
from springpython.security.context import SecurityContextHolder
from springpython.security.providers import UsernamePasswordAuthenticationToken

def header():
    """Standard header used for all pages"""
    return """
        <!--
        
            ${properName} Application :: A ${name} application-creating template
        
        -->
        
        <html>
        <head>
        <title>${properName} Application :: A ${name} application-creating template</title>
            <style type="text/css">
                    td { padding:3px; }
                    div#top {position:absolute; top: 0px; left: 0px; background-color: #E4EFF3; height: 50px; width:100%; padding:0px; border: none;margin: 0;}
                    div#image {position:absolute; top: 50px; right: 0%; background-image: url(images/spring_python_white.png); background-repeat: no-repeat; background-position: right; height: 100px; width:300px }
            </style>
        </head>
        
        <body>
            <div id="top">&nbsp;</div>
            <div id="image">&nbsp;</div>
            <br clear="all">
            <p>&nbsp;</p>
            <br/>
            <br/>
            <br/>
            <br/>
            """

def footer():
    """Standard footer used for all pages."""
    return """
        <hr>
        <table style="width:100%"><tr>
                <td><A href="/">Home</A></td>
                <td style="text-align:right;color:silver">${properName} Application :: A <a href="http://cherrypy.org">CherryPy</a>-based ${properName} application-creating template</td>
        </tr></table>
        </body>
        """
    
class ${properName}View(object):
    """Presentation layer of the web application."""

    def __init__(self):
        self.logger = logging.getLogger("${name}.${properName}App")
        
    @cherrypy.expose
    def index(self):
        """This is the root page for your ${name} app. Its default includes links to all other exposed
           links automatically."""

        return header() + """
            <H2>Welcome to ${properName}</H2>
            <P>""" + "".join(['<a href="%s">%s</a> - %s<p>\n' % (name, name, method.__doc__)
		for (name, method) in inspect.getmembers(self, inspect.ismethod)
		if hasattr(method, "exposed") and name != "index"]) + footer()

    @cherrypy.expose
    def admin(self):
	"""This page will provide some administrative functionality"""
        return self.under_dev()

    @cherrypy.expose
    def user_management(self):
        """Define users"""
        return self.under_dev()

    @cherrypy.expose
    def role_management(self):
        "Define roles"
        return self.under_dev()

    def under_dev(self):
        return header() + "This page is under development" + footer()

    @cherrypy.expose
    def login(self, fromPage="/", login="", password="", errorMsg=""):
        if login != "" and password != "":
            try:
                self.attemptAuthentication(login, password)
                return [self.redirectStrategy.redirect(fromPage)]
            except AuthenticationException, e:
                return [self.redirectStrategy.redirect("?login=%s&errorMsg=Username/password failure" % login)]

        # Display hard-coded, unhashed passwords. NOTE: These cannot be retrieved from
        # the application context, because they are one way hashes. This must be kept
        # in sync with the application context.
        results = header()

        results += self.demo_passwords()   # Remove this step to stop displaying sample users
            
        results += """
                <form method="POST" action="">
                    Login: <input type="text" name="login" value="%s" size="10"/><br/>
                    Password: <input type="password" name="password" size="10"/><br/>
                    <input type="hidden" name="fromPage" value="%s"/><br/>
                    <input type="submit"/>
                </form>
            </body></html>
        """ % (login, fromPage)
        results += footer()
        return [results]
    

    def demo_passwords(self):
        results = """
            <html><body>
            <h4>Hashed passwords - <small>The following tables contain accounts that are stored with one-way hashes.</small></h4>
            <p>
        """
        for hashedUserDetailsService in self.hashedUserDetailsServiceList:
            results += """
                <small>%s</small>
                <table  border="1" cellspacing="0">
                    <tr>
                        <th><small>Username</small></th>
                        <th><small>Password</small></th>
                        <th><small>Granted authorities</small></th>
                        <th><small>Enabled?</small></th>
                    </tr>
                """ % re.compile("<").sub("&lt;", str(hashedUserDetailsService))
            for key, value in hashedUserDetailsService.wrappedUserDetailsService.user_dict.items():
                    results += """
                    <tr>
                        <td><small>%s </small></td>
                        <td><small>%s </small></td>
                        <td><small>%s </small></td>
                        <td><small>%s </small></td>
                    </tr>
                """ % (key, value[0], value[1], value[2])
            results += """
                </table>
                <p>
            """
        return results

    @cherrypy.expose    
    def logout(self):
        """Replaces current authentication token, with an empty, non-authenticated one."""
        self.filter.logout()
	self.httpContextFilter.saveContext()
        raise cherrypy.HTTPRedirect("/")

    def attemptAuthentication(self, username, password):
        """Authenticate a new username/password pair using the authentication manager."""
        self.logger.debug("Trying to authenticate %s using the authentication manager" % username)
        token = UsernamePasswordAuthenticationToken(username, password)
        SecurityContextHolder.getContext().authentication = self.authenticationManager.authenticate(token)
	self.httpContextFilter.saveContext()
        self.logger.debug(SecurityContextHolder.getContext())


