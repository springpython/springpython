Security
========

Spring Python's Security module is based on
`Acegi Security's <http://acegisecurity.org/>`_ architecture.
You can read `Acegi's detailed reference manual <http://acegisecurity.org/guide/springsecurity.html>`_
for a background on this module.

.. note::

    Spring Security vs. Acegi Security

    At the time this module was implemented, Spring Security was still Acegi
    Security. Links include reference documentation that was used at the time
    to implement this security module.

External dependencies
---------------------

*springpython.security.cherrypy3* package depends on `CherryPy 3 <http://cherrypy.org/>`_
being installed prior to using it. Other than that, there are no specific external libraries
required by Spring Python's security system, however the IoC configuration
format that you'll be using may need some, check IoC documentation
for more details.

Shared Objects
--------------

The major building blocks of Spring Python Security are

* *SecurityContextHolder*, to provide any type access to the *SecurityContext*.
* *SecurityContext*, to hold the Authentication and possibly request-specific security information.
* *HttpSessionContextIntegrationFilter*, to store the *SecurityContext* in the HTTP session between web requests.
* *Authentication*, to represent the principal in an Acegi Security-specific manner.
* *GrantedAuthority*, to reflect the application-wide permissions granted to a principal.

These objects are needed for both authentication and authorization.

Authentication
--------------

The first level of security involves verifying your credentials. Most systems
today use some type of username/password check. To configure Spring Python,
you will need to configure one or more *AuthenticationProviders*. All
*Authentication* implementations are required to store an array of
*GrantedAuthority* objects. These represent the authorities that have been
granted to the principal. The GrantedAuthority objects are inserted into
the *Authentication* object by the *AuthenticationManager* and are later read
by *AccessDecisionManagers* when making authorization decisions. These are
chained together inside an *AuthenticationManager*.

AuthenticationProviders
+++++++++++++++++++++++

DaoAuthenticationProvider
>>>>>>>>>>>>>>>>>>>>>>>>>

This *AuthenticationProvider* allows you to build a dictionary of user accounts,
and is very handy for integration testing without resorting to complex
configuration of 3rd party systems.

To configure this using :doc:`a pythonic, decorator-based IoC container <objects-pythonconfig>`::

    class SampleContainer(PythonConfig):

        @Object
        def inMemoryDaoAuthenticationProvider(self):
            provider = DaoAuthenticationProvider()
            provider.user_details_service = inMemoryUserDetailsService()
            return provider

        @Object
        def inMemoryUserDetailsService(self):
            user_details_service = InMemoryUserDetailsService()
            user_details_service.user_dict = {
               "vet1": ("password1", ["VET_ANY"], False),
               "bdavis": ("password2", ["CUSTOMER_ANY"], False),
               "jblack": ("password3", ["CUSTOMER_ANY"], False),
               "disableduser": ("password4", ["VET_ANY"], True),
               "emptyuser": ("", [], False) }
            return user_details_service

.. highlight:: xml

XML configuration using :doc:`XMLConfig <objects-xmlconfig>`::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                   http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="inMemoryUserDetailsService" class="springpython.security.userdetails.InMemoryUserDetailsService">
            <property name="user_dict">
                <dict>
                    <entry>
                        <key><value>user1</value></key>
                        <value>
                            <tuple>
                                <value>password1</value>
                                <list><value>role1</value><value>blue</value></list>
                                <value>True</value>
                            </tuple>
                        </value>
                    </entry>
                    <entry>
                        <key><value>user2</value></key>
                        <value>
                            <tuple>
                                <value>password2</value>
                                <list><value>role1</value><value>orange</value></list>
                                <value>True</value>
                            </tuple>
                        </value>
                    </entry>
                    <entry>
                        <key><value>adminuser</value></key>
                        <value>
                            <tuple>
                                <value>password3</value>
                                <list><value>role1</value><value>admin</value></list>
                                <value>True</value>
                            </tuple>
                        </value>
                    </entry>
                    <entry>
                        <key><value>disableduser</value></key>
                        <value>
                            <tuple>
                                <value>password4</value>
                                <list><value>role1</value><value>blue</value></list>
                                <value>False</value>
                            </tuple>
                        </value>
                    </entry>
                    <entry>
                        <key><value>emptyuser</value></key>
                        <value>
                            <tuple>
                                <value/>
                                <list/>
                                <value>True</value>
                            </tuple>
                        </value>
                    </entry>
                </dict>
            </property>
        </object>

        <object id="inMemoryDaoAuthenticationProvider" class="springpython.security.providers.dao.DaoAuthenticationProvider">
            <property name="user_details_service" ref="inMemoryUserDetailsService"/>
        </object>

    </objects>

