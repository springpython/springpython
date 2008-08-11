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
     