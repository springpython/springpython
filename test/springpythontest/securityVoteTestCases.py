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
import unittest
from springpython.security import AccessDeniedException
from springpython.security.context import SecurityContext
from springpython.security.context import SecurityContextHolder
from springpython.security.providers import AuthenticationManager
from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.providers.dao import DaoAuthenticationProvider
from springpython.security.userdetails import InMemoryUserDetailsService
from springpython.security.vote import AccessDecisionVoter
from springpython.security.vote import AccessDecisionManager
from springpython.security.vote import LabelBasedAclVoter
from springpython.security.vote import AffirmativeBased
from springpython.security.vote import ConsensusBased
from springpython.security.vote import UnanimousBased
from springpythontest.support.testSecurityClasses import SampleBlockOfData
from springpythontest.support.testSecurityClasses import SampleService
from springpython.context import XmlApplicationContext

class VoteInterfaceTestCase(unittest.TestCase):
    def testAccessDecisionVoterInterface(self):
        accessDecisionVoter = AccessDecisionVoter()
        self.assertRaises(NotImplementedError, accessDecisionVoter.supports, None)
        self.assertRaises(NotImplementedError, accessDecisionVoter.vote, None, None, None)

    def testAccessDecisionManagerInterface(self):
        access_decision_mgr = AccessDecisionManager()
        self.assertRaises(NotImplementedError, access_decision_mgr.supports, None)
        self.assertRaises(NotImplementedError, access_decision_mgr.decide, None, None, None)
        