This is the user map defined for one of the test cases. The first user, user1,
has a password of password1, a list of granted authorities ("role1", "blue"),
and is enabled. The fourth user, "disableduser", has a password and a list of
granted authorities, but is NOT enabled. The last user has no password, which
will cause authentication to fail.

LDAP Authentication Provider
>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Spring Python has an *LdapAuthenticationProvider* that is able to authenticate
users against an LDAP server using either binding or password comparison. It
will also search the LDAP server for groups in order to identify roles.

.. note::

    Spring Python's LDAP only works with CPython

    Currently, Spring Python only provides LDAP support for CPython. There is
    on-going effort to extend support to Jython as well.

It is possible to the customize the query parameters, as well as inject an
alternative version of authentication as well as role identification.

There are two ways to verify a password in ldap: binding to the server using
the password, or fetching the password from ldap and comparing outside the
server. Spring Python supports both. You can choose which mechanism by
injecting either a *BindAuthenticator* or a *PasswordComparisonAuthenticator*
into *LdapAuthenticationProvider*.

.. highlight:: xml

The following XML fragment demonstrates how to configure Spring Python's
*LdapAuthenticationProvider* using a *BindAuthenticator* combined with a
*DefaultLdapAuthoritiesPopulator*::

    <object id="context_source" class="springpython.security.providers.Ldap.DefaultSpringSecurityContextSource">
        <property name="url" value="ldap://localhost:53389/dc=springframework,dc=org"/>
    </object>

    <object id="bindAuthenticator" class="springpython.security.providers.Ldap.BindAuthenticator">
        <property name="context_source" ref="context_source"/>
        <property name="user_dn_patterns" value="uid={0},ou=people"/>
    </object>

    <object id="authoritiesPopulator" class="springpython.security.providers.Ldap.DefaultLdapAuthoritiesPopulator">
        <property name="context_source" ref="context_source"/>
        <property name="group_search_filter" value="member={0}"/>
    </object>

    <object id="ldapAuthenticationProvider" class="springpython.security.providers.Ldap.LdapAuthenticationProvider">
        <property name="ldap_authenticator" ref="bindAuthenticator"/>
        <property name="ldap_authorities_populator" ref="authoritiesPopulator"/>
    </object>

    <object id="ldapAuthenticationManager" class="springpython.security.providers.AuthenticationManager">
        <property name="auth_providers">
            <list><ref object="ldapAuthenticationProvider"/></list>
        </property>
    </object>

* *context_source* - points to an ldap server, defining the base DN to start
  searching for users and groups.

* *bindAuthenticator* - configured to use the context_source, and does a user
  search based on sub-entry *uid={0},ou=people*. *{0}* is the variable where an
  entered username will be substituted before executing the ldap search.

* *authoritiesPopulator* - assuming the user is found, it uses the
  group_search_filter to find groups containing this attribute pointed at the user's DN.

* *ldapAuthenticationProvider* - combines together the bindAuthenticator and
  the authoritiesPopulator, in order to process a *UsernamePasswordAuthenticationToken*.

* *ldapAuthenticationManager* - just like the other examples, this
  *AuthenticationManager* iterates over the list of providers, giving them a
  chance to authenticate the user.

.. highlight:: python

The following shows the same configuration in pure Python, using
:doc:`PythonConfig <objects-pythonconfig>`::

    class LdapContext(PythonConfig):
        def __init__(self):
            PythonConfig.__init__(self)

        @Object
        def context_source(self):
            return DefaultSpringSecurityContext(url="ldap://localhost:53389/dc=springframework,dc=org")

        @Object
        def bind_authenticator(self):
            return BindAuthenticator(self.context_source(), user_dn_patterns="uid={0},ou=people")

        @Object
        def authorities_populator(self):
            return DefaultLdapAuthoritiesPopulator(self.context_source(), group_search_filter="member={0}")

        @Object
        def provider(self):
            return LdapAuthenticationProvider(self.bind_authenticator(), self.authorities_populator())

        @Object
        def manager(self):
            return AuthenticationManager(auth_providers=[self.provider()])

.. highlight:: xml

