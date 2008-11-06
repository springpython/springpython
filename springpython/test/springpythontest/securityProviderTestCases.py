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

class InMemoryDaoAuthenticationProviderTestCase(unittest.TestCase):
    def setUp(self):
        SecurityContextHolder.setContext(SecurityContext())
        self.appContext = ApplicationContext(XMLConfig("support/providerApplicationContext.xml"))
        self.auth_manager = self.appContext.get_object("inMemoryDaoAuthenticationManager")
        
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.logger = logging.getLogger("springpythontest.providerTestCases.InMemoryDaoAuthenticationProviderTestCase")

    def testIoCDaoAuthenticationGoodUsers(self):                
        authentication = UsernamePasswordAuthenticationToken(username="user1", password="password1")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.granted_auths)
        self.assertTrue("blue" in SecurityContextHolder.getContext().authentication.granted_auths)
        
        authentication = UsernamePasswordAuthenticationToken(username="user2", password="password2")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.granted_auths)
        self.assertTrue("orange" in SecurityContextHolder.getContext().authentication.granted_auths)

        authentication = UsernamePasswordAuthenticationToken(username="adminuser", password="password3")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.granted_auths)
        self.assertTrue("admin" in SecurityContextHolder.getContext().authentication.granted_auths)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptions(self):
        authentication = UsernamePasswordAuthenticationToken(username="nonexistent", password="password999")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password="password4")
        self.assertRaises(DisabledException, self.auth_manager.authenticate, authentication)

        authentication = UsernamePasswordAuthenticationToken(username="emptyuser", password="")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

class DaoAuthenticationProviderHidingUserNotFoundExceptionsTestCase(MockTestCase):
    def __init__(self, methodName='runTest'):
        MockTestCase.__init__(self, methodName)
        self.logger = logging.getLogger("springpythontest.providerTestCases.DaoAuthenticationProviderHidingUserNotFoundExceptionsTestCase")

    def setUp(self):
        SecurityContextHolder.setContext(SecurityContext())
        self.appContext = ApplicationContext(XMLConfig("support/providerApplicationContext.xml"))
        self.auth_manager = self.appContext.get_object("dao_mgr_hiding_exception")
        self.mock = self.mock()
        self.appContext.get_object("dataSource").stubConnection.mockCursor = self.mock
        
    def testIoCDaoAuthenticationActiveUserBadPassword(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('activeuser', 'correctpassword', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('activeuser', 'role1')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="activeuser", password="wrongpassword")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)
        
    def testIoCDaoAuthenticationDisabledUserBadPassword(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('disabled', 'correctpassword', False)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('disabled', 'role1')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="disabled", password="wrongpassword")
        self.assertRaises(DisabledException, self.auth_manager.authenticate, authentication)
        
    def testIoCDaoAuthenticationGoodUser1(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('user1', 'password1', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('user1', 'role1'), ('user1', 'blue')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="user1", password="password1")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.granted_auths)
        self.assertTrue("blue" in SecurityContextHolder.getContext().authentication.granted_auths)

    def testIoCDaoAuthenticationGoodUser2(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('user2', 'password2', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('user2', 'role1'), ('user2', 'orange')])).id("#4").after("#3")
        
        authentication = UsernamePasswordAuthenticationToken(username="user2", password="password2")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.granted_auths)
        self.assertTrue("orange" in SecurityContextHolder.getContext().authentication.granted_auths)

    def testIoCDaoAuthenticationGoodAdminUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('adminuser', 'password3', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('adminuser', 'role1'), ('adminuser', 'admin')])).id("#4").after("#3")
        
        authentication = UsernamePasswordAuthenticationToken(username="adminuser", password="password3")
        SecurityContextHolder.getContext().authentication = self.auth_manager.authenticate(authentication)
        
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.granted_auths)
        self.assertTrue("admin" in SecurityContextHolder.getContext().authentication.granted_auths)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptionsNonexistentUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([])).id("#2").after("#1")

        authentication = UsernamePasswordAuthenticationToken(username="nonexistent", password="password999")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptionsDisabledUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'password4', False)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'role1'), ('disableduser', 'blue')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password="password4")
        self.assertRaises(DisabledException, self.auth_manager.authenticate, authentication)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptionsEmptyUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('emptyuser', '', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="emptyuser", password="")
        self.assertRaises(BadCredentialsException, self.auth_manager.authenticate, authentication)

class DaoAuthenticationProviderNotHidingUserNotFoundExceptionsTestCase(MockTestCase):
    def __init__(self, methodName='runTest'):
        MockTestCase.__init__(self, methodName)
        self.logger = logging.getLogger("springpythontest.providerTestCases.DaoAuthenticationProviderNotHidingUserNotFoundExceptionsTestCase")

    def setUp(self):
        SecurityContextHolder.setContext(SecurityContext())
        self.appContext = ApplicationContext(XMLConfig("support/providerApplicationContext.xml"))
        self.auth_manager = self.appContext.get_object("dao_mgr_not_hiding_exceptions")
        self.mock = self.mock()
        self.appContext.get_object("dataSource").stubConnection.mockCursor = self.mock
        
    def testIocDaoAuthenticationBadUsersDontHideBadCredentialsDisabledUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'password4', False)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'role1'), ('disableduser', 'blue')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password="password4")
        self.assertRaises(DisabledException, self.auth_manager.authenticate, authentication)

    def testIocDaoAuthenticationBadUsersDontHideBadCredentialsEmptyUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('emptyuser', '', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="emptyuser", password="")
        self.assertRaises(UsernameNotFoundException, self.auth_manager.authenticate, authentication)
