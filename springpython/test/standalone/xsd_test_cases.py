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

# stdlib
import glob
import logging
import unittest

# lxml
from lxml import etree
from lxml import objectify

logger = logging.getLogger("springpythontest.xsd_test_cases")

class XSDTestCase(unittest.TestCase):
    """Verifies whether the XMLConfig files used for the tests themselves
    are valid according to the appropriate Spring Python's XSD schema."""
    
    NS_10 = "http://www.springframework.org/springpython/schema/objects"
    NS_11 = "http://www.springframework.org/springpython/schema/objects/1.1"
    
    def _get_schema(self, version):
        schema_file = open("../../xml/schema/context/spring-python-context-%s.xsd" % version)
        schema = etree.XMLSchema(etree.parse(schema_file))
        schema_file.close()
        
        return schema
    
    def setUp(self):
        self.schema10 = self._get_schema("1.0")
        self.schema11 = self._get_schema("1.1")
        
    def test_xsd(self):
        xmls = glob.glob("../springpythontest/support/*.xml")
        
        if not xmls:
            self.fail("No XMLs found")
        
        for xml in xmls:
            doc = objectify.fromstring(open(xml).read())
            xmlns = doc.nsmap[None]
            
            # XSD v. 1.0
            if xmlns == self.NS_10:
                schema = self.schema10
                
            # XSD v. 1.1
            elif xmlns == self.NS_11:
                schema = self.schema11
                
            # Ignore any other XML files
            else:
                continue
            
            try:
                schema.assert_(doc)
            except Exception, e:
                logging.error("Exception in assert_, xml=[%s] e=[%s]" % (xml, e))
                raise
                
if __name__ == "__main__":
    import logging

    loggingLevel = logging.DEBUG
    logger.setLevel(loggingLevel)
    ch = logging.StreamHandler()
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    unittest.main()