To use the password comparison mechanism with :doc:`XMLConfig <objects-xmlconfig>`,
substitute PasswordComparisonAuthenticator for BindAuthenticator as follows::

    <object id="context_source" class="springpython.security.providers.Ldap.DefaultSpringSecurityContextSource">
        <property name="url" value="ldap://localhost:53389/dc=springframework,dc=org"/>
    </object>

    <object id="passwordAuthenticator" class="springpython.security.providers.Ldap.PasswordComparisonAuthenticator">
        <property name="context_source" ref="context_source"/>
        <property name="user_dn_patterns" value="uid={0},ou=people"/>
    </object>

    <object id="authoritiesPopulator" class="springpython.security.providers.Ldap.DefaultLdapAuthoritiesPopulator">
        <property name="context_source" ref="context_source"/>
        <property name="group_search_filter" value="member={0}"/>
    </object>

    <object id="ldapAuthenticationProvider" class="springpython.security.providers.Ldap.LdapAuthenticationProvider">
        <property name="ldap_authenticator" ref="bindAuthenticator"/>
        <property name="ldap_authorities_populator" ref="authoritiesPopulator"/>
    </object>

    <object id="ldapAuthenticationManager" class="springpython.security.providers.AuthenticationManager">
        <property name="auth_providers">
            <list><ref object="ldapAuthenticationProvider"/></list>
        </property>
    </object>

.. highlight:: python

The following block shows the same configuration using the pure Python container::

    class LdapContext(PythonConfig):
        def __init__(self):
            PythonConfig.__init__(self)

        @Object
        def context_source(self):
            return DefaultSpringSecurityContext(url="ldap://localhost:53389/dc=springframework,dc=org")

        @Object
        def password_authenticator(self):
            return PasswordComparisonAuthenticator(self.context_source(), user_dn_patterns="uid={0},ou=people")

        @Object
        def authorities_populator(self):
            return DefaultLdapAuthoritiesPopulator(self.context_source(), group_search_filter="member={0}")

        @Object
        def provider(self):
            return LdapAuthenticationProvider(self.password_authenticator(), self.authorities_populator())

        @Object
        def manager(self):
            return AuthenticationManager(auth_providers=[self.provider()])

By default, *PasswordComparisonAuthenticator* handles SHA encrypted passwords as
well passwords stored in plain text. However, you can inject a custom
*PasswordEncoder* to support alternative password encoding schemes.

Future AuthenticationProviders
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

So far, Spring Python has implemented a DaoAuthenticationProvider than can link
with any database or use an in-memory user data structure, as well as an
LdapAuthenticationProvider. Future releases should include:

* *OpenIDAuthenticationProvider*
* Anonymous authentication provider - allows you to tag anonymous users, and
  constrain what they can access, even if they don't provide a password

AuthenticationManager
+++++++++++++++++++++

An AuthenticationManager holds a list of one or more AuthenticationProvider's,
and will go through the list when attempting to authenticate. PetClinic
configures it like this using :doc:`PythonConfig <objects-pythonconfig>`::

    class SampleContainer(PythonConfig):

        @Object
        def authenticationManager(self):
            return AuthenticationManager(auth_providers = [self.authenticationProvider()])

.. highlight:: xml

XML-based configuration with :doc`XMLConfig <objects-xmlconfig>`::

    <object id="authenticationManager" class="springpython.security.providers.AuthenticationManager">
        <property name="auth_providers">
            <list><ref object="authenticationProvider"/></list>
           </property>
    </object>

This *AuthenticationManager* has a list referencing one object already defined
in the *ApplicationContext*, authenticationProvider. The authentication manager
is supplied as an argument to the security interceptor, so it can perform
checks as needed.

Authorization
-------------

.. highlight:: python

After successful authentication, a user is granted various roles. The next
step of security is to determine if that user is authorized to conduct a
given operation or access a particular web page. The *AccessDecisionManager*
is called by the *AbstractSecurityInterceptor* and is responsible for making
final access control decisions. The *AccessDecisionManager* interface contains
two methods::

    def decide(self, authentication, object, config)
    def supports(self, attr)

As can be seen from the first method, the *AccessDecisionManager* is passed via
method parameters all information that is likely to be of value in assessing
an authorization decision. In particular, passing the secure object enables
those arguments contained in the actual secure object invocation to be inspected.
For example, let's assume the secure object was a *MethodInvocation*. It would
be easy to query the *MethodInvocation* for any Customer argument, and then
implement some sort of security logic in the *AccessDecisionManager* to ensure
the principal is permitted to operate on that customer. Implementations are
expected to throw an *AccessDeniedException* if access is denied.

Whilst users can implement their own *AccessDecisionManager* to control all
aspects of authorization, Spring Python Security includes several
*AccessDecisionManager* implementations that are based on voting. Using this
approach, a series of *AccessDecisionVoter* implementations are polled on an
authorization decision. The *AccessDecisionManager* then decides whether or
not to throw an *AccessDeniedException* based on its assessment of the votes.

