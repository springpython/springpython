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

TRACE1 = 6
logging.addLevelName(TRACE1, "TRACE1")

try:
    from cStringIO import StringIO
except ImportError, e:
    from StringIO import StringIO

def get_last_traceback(exception):
    """ A utility function for better displaying exceptions.
    """
    buff = StringIO()
    traceback.print_exc(file=buff)
    
    return buff.getvalue()
