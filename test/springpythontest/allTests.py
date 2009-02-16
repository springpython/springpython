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
import unittest, os
import springpython
import sys

if __name__ == "__main__":    
    module_name = sys.argv[1]
    print "Trying to import module %s" % module_name
    mod = __import__("%s" % module_name)

    print mod

    logger = logging.getLogger("springpython")
    loggingLevel = logging.INFO
    logger.setLevel(loggingLevel)
    ch = logging.StreamHandler()
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s") 
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(mod))
    unittest.TextTestRunner(verbosity=3).run(suite)
