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
import os
import shutil
import subprocess
import unittest
from pmock import *
from springpython.config import XMLConfig
from springpython.context import ApplicationContext
from springpython.database.core import DatabaseTemplate
from springpython.security.providers import AuthenticationManager
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.context import SecurityContextHolder
from springpython.security.context import SecurityContext
from springpython.security import BadCredentialsException
from springpython.security import DisabledException
from springpython.security import UsernameNotFoundException
from springpythontest.support import testSupportClasses

class LdapAuthenticationProviderTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.logger = logging.getLogger("springpythontest.securityLdapTestCases.LdapAuthenticationProviderTestCase")

    def setUp(self):
        SecurityContextHolder.setContext(SecurityContext())
        self.appContext = ApplicationContext(XMLConfig("support/ldapApplicationContext.xml"))

    def testGoodUsersBindAuthentication(self):                
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider")

        authentication = UsernamePasswordAuthenticationToken(username="bob", password="bobspassword")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        self.assertTrue("ROLE_DEVELOPERS" in SecurityContextHolder.getContext().authentication.granted_auths)

    def testGoodUsersPasswordAuthentication(self):
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider2")

        authentication = UsernamePasswordAuthenticationToken(username="bob", password="bobspassword")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        self.assertTrue("ROLE_DEVELOPERS" in SecurityContextHolder.getContext().authentication.granted_auths)

    def testGoodUserWithShaEncoding(self):
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider2")

        authentication = UsernamePasswordAuthenticationToken(username="ben", password="benspassword")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        self.assertTrue("ROLE_DEVELOPERS" in SecurityContextHolder.getContext().authentication.granted_auths)

    def testWrongPasswordBindAuthentication(self):
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider")

        authentication = UsernamePasswordAuthenticationToken(username="bob", password="wrongpassword")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

    def testWrongPasswordAuthentication(self):
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider2")

        authentication = UsernamePasswordAuthenticationToken(username="bob", password="wrongpassword")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

    def testNonexistentUserBindAuthentication(self):
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider")

        authentication = UsernamePasswordAuthenticationToken(username="nonexistentuser", password="password")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

    def testNonexistentUserPasswordAuthentication(self):
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider2")

        authentication = UsernamePasswordAuthenticationToken(username="nonexistentuser", password="password")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

    def testEmptyPassword(self):
        self.auth_manager = self.appContext.get_object("ldapAuthenticationProvider")

        authentication = UsernamePasswordAuthenticationToken(username="nonexistentuser", password="")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)
