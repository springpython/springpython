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
import logging
from springpython.security.context import SecurityContextHolder

logger = logging.getLogger("springpython.test.support")

class SampleBlockOfData:
    def __init__(self, data):
        self.data = data
    def getLabel(self):
        return self.data

class SampleService:
    def __init__(self):
        self.logger = logging.getLogger("springpython.test.support.SampleService")

    def method(self, data):
        return "You made it!"
    
    def doSomethingOnThis(self, block1, block2):
        self.logger.debug("You made it! Your context is %s" % SecurityContextHolder.getContext().authentication)
        return "You made it!"

    def getTheSampleData(self):
        return [SampleBlockOfData("blue"), 
                SampleBlockOfData("orange"), 
                SampleBlockOfData("blue-orange")]


    def updateData(self, data):
        pass