class LabelBasedAclVoterTestCase(unittest.TestCase):
    def setupContext(self, username, password):
        applicationContext = XmlApplicationContext("support/labelBasedAclVoterApplicationContext.xml")
        token = UsernamePasswordAuthenticationToken(username, password)
        auth_manager = applicationContext.get_component("auth_manager")
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = auth_manager.authenticate(token)
        self.sampleService = applicationContext.get_component("sampleService")
        self.blueblock = SampleBlockOfData("blue")
        self.orangeblock = SampleBlockOfData("orange")
        self.sharedblock = SampleBlockOfData("blue-orange")

    def testProgrammaticSetupForUnanimousBased(self):
        inMemoryUserDetailsService = InMemoryUserDetailsService()
        inMemoryUserDetailsService.user_dict["blueuser"] = ("password1", ["LABEL_BLUE"], False)
        inMemoryUserDetailsService.user_dict["superuser"] = ("password2", ["LABEL_SHARED"], False),
        inMemoryUserDetailsService.user_dict["orangeuser"] = ("password3", ["LABEL_ORANGE"], False),
        inMemoryUserDetailsService.user_dict["multiuser"] = ("password4", ["LABEL_BLUE", "LABEL_ORANGE"], False)
        inMemoryDaoAuthenticationProvider = DaoAuthenticationProvider()
        inMemoryDaoAuthenticationProvider.userDetailsService = inMemoryUserDetailsService
        authenticationProvider = AuthenticationManager([inMemoryDaoAuthenticationProvider])

        auth_manager = AuthenticationManager()
        auth_manager.authenticationProviderList = [authenticationProvider]

        labelBasedAclVoter = LabelBasedAclVoter()
        labelBasedAclVoter.label_dict["LABEL_BLUE"] = ["blue", "blue-orange"]
        labelBasedAclVoter.label_dict["LABEL_ORANGE"] = ["orange", "blue-orange"]
        labelBasedAclVoter.label_dict["LABEL_SHARED"] = ["blue", "orange", "blue-orange"]
        labelBasedAclVoter.attr_indicating_labeled_op = "LABELED_OPERATION"
        labelBasedAclVoter.access_decision_mgr = UnanimousBased(access_decision_voters = [labelBasedAclVoter], \
                                                                  allow_if_all_abstain = False)
        
    def testProgrammaticSetupForAffirmativeBased(self):
        inMemoryUserDetailsService = InMemoryUserDetailsService()
        inMemoryUserDetailsService.user_dict["blueuser"] = ("password1", ["LABEL_BLUE"], False)
        inMemoryUserDetailsService.user_dict["superuser"] = ("password2", ["LABEL_SHARED"], False),
        inMemoryUserDetailsService.user_dict["orangeuser"] = ("password3", ["LABEL_ORANGE"], False),
        inMemoryUserDetailsService.user_dict["multiuser"] = ("password4", ["LABEL_BLUE", "LABEL_ORANGE"], False)
        inMemoryDaoAuthenticationProvider = DaoAuthenticationProvider()
        inMemoryDaoAuthenticationProvider.userDetailsService = inMemoryUserDetailsService
        authenticationProvider = AuthenticationManager([inMemoryDaoAuthenticationProvider])

        auth_manager = AuthenticationManager()
        auth_manager.authenticationProviderList = [authenticationProvider]

        labelBasedAclVoter = LabelBasedAclVoter()
        labelBasedAclVoter.label_dict["LABEL_BLUE"] = ["blue", "blue-orange"]
        labelBasedAclVoter.label_dict["LABEL_ORANGE"] = ["orange", "blue-orange"]
        labelBasedAclVoter.label_dict["LABEL_SHARED"] = ["blue", "orange", "blue-orange"]
        labelBasedAclVoter.attr_indicating_labeled_op = "LABELED_OPERATION"
        labelBasedAclVoter.access_decision_mgr = AffirmativeBased(access_decision_voters = [labelBasedAclVoter], \
                                                                    allow_if_all_abstain = False)
        
    def testProgrammaticSetupForConsensusBased(self):
        inMemoryUserDetailsService = InMemoryUserDetailsService()
        inMemoryUserDetailsService.user_dict["blueuser"] = ("password1", ["LABEL_BLUE"], False)
        inMemoryUserDetailsService.user_dict["superuser"] = ("password2", ["LABEL_SHARED"], False),
        inMemoryUserDetailsService.user_dict["orangeuser"] = ("password3", ["LABEL_ORANGE"], False),
        inMemoryUserDetailsService.user_dict["multiuser"] = ("password4", ["LABEL_BLUE", "LABEL_ORANGE"], False)
        inMemoryDaoAuthenticationProvider = DaoAuthenticationProvider()
        inMemoryDaoAuthenticationProvider.userDetailsService = inMemoryUserDetailsService
        authenticationProvider = AuthenticationManager([inMemoryDaoAuthenticationProvider])

        auth_manager = AuthenticationManager()
        auth_manager.authenticationProviderList = [authenticationProvider]

        labelBasedAclVoter = LabelBasedAclVoter()
        labelBasedAclVoter.label_dict["LABEL_BLUE"] = ["blue", "blue-orange"]
        labelBasedAclVoter.label_dict["LABEL_ORANGE"] = ["orange", "blue-orange"]
        labelBasedAclVoter.label_dict["LABEL_SHARED"] = ["blue", "orange", "blue-orange"]
        labelBasedAclVoter.attr_indicating_labeled_op = "LABELED_OPERATION"
        labelBasedAclVoter.access_decision_mgr = ConsensusBased(access_decision_voters = [labelBasedAclVoter], \
                                                                  allow_if_all_abstain = False)
        
    def testDoingSomethingForBlueUser(self):
        self.setupContext("blueuser", "password1")

        self.sampleService.doSomethingOnThis(self.blueblock, self.blueblock)
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.orangeblock, self.orangeblock)
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.blueblock, self.orangeblock)
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.orangeblock, self.blueblock)
        self.sampleService.doSomethingOnThis(self.sharedblock, self.sharedblock)

    def testDoingSomethingForMultiUser(self):
        self.setupContext("multiuser", "password4")

        self.sampleService.doSomethingOnThis(self.blueblock, self.blueblock)
        self.sampleService.doSomethingOnThis(self.orangeblock, self.orangeblock)
        self.sampleService.doSomethingOnThis(self.blueblock, self.orangeblock)
        self.sampleService.doSomethingOnThis(self.orangeblock, self.blueblock)
        self.sampleService.doSomethingOnThis(self.sharedblock, self.sharedblock)

    def testDoingSomethingForOrangeUser(self):
        self.setupContext("orangeuser", "password3")

        self.sampleService.doSomethingOnThis(self.orangeblock, self.orangeblock)
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.blueblock, self.blueblock)
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.blueblock, self.orangeblock)
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.orangeblock, self.blueblock)
        self.sampleService.doSomethingOnThis(self.sharedblock, self.sharedblock)

    def testDoingSomethingForSuperUser(self):
        self.setupContext("superuser", "password2")

        self.sampleService.doSomethingOnThis(self.blueblock, self.blueblock)
        self.sampleService.doSomethingOnThis(self.orangeblock, self.orangeblock)
        self.sampleService.doSomethingOnThis(self.blueblock, self.orangeblock)
        self.sampleService.doSomethingOnThis(self.orangeblock, self.blueblock)
        self.sampleService.doSomethingOnThis(self.sharedblock, self.sharedblock)

class SecurityInterceptorTestCase(unittest.TestCase):
    def setupContext(self, username, password):
        applicationContext = XmlApplicationContext("support/roleVoterApplicationContext.xml")
        token = UsernamePasswordAuthenticationToken(username, password)
        auth_manager = applicationContext.get_component("auth_manager")
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = auth_manager.authenticate(token)
        self.sampleService = applicationContext.get_component("sampleService")
        self.block1 = SampleBlockOfData("block1")
        self.block2 = SampleBlockOfData("block2")

    def testVerifySecurityMethodInterceptorReturnsSomething(self):
        self.setupContext("basicuser", "password1")
        self.assertEquals(self.sampleService.doSomethingOnThis(self.block1, self.block2), "You made it!")

