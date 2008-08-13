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
import difflib
import time
from model import ActionCompletedPage
from model import DeletePage
from model import EditPage
from model import HistoryPage
from model import NoPage
from model import OldPage
from model import Page

wikiDatabase = {
    "Main Page":["""
Welcome to [[Spring Wiki]]. You can see more rendered wiki at [[Greg's Page]].

== Level 2 Header ==
This is a demonstration of [http://springpython.webfactional.com Spring Python].

=== Level 3 Header ===
What do you think?

==== Level 4 Header ====
Personally, I think this is cool. This is a wiki engine that uses the same wiki-text as [http://en.wikipedia.org Wikipedia].

There are many features:
* You can make intrawiki links
* You can make interwiki links
* You can make bullet lists
** And even sublists

# You can also make numbered lists.
## Sub-numbered lists.
# This is useful if you want to plug a wiki into your Python application

* You can 
*# Mix lists
*# With bullets and numbered
* As well

===== Level 5 Header =====
By using Python, you get:
* Fast development.
* Spring Python helps you cut more corners.
* And finally, [[CherryPy]] finishes it up by offering lightning fast web development time.
    """, [("Original", "This is the initial entry", "20:02, 6 October 2006", "User:Gregturn"), ("First edit", "This is an edit", "20:12, 12 October 2006", "User:Gregturn")]],
    "Spring Wiki":["""Spring Wiki is a demonstration application that shows how to write a wiki engine using Spring Python and [[CherryPy]].""", []],
    "CherryPy":["""[http://www.cherrypy.org CherryPy] is a web application framework.""", []],
    "Springwiki Sidebar": ["""
Single-star entries define boxes in the sidebar. Double-star boxes define the links listed underneath the boxes.

* Navigation
** [[Main Page]]
** [[Springwiki Sidebar|Edit the sidebar]]
* Spring Python
** [[Spring Wiki]]
** [http://springpython.webfactional.com Spring Python]
""", [("Original", "This is the initial entry", "20:02, 6 October 2006", "User:Gregturn")]]
    }

class SpringWikiController(object):
    def getPage(self, article, oldid=None):
        global wikiDatabase
        if article not in wikiDatabase:
            return NoPage(article=article, controller=self)

        if oldid:
            return OldPage(article=article, wikitext=wikiDatabase[article][1][int(oldid)][0], controller=self)
        
        return Page(article=article, wikitext=wikiDatabase[article][0], controller=self)
        
    def getEditPage(self, article):
        global wikiDatabase
        try:
            return EditPage(article=article, wikitext=wikiDatabase[article][0], controller=self)
        except KeyError:
            return EditPage(article=article, wikitext="", controller=self)
        
    def getHistory(self, article):
        global wikiDatabase
        return HistoryPage(article=article, controller=self, history=wikiDatabase[article][1])
        
    def exists(self, article):
        if article in wikiDatabase:
            return True
        else:
            return False
    
    def updatePage(self, article, wikitext, summary, minorEdit):
        global wikiDatabase
        try:
            wikiDatabase[article][1].append((wikiDatabase[article][0], summary, time.strftime("%H:%M:%S %d %b %Y", time.localtime()), ""))
            wikiDatabase[article][0] = wikitext
        except:
            wikiDatabase[article] = [None, None]
            wikiDatabase[article][0] = wikitext
            wikiDatabase[article][1] = [(wikitext, summary, time.strftime("%H:%M:%S %d %b %Y", time.localtime()), "")]
    
    def getDeletePage(self, article):
        return DeletePage(article=article, controller=self)
    
    def deletePage(self, article, reason):
        global wikiDatabase
        try:
            del wikiDatabase[article]
        except:
            pass
        
    def getActionCompletedPage(self, article):
        return ActionCompletedPage(article, self)
    