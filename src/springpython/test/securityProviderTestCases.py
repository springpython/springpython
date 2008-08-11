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
from springpython.context import XmlApplicationContext
from springpython.database.core import DatabaseTemplate
from springpython.security.providers import InMemoryAuthenticationProvider
from springpython.security.providers import AuthenticationManager
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.context import SecurityContextHolder
from springpython.security.context import SecurityContext
from springpython.security import BadCredentialsException
from springpython.security import DisabledException
from springpython.security import UsernameNotFoundException
from springpython.test.support import testSupportClasses

class InMemoryAuthenticationProviderTestCase(unittest.TestCase):
    """
    DEPRECATED since v0.2: Use InMemoryUserDetailsService with a DaoAuthenticationProvider instead.
    This test case provides testing supporting until that section of code is removed.
    """
    def testProgrammaticInMemoryAuthentication(self):
        SecurityContextHolder.setContext(SecurityContext())
        
        userMap = {}
        userMap["user1"] = ("password1", ["role1", "blue"], True)
        userMap["user2"] = ("password2", ["role1", "orange"], True)
        userMap["adminuser"] = ("password3", ["role1", "admin"], True)
        userMap["disableduser"] = ("password4", ["role1", "blue"], False)
        userMap["emptyuser"] = ("", [], True)
        userMap["toomanyroles1"] = ("password5", ["blue", "orange"], True)
        userMap["toomanyroles2"] = ("password6", ["orange", "admin"], True)
        userMap["toomanyroles3"] = ("password7", ["blue", "admin"], True)
        userMap["toomanyroles4"] = ("password8", ["blue", "admin"], True)

        authenticationProvider = InMemoryAuthenticationProvider(userMap = userMap)
        
        authenticationManager = AuthenticationManager(authenticationProviderList = [authenticationProvider])
        
        authentication = UsernamePasswordAuthenticationToken(username="user1", password=userMap["user1"][0])
        SecurityContextHolder.getContext().authentication = authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in authentication.grantedAuthorities)
        self.assertTrue("blue" in authentication.grantedAuthorities)
        
        authentication = UsernamePasswordAuthenticationToken(username="user2", password=userMap["user2"][0])
        SecurityContextHolder.getContext().authentication = authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in authentication.grantedAuthorities)
        self.assertTrue("orange" in authentication.grantedAuthorities)

        authentication = UsernamePasswordAuthenticationToken(username="adminuser", password=userMap["adminuser"][0])
        SecurityContextHolder.getContext().authentication = authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in authentication.grantedAuthorities)
        self.assertTrue("admin" in authentication.grantedAuthorities)

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password=userMap["disableduser"][0])
        self.assertRaises(DisabledException, authenticationManager.authenticate, authentication)
        
        authentication = UsernamePasswordAuthenticationToken(username="user1", password="badpassword")
        self.assertRaises(BadCredentialsException, authenticationManager.authenticate, authentication)

    def testIoCInMemoryAuthentication(self):
        SecurityContextHolder.setContext(SecurityContext())
        appContext = XmlApplicationContext("support/providerApplicationContext.xml")
        
        authenticationManager = appContext.getComponent("deprecatedAuthenticationManager")
        
        authentication = UsernamePasswordAuthenticationToken(username="user1", password="password1")
        SecurityContextHolder.getContext().authentication = authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in authentication.grantedAuthorities)
        self.assertTrue("blue" in authentication.grantedAuthorities)
        
        authentication = UsernamePasswordAuthenticationToken(username="user2", password="password2")
        SecurityContextHolder.getContext().authentication = authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in authentication.grantedAuthorities)
        self.assertTrue("orange" in authentication.grantedAuthorities)

        authentication = UsernamePasswordAuthenticationToken(username="adminuser", password="password3")
        SecurityContextHolder.getContext().authentication = authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in authentication.grantedAuthorities)
        self.assertTrue("admin" in authentication.grantedAuthorities)

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password="password4")
        self.assertRaises(DisabledException, authenticationManager.authenticate, authentication)

class InMemoryDaoAuthenticationProviderTestCase(unittest.TestCase):
    def setUp(self):
        SecurityContextHolder.setContext(SecurityContext())
        self.appContext = XmlApplicationContext("support/providerApplicationContext.xml")
        self.authenticationManager = self.appContext.getComponent("inMemoryDaoAuthenticationManager")
        
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.logger = logging.getLogger("springpython.test.providerTestCases.InMemoryDaoAuthenticationProviderTestCase")

    def testIoCDaoAuthenticationGoodUsers(self):                
        authentication = UsernamePasswordAuthenticationToken(username="user1", password="password1")
        SecurityContextHolder.getContext().authentication = self.authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.grantedAuthorities)
        self.assertTrue("blue" in SecurityContextHolder.getContext().authentication.grantedAuthorities)
        
        authentication = UsernamePasswordAuthenticationToken(username="user2", password="password2")
        SecurityContextHolder.getContext().authentication = self.authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.grantedAuthorities)
        self.assertTrue("orange" in SecurityContextHolder.getContext().authentication.grantedAuthorities)

        authentication = UsernamePasswordAuthenticationToken(username="adminuser", password="password3")
        SecurityContextHolder.getContext().authentication = self.authenticationManager.authenticate(authentication)
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.grantedAuthorities)
        self.assertTrue("admin" in SecurityContextHolder.getContext().authentication.grantedAuthorities)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptions(self):
        authentication = UsernamePasswordAuthenticationToken(username="nonexistent", password="password999")
        self.assertRaises(BadCredentialsException, self.authenticationManager.authenticate, authentication)

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password="password4")
        self.assertRaises(DisabledException, self.authenticationManager.authenticate, authentication)

        authentication = UsernamePasswordAuthenticationToken(username="emptyuser", password="")
        self.assertRaises(BadCredentialsException, self.authenticationManager.authenticate, authentication)

