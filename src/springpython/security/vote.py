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
from springpython.security import AccessDeniedException

logger = logging.getLogger("springpython.security.vote")

class AccessDecisionVoter:
    """
    Indicates a class is responsible for voting on authorization decisions.
    
    The coordination of voting (ie polling AccessDecisionVoters, tallying
    their responses, and making the final authorization decision) is performed
    by an AccessDecisionManager. 
    """
    ACCESS_ABSTAIN = 0
    ACCESS_DENIED = 1
    ACCESS_GRANTED = 2
    access_dict = { ACCESS_ABSTAIN: "ACCESS_ABSTAIN", ACCESS_DENIED: "ACCESS_DENIED", ACCESS_GRANTED: "ACCESS_GRANTED" }
    
    def supports(self, attr):
        """
        Indicates whether this AccessDecisionVoter is able to vote on the passed in object.
        """
        raise NotImplementedError()
    
    def vote(self, authentication, object, config):
        """Indicates whether or not access is granted."""
        raise NotImplementedError()

class RoleVoter(AccessDecisionVoter):
    """
    Votes if any ConfigAttribute.getAttribute() starts with a prefix indicating that it is a role.
    The default prefix string is ROLE_, but this may be overriden to any value. It may also be set
    to empty, which means that essentially any attribute will be voted on. As described further
    below, the effect of an empty prefix may not be quite desireable.
    
    Abstains from voting if no configuration attribute commences with the role prefix. Votes to
    grant access if there is an exact matching GrantedAuthority to a ConfigAttribute starting
    with the role prefix. Votes to deny access if there is no exact matching GrantedAuthority
    to a ConfigAttribute starting with the role prefix.
    
    An empty role prefix means that the voter will vote for every ConfigAttribute. When there
    are different categories of ConfigAttributes used, this will not be optimal since the voter
    will be voting for attributes which do not represent roles. However, this option may be of
    some use when using preexisting role names without a prefix, and no ability exists to prefix
    them with a role prefix on reading them in, such as provided for example in JdbcDaoImpl.
    
    All comparisons and prefixes are case sensitive.
    """
    def __init__(self, role_prefix = "ROLE_"):
        self.role_prefix = role_prefix
        self.logger = logging.getLogger("springpython.security.vote.RoleVoter")

    def supports(self, attr):
        """This voter will support a list, or a string starting with
        the same characters as the set prefix.
        """
        if isinstance(attr, list) or (attr is not None and attr.startswith(self.role_prefix)):
            return True
        else:
            return False

    def vote(self, authentication, invocation, config):
        """Grant access if any of the granted authorities matches any of the required
        roles.
        """
        results = self.ACCESS_ABSTAIN
        for attribute in config:
            if self.supports(attribute):
                self.logger.debug("This %s role voter will vote whether user has %s" % (self.role_prefix, attribute))
                results = self.ACCESS_DENIED
                for authority in authentication.granted_auths:
                    if attribute == authority:
                        self.logger.debug("This user has %s in %s. Vote for GRANTED!" % (attribute, authentication.granted_auths))
                        return self.ACCESS_GRANTED

        if results == self.ACCESS_ABSTAIN:
            self.logger.debug("This %s voter is abstaining from voting" % self.role_prefix)
        elif results == self.ACCESS_DENIED:
            self.logger.debug("This %s voter did NOT find the required credentials in %s. Vote for DENIED!" % (self.role_prefix, authentication.granted_auths))

        return results

    def __str__(self):
        return "<'%s' role voter>" % self.role_prefix

class AbstractAclVoter(AccessDecisionVoter):
    """
    May/may not need this class
    """
    pass

class LabelBasedAclVoter(AbstractAclVoter):
    """
     * This Acl voter will evaluate methods based on labels applied to incoming arguments. It will
     * only check methods that have been properly tagged in the MethodSecurityInterceptor with the
     * value stored in <b>attr_indicating_labeled_op</b>. If a method has been tagged, then
     * it examines each argument, and if the argument implements {@link LabeledData}, then it will
     * asses if the user's list of granted authorities matches.<p>
     * <p>
     * By default, if none of the arguments are labeled, then the access will be granted. This can
     * be overridden by setting <b>allow_access_if_no_attr_labeled</b> to false in the Spring
     * context file.<p>
     * <p>
     * In many situations, different values are linked together to define a common label, it is 
     * necessary to define a map in the application context that links user-assigned label access
     * to domain object labels. This is done by setting up the <b>label_dict</b> in the application
     * context.<p>
     * 
     * @author Greg Turnquist
     * @see org.acegisecurity.intercept.method.aopalliance.MethodSecurityInterceptor
    """
    def __init__(self, label_dict = None, allow_access_if_no_attr_labeled = False, attr_indicating_labeled_op = ""):
        if label_dict is None:
            self.label_dict = {}
        else:
            self.label_dict = label_dict
        self.allow_access_if_no_attr_labeled = allow_access_if_no_attr_labeled
        self.attr_indicating_labeled_op = attr_indicating_labeled_op
        self.logger = logging.getLogger("springpython.security.vote.LabelBasedAclVoter")

    def supports(self, attr):
    	if isinstance(attr, list) or (attr == self.attr_indicating_labeled_op):
            return True
        else:
            return False

    def vote(self, authentication, invocation, config):
        result = self.ACCESS_ABSTAIN;
        
        for attribute in config:
            if self.supports(attribute):
                result = self.ACCESS_DENIED;
            
                userLabels = []
            
                for label in authentication.granted_auths:
                    if label in self.label_dict:
                        userLabels.extend(self.label_dict[label])

                labeledArguments = [arg.getLabel() for arg in invocation.args if hasattr(arg, "getLabel")]
                matches = [arg for arg in labeledArguments if arg in userLabels]
                misses  = [arg for arg in labeledArguments if arg not in userLabels]
                self.logger.debug("Arguments: %s Matches: %s Misses: %s User labels: %s" % (labeledArguments, matches, misses, userLabels))

                if len(matches) > 0 and misses == []:
                    self.logger.debug("Access is granted!")
                    return self.ACCESS_GRANTED;
                elif labeledArguments == []:
                    if self.allow_access_if_no_attr_labeled:
                        self.logger.debug("Access is granted, since there are no attributes set!")
                        return self.ACCESS_GRANTED;
                    else:
                        self.logger.debug("Access is denied, since there are no attributes set!")
                        return self.ACCESS_DENIED;

            self.logger.debug("No matches, so returning %s" % self.access_dict[result])
            return result;

    def __str__(self):
        return "<'%s' label-based ACL voter>" % self.label_dict

