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
from springpython.security import SecurityException
from springpython.security.context import ThreadLocalSecurityContextHolderStrategy
from springpython.security.context import GlobalSecurityContextHolderStrategy

"""
This represents a static object that holds the context of the current session.
"""

# Currently supported strategies
MODE_THREADLOCAL = "THREADLOCAL"
MODE_GLOBAL = "GLOBAL"

# Local settings used to track strategy configuration
settings = {"strategyName" : MODE_GLOBAL, "strategy" : None, "initialized" : False }

def initialize():
    global settings

    if settings["strategyName"] == MODE_THREADLOCAL:
        settings["strategy"] = ThreadLocalSecurityContextHolderStrategy()
    elif settings["strategyName"] == MODE_GLOBAL:
        settings["strategy"] = GlobalSecurityContextHolderStrategy()
    else:
        raise SecurityException("We don't support strategy type %s" % settings["strategyName"])

    settings["initialized"] = True

def setStrategy(newStrategyName):
    global settings
    settings["strategyName"] = newStrategyName
    initialize()

def clearContext():
    if not settings["initialized"]:
        initialize()
    settings["strategy"].clearContext()

def getContext():
    """Retrieve the context, based on the strategy."""
    if not settings["initialized"]:
        initialize()
    return settings["strategy"].getContext()

def setContext(context):
    """Store the context, based on the strategy."""
    if not settings["initialized"]:
        initialize()
    settings["strategy"].setContext(context)
