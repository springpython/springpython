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
import os
import glob
import logging
import unittest

# minixsv
from minixsv import pyxsval

logger = logging.getLogger("springpythontest.xsd_test_cases")

def get_xml_wrapper(xml_file, xsd_file):
    validator = pyxsval.XsValidator()
    xml_wrapper = validator.parse(xml_file)
    
    return xml_wrapper

class _Validator(pyxsval.XsValidator):
    def __init__(self, *args, **kwargs):
        pyxsval.XsValidator.__init__(self)

    def validate(self, xml, xml_wrapper, xsd=None):
        xsd_wrapper = self.parse(xsd)
        self._validateXmlInput (xml, xml_wrapper, [xsd_wrapper])
        xsd_wrapper.unlink()

class XSDTestCase(unittest.TestCase):
    """Verifies whether the XMLConfig files used for the tests themselves
    are valid according to the appropriate Spring Python's XSD schema."""
    
    NS_10 = "http://www.springframework.org/springpython/schema/objects"
    NS_11 = "http://www.springframework.org/springpython/schema/objects/1.1"
    
    def _get_schema(self, version):
        return os.path.abspath("../../xml/schema/context/spring-python-context-%s.xsd" % version)
    
    def setUp(self):
        self.schema10 = self._get_schema("1.0")
        self.schema11 = self._get_schema("1.1")
        
    def test_xsd(self):
        
        xmls = glob.glob("./support/*.xml")
        for xml in xmls:
            
            xml_data = open(xml).read()
            
            # XSD v. 1.1
            if self.NS_11 in xml_data:
                schema = self.schema11
            
            # XSD v. 1.0
            elif self.NS_10 in xml_data:
                schema = self.schema10
                
            # Ignore any other XML files
            else:
                continue
            
            try:
                xml_wrapper = get_xml_wrapper(xml, schema)
                validator = _Validator()
                validator.validate(xml, xml_wrapper, schema)
            except Exception, e:
                logger.error("Exception caught during validation, xml=[%s], schema=[%s], e=[%s]" % (xml, schema, e))
                raise
