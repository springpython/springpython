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
import re
import types
from springpython.database.core import DatabaseTemplate
from springpython.security import AuthenticationException
from springpython.security.context import SecurityContext
from springpython.security.context import SecurityContextHolder
from springpython.security.providers import UsernamePasswordAuthenticationToken

def header():
    """Standard header used for all pages"""
    return """
        <!--
        
            PetClinic :: a Spring Python demonstration (powered by CherryPy)
        
        -->
        
        <html>
        <head>
        <title>PetClinic :: a Spring Python demonstration</title>
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
                <td style="text-align:right;color:silver">PetClinic :: a <a href="http://springpython.webfactional.com">Spring Python</a> demonstration (powered by <A HREF="http://www.cherrypy.org">CherryPy</A>)</td>
        </tr></table>
        </body>
        """
    
class PetClinicView(object):
    """Presentation layer of the web application."""

    def __init__(self, filter=None, controller = None, hashedUserDetailsServiceList = None, authenticationManager=None, redirectStrategy=None):
        self.filter = filter
        self.controller = controller
        self.hashedUserDetailsServiceList = hashedUserDetailsServiceList
        self.authenticationManager = authenticationManager
        self.redirectStrategy = redirectStrategy
	self.httpContextFilter = None
        self.logger = logging.getLogger("springpython.petclinic.view.PetClinicView")
        
    @cherrypy.expose
    def accessDenied(self):
        return header() + """
            <H2>Access Denied</H2>
            <P>
            <b>You have attempted to access a page which you are unauthorized to view.</b>
            """ + footer()
        
    @cherrypy.expose
    def index(self):
        """CherryPy will call this method for the root URI ("/") and send
        its return value to the client."""
        
        return header() + """
            <H2>Welcome</H2>
            <P>
            <A href="findOwners">Find owner</A>
            <P>
            <A href="vets">Display all veterinarians</A>
            <P>
            <A HREF="html/petclinic.html">Detailed description of this demo</A>
            <P>
            <a href="/logout">Logout</a>
            """ + footer()

    @cherrypy.expose
    def findOwners(self, lastName = ""):
        """Fetch owners by a partially matching against last name."""
        
        results = header() + """
            <P>
            <H2>Find Owners:</H2>
            <P>
            <FORM method="POST">
                <B>Last Name:</B>
                  <BR><INPUT type="text" maxlength="30" size="30" name="lastName" value="%s">
                <P>
              <INPUT type = "submit" value="Find Owners"/>
            </FORM>
            <P>
            <BR>
            """ % lastName
        if lastName != "":
            results += """
                <H2>Owners:</H2>
                <TABLE border="1">
                    <TH>Name</TH>
                    <TH>Address</TH>
                    <TH>City</TH>
                    <TH>Telephone</TH>
                """
            for owner in self.controller.getOwners(lastName):
                results += """
                    <TR>
                        <TD><A HREF="editOwner?id=%s">%s %s</A></TD>
                        <TD>%s</TD>
                        <TD>%s</TD>
                        <TD>%s</TD>
                    </TR>      
                    """ % (owner.id, owner.firstName, owner.lastName, owner.address, owner.city, owner.telephone)
            results += """
                </TABLE>
                <P>
                <BR>
                """
        results += """
            <A href="addOwner">Add Owner</A>
            <P>
            <BR>
            <a href="/logout">Logout</a>
            """ + footer()
        return results

    @cherrypy.expose
    def addOwner(self, **kwargs):
        """Insert a new owner into the database."""
        
        results = header()
        
        if len(kwargs) > 0:
            rowsAffected = self.controller.addOwner(**kwargs)
        else:
            rowsAffected = 0
            kwargs = { "firstName": "", "lastName": "", "address": "", "city": "", "telephone":"" }

        if rowsAffected > 0:
            results += "<H3>%s %s was successfully added.</H3>" % (kwargs["firstName"], kwargs["lastName"])
            
        results += """
            <P>
            <H2>New Owner:</H2>
            <P>
            <FORM method="GET" action="addOwner">
                <B>First Name:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="firstName" value="%s" >
                <P>
                
                <B>Last Name:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="lastName" value="%s" >
                <P>
    
                <B>Address:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="address" value="%s" >
                <P>
                
                <B>City:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="city" value="%s" >
                <P>
                
                <B>Telephone:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="telephone" value="%s" >
                <P>
                <INPUT type = "submit" value="Add Owner"/>
            </FORM>
            <P>
            <BR>
            <a href="/logout">Logout</a>
            """ % (kwargs["firstName"], kwargs["lastName"], kwargs["address"], kwargs["city"], kwargs["telephone"]) + footer()
        return results
    
    @cherrypy.expose
    def editOwner(self, id):
        """Update an existing owner"""
        owner = self.controller.getOwner(id)
        results = header() + """
            <P>
            <H2>Owner: %s %s</H2>
            <P>
            <FORM method="GET" action="doUpdateOwner">   
                <INPUT type="hidden" name="id" value="%s">
                <B>Address:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="address" value="%s" >
                <P>
                
                <B>City:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="city" value="%s" >
                <P>
                
                <B>Telephone:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="telephone" value="%s" >
                <P>
                <INPUT type = "submit" value="Update Owner"/>
            </FORM>
            <BR>
            <H2>Pets: </H2>
            <P>
            <TABLE border="1">
                <TH>Name</TH>
                <TH>Birth date</TH>
                <TH>Type</TH>
            """ % (owner.firstName, owner.lastName, owner.id, owner.address, owner.city, owner.telephone)
        for pet in self.controller.getPets(owner):
            results += """
                <TR>
                    <TD><A HREF="/vetHistory?ownerId=%s&petId=%s">%s</A></TD>
                    <TD>%s</TD>
                    <TD>%s</TD>
                </TR>
                """ % (owner.id, pet.id, pet.name, pet.birthDate, pet.type)
        results += """
            </TABLE>
            <P>
            <A href="addPet?id=%s">Add Pet</A>
            <P>
            <BR>
            <a href="/logout">Logout</a>
            """ % id + footer()
        return results
    
    @cherrypy.expose
    def doUpdateOwner(self, id, address = "", city = "", telephone = ""):
        owner = self.controller.updateOwner(id, address, city, telephone)
        return self.editOwner(id)
    
    @cherrypy.expose
    def addPet(self, id):
        types = self.controller.getPetTypes()
        results = header() + """
            <P>
            <H2>New Pet:</H2>
            <P>
            <FORM method="GET" action="doAddPet">
                <INPUT type="hidden" name="id" value="%s">
                <B>Name:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="name" value="" >
                <P>
                
                <B>Birth Date:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="birthDate" value="" >
                <P>
    
                <B>Type:</B>
                    <BR><select name="type">""" % id
                    
        for type in types:
            results += """
                            <option value="%s">%s</option>""" % (type.id, type.name)
            
        results += """
                        </select>
                <P>
                <INPUT type = "submit" value="Add Pet"/>
            </FORM>
            <A HREF="editOwner?id=%s">Back to Owner</A>
            <P>
            <BR>
            <a href="/logout">Logout</a>
            """ % id + footer()
        return results

    @cherrypy.expose
    def doAddPet(self, id, name = "", birthDate = "", type = ""):
        owner = self.controller.addPet(id, name, birthDate, type)
        return self.addPet(id)
    
    @cherrypy.expose
    def vetHistory(self, ownerId, petId):
        """Look up history of visits for a pet."""
        pet = self.controller.getPet(petId)
        
        results = header() + """
            <P>
            <H2>History of visits for %s:</H2>
            <TABLE border="1">
                <TH>Date</TH>
                <TH>Description</TH>

            """ % pet.name
        for visit in self.controller.getVisits(pet):
            results += """
                <TR>
                    <TD>%s</TD>
                    <TD>%s</TD>
                </TR>
                """ % (visit.date, visit.description)
        results += """
            </TABLE>
            <P>
            <A HREF="visitClinic?ownerId=%s&petId=%s&name=%s">Visit the Clinic</A>
            <P>
            <A HREF="editOwner?id=%s">Back to owner</A>
            <BR>
            <a href="/logout">Logout</a>
            """ % (ownerId, pet.id, pet.name, ownerId) + footer()
        return results

    @cherrypy.expose
    def visitClinic(self, ownerId, petId, name):
        """Look up history of visits for a pet."""
        results = header() + """
            <H2>New visit for %s:</H2>
            <FORM method="GET" action="doVisitClinic">
                <INPUT type="hidden" name="name" value="%s">
                <INPUT type="hidden" name="ownerId" value="%s">
                <INPUT type="hidden" name="petId" value="%s">
                <B>Name:</B>
                    <BR><INPUT type="text" maxlength="30" size="30" name="description" value="">
                <P>
                <INPUT type = "submit" value="Record Visit"/>
            </FORM>
            <P>
            <A HREF="vetHistory?ownerId=%s&petId=%s">Back to history of visits</A>
            <P>
            <a href="/logout">Logout</a>
            """ % (name, name, ownerId, petId, ownerId, petId) + footer()
        return results

    @cherrypy.expose
    def doVisitClinic(self, ownerId, petId, name, description = ""):
        owner = self.controller.visitClinic(petId, description)
        return self.visitClinic(ownerId, petId, name)

    @cherrypy.expose
    def vets(self):
        """Look up all the veterinarians."""
        
        results = header() + """
            <P>
            <H2>Veterinarians:</H2>
            <TABLE border="1">
                <TH>Name</TH>
                <TH>Specialties</TH>

            """
        for vet in self.controller.getVets():
            specialties = ",".join([specialty.name for specialty in self.controller.getVetSpecialties(vet)])
            results += """
                <TR>
                    <TD>%s %s</TD>
                    <TD>%s</TD>
                </TR>
                """ % (vet.firstName, vet.lastName, specialties)
        results += """
            </TABLE>
            <P>
            <BR>
            <a href="/logout">Logout</a>
            """ + footer()
        return results
      
    @cherrypy.expose
    def login(self, fromPage="/", login="", password="", errorMsg=""):
        if login != "" and password != "":
            try:
                self.attemptAuthentication(login, password)
                return [self.redirectStrategy.redirect(fromPage)]
            except AuthenticationException, e:
                return [self.redirectStrategy.redirect("?login=%s&errorMsg=Username/password failure" % login)]

        results = header() + """
            <html><body>
                %s
		    <p>
            <h4>Unhashed passwords - <small>The following table contains a set of accounts that are stored in the clear.</small></h4>
            <p>
            <table  border="1" cellspacing="0">
                <tr>
                    <th><small>Username</small></th>
                    <th><small>Password</small></th>
                    <th><small>Granted authorities</small></th>
                    <th><small>Enabled?</small></th>
                </tr>
        """ % errorMsg

        for (username, password, authorities, enabled) in self.controller.getUsers():
            results += """
                <tr>
                    <td><small>%s </small></td>
                    <td><small>%s </small></td>
                    <td><small>%s </small></td>
                    <td><small>%s </small></td>
                </tr>
            """ % (username, password, authorities, enabled)
            
        results += """
            </table>
        """

        # Display hard-coded, unhashed passwords. NOTE: These cannot be retrieved from
        # the application context, because they are one way hashes. This must be kept
        # in sync with the application context.
        results += """
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