class AccessDecisionManager:
    """"
    Makes a final access control (authorization) decision.
    """
    def __init__(self, access_decision_voters = [], allow_if_all_abstain = False):
        self.access_decision_voters = access_decision_voters
        self.allow_if_all_abstain = allow_if_all_abstain

    def decide(self, authentication, object, config):
        """Resolves an access control decision for the passed parameters."""
        raise NotImplementedError()


    def supports(self, attr):
        """
        Indicates whether the AccessDecisionManager implementation is able to
        provide access control decisions for the indicated secured object type.
        """
        raise NotImplementedError()
    
class AffirmativeBased(AccessDecisionManager):
    """
    Simple concrete implementation of AccessDecisionManager that grants access
    if any AccessDecisionVoter returns an affirmative response.
    """
    def __init__(self, access_decision_voters = [], allow_if_all_abstain = False):
        AccessDecisionManager.__init__(self, access_decision_voters, allow_if_all_abstain)
        self.logger = logging.getLogger("springpython.security.vote.AffirmativeBased")

    def decide(self, authentication, invocation, config):
        """
        This concrete implementation simply polls all configured
        AccessDecisionVoters and grants access if any AccessDecisionVoter voted affirmatively.
        """
        for voter in self.access_decision_voters:
            if voter.supports(config) and \
               voter.vote(authentication, invocation, config) == AccessDecisionVoter.ACCESS_GRANTED:
                self.logger.debug("Received affirmative vote from %s, granting access." % voter)
                return
        raise AccessDeniedException("Access is denied.")

class ConsensusBased(AccessDecisionManager):
    """
    Simple concrete implementation of AccessDecisionManager that uses a consensus-based approach.
    """
    def __init__(self, access_decision_voters = [], allow_if_all_abstain = False):
        AccessDecisionManager.__init__(self, access_decision_voters, allow_if_all_abstain)
        self.allow_if_tied = True
        self.logger = logging.getLogger("springpython.security.vote.ConsensusBased")

    def decide(self, authentication, invocation, config):
        """
        This concrete implementation simply polls all configured AccessDecisionVoters
        and upon completion determines the consensus of granted vs denied responses.
        """
        granted_votes = []
        denied_votes = []
        for voter in self.access_decision_voters:
            if voter.supports(config):
                vote = voter.vote(authentication, invocation, config)
                if vote == AccessDecisionVoter.ACCESS_GRANTED:
                    granted_votes.append(voter)
                if vote == AccessDecisionVoter.ACCESS_DENIED:
                    denied_votes.append(voter)
        if len(granted_votes) > len(denied_votes):
            self.logger.debug("%s granted votes, %s denial votes, granting access." % (len(granted_votes), len(denied_votes)))
            return
        elif len(granted_votes) < len(denied_votes):
            self.logger.debug("%s granted votes, %s denial votes, denying access." % (len(granted_votes), len(denied_votes)))
            raise AccessDeniedException("Access is denied.")
        elif self.allow_if_tied:
            self.logger.debug("%s granted votes, %s denial votes, granting access." % (len(granted_votes), len(denied_votes)))
            return
        else:
            self.logger.debug("%s granted votes, %s denial votes, denying access." % (len(granted_votes), len(denied_votes)))
            raise AccessDeniedException("Access is denied.")

class UnanimousBased(AccessDecisionManager):
    """
    Simple concrete implementation of AccessDecisionManager that requires all voters to
    abstain or grant access.
    """
    def __init__(self, access_decision_voters = [], allow_if_all_abstain = False):
        AccessDecisionManager.__init__(self, access_decision_voters, allow_if_all_abstain)
        self.logger = logging.getLogger("springpython.security.vote.UnanimousBased")

    def decide(self, authentication, invocation, config):
        """
        This concrete implementation polls all configured AccessDecisionVoters for
        each ConfigAttribute and grants access if only grant votes were received.
        """
        for voter in self.access_decision_voters:
            if voter.supports(config) and \
               voter.vote(authentication, invocation, config) == AccessDecisionVoter.ACCESS_DENIED:
                self.logger.debug("Received denial vote from %s, denying access" % voter)
                raise AccessDeniedException("Access is denied.")
