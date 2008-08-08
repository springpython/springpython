"""
    Copyright 2007 Greg L. Turnquist, All Rights Reserved

    This file is part of "Spring Wiki".
    
    "Spring Wiki" is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import cherrypy
import re
from model import ActionCompletedPage
from model import Page
from model import PreviewEditPage

def forward(url):
    return '<META HTTP-EQUIV="Refresh" CONTENT="0; URL=' + url + '">'

class Springwiki(object):
    """Render a RESTful wiki article for display."""

    def __init__(self, controller = None):
        """Inject a controller object in order to fetch live data."""
        self.controller = controller

    @cherrypy.expose
    def index(self, article = "Main Page"):
        if article:
            return self.default(article)
        
    def addRawWikitext(self, page):
        return "<p><p> <h1>Original Wikitext</h1>" + re.sub("\n", "<br>", page.wikitext)
    
    @cherrypy.expose
    def default(self, article, oldid=None):
        page = self.controller.getPage(article, oldid)
        return page.html()
    
    def addRawWikitext(self, page):
        return "<p><p> <h1>Original Wikitext</h1>" + re.sub("\n", "<br>", page.wikitext)
    
    @cherrypy.expose
    def submit(self, article, wpTextbox1 = None, wpSummary = None, wpSave = None, wpMinorEdit = False,
               wpPreview = None, wpDiff = None, wpMinoredit = False):
        
        if wpSave:
            self.controller.updatePage(article, wpTextbox1, wpSummary, wpMinorEdit)
        
        if wpPreview:
            return PreviewEditPage(article, wpTextbox1, self.controller).html()

        return forward("/" + article)
    
    @cherrypy.expose
    def edit(self, article):
        page = self.controller.getEditPage(article)
        return page.html()
    
    @cherrypy.expose
    def history(self, article):
        page = self.controller.getHistory(article)
        return page.html()
    
    @cherrypy.expose
    def delete(self, article):
        page = self.controller.getDeletePage(article)
        return page.html()
    
    @cherrypy.expose
    def doDelete(self, article, wpReason = None, wpConfirmB = None):
        if wpConfirmB == "Confirm":
            self.controller.deletePage(article, wpReason)
            return forward("/actionCompleted?article=%s" % article)
            
    @cherrypy.expose
    def actionCompleted(self, article):
        page = self.controller.getActionCompletedPage(article)
        return page.html()
    
    @cherrypy.expose
    def special(self, specialPage, article = None):
        return "Special page " + specialPage + " doesn't exist yet."
     