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
import traceback
from threading import RLock, currentThread

try:
    from cStringIO import StringIO
except ImportError, e:
    from StringIO import StringIO


TRACE1 = 6
logging.addLevelName(TRACE1, "TRACE1")

# Original code by Anand Balachandran Pillai (abpillai at gmail.com)
# http://code.activestate.com/recipes/533135/
class synchronized(object):
    """ Class enapsulating a lock and a function allowing it to be used as
    a synchronizing decorator making the wrapped function thread-safe """

    def __init__(self, *args):
        self.lock = RLock()
        self.logger = logging.getLogger("springpython.util.synchronized")

    def __call__(self, f):
        def lockedfunc(*args, **kwargs):
            try:
                self.lock.acquire()
                self.logger.log(TRACE1, "Acquired lock [%s] thread [%s]" % (self.lock, currentThread()))
                try:
                    return f(*args, **kwargs)
                except Exception, e:
                    raise
            finally:
                self.lock.release()
                self.logger.log(TRACE1, "Released lock [%s] thread [%s]" % (self.lock, currentThread()))
        return lockedfunc