class RoleVoterTestCase(unittest.TestCase):
    def setupContext(self, username, password):
        applicationContext = XmlApplicationContext("support/roleVoterApplicationContext.xml")
        token = UsernamePasswordAuthenticationToken(username, password)
        auth_manager = applicationContext.get_component("auth_manager")
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = auth_manager.authenticate(token)
        self.sampleService = applicationContext.get_component("sampleService")
        self.block1 = SampleBlockOfData("block1")
        self.block2 = SampleBlockOfData("block2")

    def testDoingSomethingForBasicUser(self):
        self.setupContext("basicuser", "password1")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForOtherUser(self):
        self.setupContext("otheruser", "password2")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

    def testTryingToExecuteAnUnauthorizedFunction(self):
        self.setupContext("basicuser", "password1")
        self.assertRaises(AccessDeniedException, self.sampleService.updateData, "sample")

class AffirmativeBasedTestCase(unittest.TestCase):
    def setupContext(self, username, password):
        applicationContext = XmlApplicationContext("support/affirmativeBasedApplicationContext.xml")
        token = UsernamePasswordAuthenticationToken(username, password)
        auth_manager = applicationContext.get_component("auth_manager")
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = auth_manager.authenticate(token)
        self.sampleService = applicationContext.get_component("sampleService")
        self.block1 = SampleBlockOfData("block1")
        self.block2 = SampleBlockOfData("block2")

    def testDoingSomethingForBasicBlueUser(self):
        self.setupContext("basicblueuser", "password1")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForBasicOrangeUser(self):
        self.setupContext("basicorangeuser", "password2")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForOtherBlueUser(self):
        self.setupContext("otherblueuser", "password3")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForOtherOrangeUser(self):
        self.setupContext("otherorangeuser", "password4")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

class ConsensusBasedTestCase(unittest.TestCase):
    def setupContext(self, username, password):
        applicationContext = XmlApplicationContext("support/consensusBasedApplicationContext.xml")
        token = UsernamePasswordAuthenticationToken(username, password)
        auth_manager = applicationContext.get_component("auth_manager")
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = auth_manager.authenticate(token)
        self.sampleService = applicationContext.get_component("sampleService")
        self.block1 = SampleBlockOfData("block1")
        self.block2 = SampleBlockOfData("block2")

    def testDoingSomethingForBasicHiBlueUser(self):
        self.setupContext("basichiblueuser", "password1")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForBasicHiOrangeUser(self):
        self.setupContext("basichiorangeuser", "password2")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForOtherHiBlueUser(self):
        self.setupContext("otherhiblueuser", "password3")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForOtherHiOrangeUser(self):
        self.setupContext("otherhiorangeuser", "password4")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

    def testDoingSomethingForBasicLoBlueUser(self):
        self.setupContext("basicloblueuser", "password5")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForBasicLoOrangeUser(self):
        self.setupContext("basicloorangeuser", "password6")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

    def testDoingSomethingForOtherLoBlueUser(self):
        self.setupContext("otherloblueuser", "password7")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

    def testDoingSomethingForOtherLoOrangeUser(self):
        self.setupContext("otherloorangeuser", "password8")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

class UnanimousBasedTestCase(unittest.TestCase):
    def setupContext(self, username, password):
        applicationContext = XmlApplicationContext("support/unanimousBasedApplicationContext.xml")
        token = UsernamePasswordAuthenticationToken(username, password)
        auth_manager = applicationContext.get_component("auth_manager")
        SecurityContextHolder.setContext(SecurityContext())
        SecurityContextHolder.getContext().authentication = auth_manager.authenticate(token)
        self.sampleService = applicationContext.get_component("sampleService")
        self.block1 = SampleBlockOfData("block1")
        self.block2 = SampleBlockOfData("block2")

    def testDoingSomethingForBasicBlueUser(self):
        self.setupContext("basicblueuser", "password1")
        self.sampleService.doSomethingOnThis(self.block1, self.block2)

    def testDoingSomethingForBasicOrangeUser(self):
        self.setupContext("basicorangeuser", "password2")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

    def testDoingSomethingForOtherBlueUser(self):
        self.setupContext("otherblueuser", "password3")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)

    def testDoingSomethingForOtherOrangeUser(self):
        self.setupContext("otherorangeuser", "password4")
        self.assertRaises(AccessDeniedException, self.sampleService.doSomethingOnThis, self.block1, self.block2)
