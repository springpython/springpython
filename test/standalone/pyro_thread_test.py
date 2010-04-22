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

########################################################################
# This is a stand-alone test, meaning it doesn't run well in automated
# scenarios. This script exposed bug http://jira.springframework.org/browse/SESPRINGPYTHONPY-99,
# which showed _PyroThread having a name collisions with python2.6's threading.Thread
# class. By renaming _PyroThread's self.daemon as self.pyro_daemon, this code
# now works with python2.6. It was also used to confirm python2.5, and jython2.5.1.FINAL.
########################################################################

from springpython.config import Object, PythonConfig
from springpython.remoting.pyro import PyroServiceExporter

class MySampleService(object):
    def hey(self):
        print "You have just called the sample service!"

class MySampleServiceAppContext(PythonConfig):
    def __init__(self):
        PythonConfig.__init__(self)

    @Object
    def mySampleService(self):
        return MySampleService()

    @Object
    def mySampleServiceExporter(self):
        return PyroServiceExporter(self.mySampleService(), "service", "localhost", 7000)

if __name__ == "__main__":
    import logging
    from springpython.context import ApplicationContext

    logger = logging.getLogger("springpython")
    loggingLevel = logging.DEBUG
    logger.setLevel(loggingLevel)
    ch = logging.StreamHandler()
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    print "Starting up context that exposese reported issue..."
    ctx = ApplicationContext(MySampleServiceAppContext()) 
