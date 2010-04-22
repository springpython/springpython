################################
# This stand-alone script is used to exercise the LDAP APIs. The intent is to get things working, and then
# replace this with an effective unit test.
################################

from springpython.security.providers import UsernamePasswordAuthenticationToken
from springpython.security.providers.Ldap import DefaultSpringSecurityContextSource
from springpython.security.providers.Ldap import BindAuthenticator
from springpython.security.providers.Ldap import PasswordComparisonAuthenticator
from springpython.security.providers.Ldap import DefaultLdapAuthoritiesPopulator
from springpython.security.providers.Ldap import LdapAuthenticationProvider

context = DefaultSpringSecurityContextSource(url="ldap://localhost:53389/dc=springframework,dc=org")
bindAuthenticator = BindAuthenticator(context_source=context, user_dn_patterns="uid={0},ou=people")
populator = DefaultLdapAuthoritiesPopulator(context_source=context, group_search_base="ou=groups")
authProvider = LdapAuthenticationProvider(ldap_authenticator=bindAuthenticator, ldap_authorities_populator=populator)

passwordAuthenticator = PasswordComparisonAuthenticator(context_source=context, user_dn_patterns="uid={0},ou=people")
authProvider2 = LdapAuthenticationProvider(ldap_authenticator=passwordAuthenticator, ldap_authorities_populator=populator)

authentication = UsernamePasswordAuthenticationToken(username="bob", password="bobspassword")

print "Input = %s" % authentication

auth1 = authProvider.authenticate(authentication)

print "Bind output = %s" % auth1


print "Input = %s" % authentication

auth2 = authProvider2.authenticate(authentication)

print "PasswordComparison output = %s" % auth2

