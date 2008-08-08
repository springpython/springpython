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

import controller
import view
from springpython.context import DecoratorBasedApplicationContext
from springpython.context import component
from springpython.security.web import FilterChainProxy

class SpringWikiClientAndServer(DecoratorBasedApplicationContext):
    def __init__(self):
        DecoratorBasedApplicationContext.__init__(self)
        
    @component
    def read(self):
        wikiView = view.Springwiki()
        wikiView.controller = self.controller()
        return wikiView
    
    @component
    def controller(self):
        return controller.SpringWikiController()
    
    @component
    def filterChainProxy(self):
        proxy = FilterChainProxy()
        proxy.filterInvocationDefinitionSource = [("/.*", [])]
        return proxy