class DaoAuthenticationProviderHidingUserNotFoundExceptionsTestCase(MockTestCase):
    def __init__(self, methodName='runTest'):
        MockTestCase.__init__(self, methodName)
        self.logger = logging.getLogger("springpython.test.providerTestCases.DaoAuthenticationProviderHidingUserNotFoundExceptionsTestCase")

    def setUp(self):
        SecurityContextHolder.setContext(SecurityContext())
        self.appContext = XmlApplicationContext("support/providerApplicationContext.xml")
        self.authenticationManager = self.appContext.getComponent("daoAuthenticationManagerHidingUserNotFoundExceptions")
        self.mock = self.mock()
        self.appContext.getComponent("dataSource").stubConnection.mockCursor = self.mock
        
    def testIoCDaoAuthenticationActiveUserBadPassword(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('activeuser', 'correctpassword', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('activeuser', 'role1')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="activeuser", password="wrongpassword")
        self.assertRaises(BadCredentialsException, self.authenticationManager.authenticate, authentication)
        
    def testIoCDaoAuthenticationDisabledUserBadPassword(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('disabled', 'correctpassword', False)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('disabled', 'role1')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="disabled", password="wrongpassword")
        self.assertRaises(DisabledException, self.authenticationManager.authenticate, authentication)
        
    def testIoCDaoAuthenticationGoodUser1(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('user1', 'password1', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('user1', 'role1'), ('user1', 'blue')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="user1", password="password1")
        SecurityContextHolder.getContext().authentication = self.authenticationManager.authenticate(authentication)
        
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.grantedAuthorities)
        self.assertTrue("blue" in SecurityContextHolder.getContext().authentication.grantedAuthorities)

    def testIoCDaoAuthenticationGoodUser2(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('user2', 'password2', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('user2', 'role1'), ('user2', 'orange')])).id("#4").after("#3")
        
        authentication = UsernamePasswordAuthenticationToken(username="user2", password="password2")
        SecurityContextHolder.getContext().authentication = self.authenticationManager.authenticate(authentication)
        
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.grantedAuthorities)
        self.assertTrue("orange" in SecurityContextHolder.getContext().authentication.grantedAuthorities)

    def testIoCDaoAuthenticationGoodAdminUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('adminuser', 'password3', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('adminuser', 'role1'), ('adminuser', 'admin')])).id("#4").after("#3")
        
        authentication = UsernamePasswordAuthenticationToken(username="adminuser", password="password3")
        SecurityContextHolder.getContext().authentication = self.authenticationManager.authenticate(authentication)
        
        self.assertTrue("role1" in SecurityContextHolder.getContext().authentication.grantedAuthorities)
        self.assertTrue("admin" in SecurityContextHolder.getContext().authentication.grantedAuthorities)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptionsNonexistentUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([])).id("#2").after("#1")

        authentication = UsernamePasswordAuthenticationToken(username="nonexistent", password="password999")
        self.assertRaises(BadCredentialsException, self.authenticationManager.authenticate, authentication)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptionsDisabledUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'password4', False)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'role1'), ('disableduser', 'blue')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password="password4")
        self.assertRaises(DisabledException, self.authenticationManager.authenticate, authentication)

    def testIocDaoAuthenticationBadUsersWithHiddenExceptionsEmptyUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('emptyuser', '', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="emptyuser", password="")
        self.assertRaises(BadCredentialsException, self.authenticationManager.authenticate, authentication)

class DaoAuthenticationProviderNotHidingUserNotFoundExceptionsTestCase(MockTestCase):
    def __init__(self, methodName='runTest'):
        MockTestCase.__init__(self, methodName)
        self.logger = logging.getLogger("springpython.test.providerTestCases.DaoAuthenticationProviderNotHidingUserNotFoundExceptionsTestCase")

    def setUp(self):
        SecurityContextHolder.setContext(SecurityContext())
        self.appContext = XmlApplicationContext("support/providerApplicationContext.xml")
        self.authenticationManager = self.appContext.getComponent("daoAuthenticationManagerNotHidingUserNotFoundExceptions")
        self.mock = self.mock()
        self.appContext.getComponent("dataSource").stubConnection.mockCursor = self.mock
        
    def testIocDaoAuthenticationBadUsersDontHideBadCredentialsDisabledUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'password4', False)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([('disableduser', 'role1'), ('disableduser', 'blue')])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="disableduser", password="password4")
        self.assertRaises(DisabledException, self.authenticationManager.authenticate, authentication)

    def testIocDaoAuthenticationBadUsersDontHideBadCredentialsEmptyUser(self):
        self.mock.expects(once()).method("execute").id("#1")
        self.mock.expects(once()).method("fetchall").will(return_value([('emptyuser', '', True)])).id("#2").after("#1")
        self.mock.expects(once()).method("execute").id("#3").after("#2")
        self.mock.expects(once()).method("fetchall").will(return_value([])).id("#4").after("#3")

        authentication = UsernamePasswordAuthenticationToken(username="emptyuser", password="")
        self.assertRaises(UsernameNotFoundException, self.authenticationManager.authenticate, authentication)