The *AccessDecisionVoter* interface has two methods::

    def supports(self, attr)
    def vote(self, authentication, object, config)

Concrete implementations return an integer, with possible values being reflected
in the *AccessDecisionVoter* static fields ACCESS_ABSTAIN, ACCESS_DENIED and
ACCESS_GRANTED. A voting implementation will return ACCESS_ABSTAIN if it has
no opinion on an authorization decision. If it does have an opinion, it must
return either ACCESS_DENIED or ACCESS_GRANTED.

There are three concrete *AccessDecisionManagers* provided with Spring Python
Security that tally the votes. The *ConsensusBased* implementation will grant
or deny access based on the consensus of non-abstain votes. Properties are
provided to control behavior in the event of an equality of votes or if all
votes are abstain. The *AffirmativeBased* implementation will grant access if
one or more ACCESS_GRANTED votes were received (ie a deny vote will be ignored,
provided there was at least one grant vote). Like the *ConsensusBased*
implementation, there is a parameter that controls the behavior if all voters
abstain. The UnanimousBased provider expects unanimous ACCESS_GRANTED votes in
order to grant access, ignoring abstains. It will deny access if there is any
ACCESS_DENIED vote. Like the other implementations, there is a parameter that
controls the behavior if all voters abstain.

It is possible to implement a custom AccessDecisionManager that tallies votes
differently. For example, votes from a particular *AccessDecisionVoter* might
receive additional weighting, whilst a deny vote from a particular voter may
have a veto effect.

Python Security. The *RoleVoter* class will vote if any config attribute begins
with *ROLE_*. It will vote to grant access if there is a *GrantedAuthority* which
returns a string representation exactly equal to one or more config attributes
starting with *ROLE_*. If there is no exact match of any config attribute starting
with *ROLE_*, the *RoleVoter* will vote to deny access. If no config attribute
begins with *ROLE_*, the voter will abstain. *RoleVoter* is case sensitive on
comparisons as well as the *ROLE_* prefix.

PetClinic has two *RoleVoters* in its :doc:`Python-config based <objects-pythonconfig>`
configuration::

    class SampleContainer(PythonConfig):

        @Object
        def vetRoleVoter(self):
            return RoleVoter(role_prefix="VET")

        @Object
        def customerRoleVoter(self):
            return RoleVoter(role_prefix="CUSTOMER")

.. highlight:: xml

XML-based configuration with XMLConfig::

    <object id="vetRoleVoter" class="springpython.security.vote.RoleVoter">
        <property name="role_prefix"><value>VET</value></property>
    </object>

    <object id="customerRoleVoter" class="springpython.security.vote.RoleVoter">
        <property name="role_prefix"><value>CUSTOMER</value></property>
    </object>

The first one votes on VET authorities, and the second one votes on CUSTOMER authorities.

The other concrete *AccessDecisionVoter* is the *LabelBasedAclVoter*. It can be
seen in the test cases. Maybe later it will be incorporated into a demo.

.. highlight:: python

Petclinic has a custom *AccessDecisionVoter*, which votes on whether a user
"owns" a record::

    class SampleContainer(PythonConfig):
        ...
        @Object
        def ownerVoter(self):
            return OwnerVoter(controller = self.controller())

.. highlight:: xml

XML-based configuration using :doc:`XMLConfig <objects-xmlconfig>`::

    <object id="ownerVoter" class="controller.OwnerVoter">
        <property name="controller" ref="controller"/>
    </object>

This class is wired in the PetClinic controller module as part of the sample,
which demonstrates how easy it is to plugin your own custom security handler
to this module.

.. highlight:: python

PetClinic wires together these *AccessDecisionVoters* into an *AccessDecisionManager*::

    class SampleContainer(PythonConfig):

        @Object
        def accessDecisionManager(self):
            manager = AffirmativeBased()
            manager.allow_if_all_abstain = False
            manager.access_decision_voters = [self.vetRoleVoter(), self.customerRoleVoter(), self.ownerVoter()]
            return manager

.. highlight:: xml

XML-based configuration using :doc:`XMLConfig <objects-xmlconfig>`::

    <object id="accessDecisionManager" class="springpython.security.vote.AffirmativeBased">
        <property name="allow_if_all_abstain"><value>False</value></property>
        <property name="access_decision_voters">
            <list>
                <ref object="vetRoleVoter"/>
                <ref object="customerRoleVoter"/>
                <ref object="ownerVoter"/>
            </list>
        </property>
    </object>
