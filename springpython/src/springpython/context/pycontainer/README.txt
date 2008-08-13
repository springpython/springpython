PyContainer
version 0.4, 2004.09.05 
(C) 2004, Rafal Sniezynski

Documentation
=============

Documentation in HTML and PDF formats is in the doc subdirectory of the distribution.

License
=======

License details are in license.txt file in the root directory of the distribution.

====================================================================
(C) 2006 modified by Greg Turnquist

I have slightly modified the packaging of PyContainer so it can be used
inside SpringPython. The license, PKG-INFO, and README files have been
moved inside the pycontainer package folder. The setup.py script has
been moved to the doc folder for historical value, and the procedures
that were listed above about using setup.py have been removed.

The intention is to include this as a bundled component inside the 
distribution of SpringPython, and generally the features inside
ApplicationContext.

Edits:
- I had to edit one function used to access/instantiate factory modules
  to take into account the full path, "springpython.context.pycontainer", in
  place of the old "pycontainer" path.
- Upgraded the XML format to support lists like Spring does. Example shows a component
  defined as an authentication provider. Later on, another component needs to populate
  a property with a list. In this case, the list must include a reference to the earlier
  component.
  
  Before, the only values available were direct component references, or hard-coded lists,
  not lists of components.
  
  Now, you can mix either values or references. It seems to intelligently discern if the
  same local is being included more than once, and filters it out.
        <component id="authenticationProvider" class="prometheus.providers.InMemoryAuthenticationProvider">
        	<property name="userMap">
        		{
		        	"user1": ("password1", ["role1", "blue"], False),
		        	"user2": ("password2", ["role1", "orange"], False),
		  			"adminuser": ("password3", ["role1", "admin"], False),
		        	"disableduser": ("password4", ["role1", "blue"], True),
		        	"emptyuser": ("", [], False),
		        	"toomanyroles1": ("password5", ["blue", "orange"], False),
		        	"toomanyroles2": ("password6", ["orange", "admin"], False),
		        	"toomanyroles3": ("password7", ["blue", "admin"], False),
		        	"toomanyroles4": ("password8", ["blue", "admin"], False) 
	        	}
	        </property>
        </component>

        <component id="authenticationManager" class="prometheus.providers.AuthenticationManager">
        	<property name="authenticationProviderList">
        		<list local="authenticationProvider"/>
        	</property>
        </component>

  To have two entries in the list, try something like this:
        <component id="authenticationProvider" class="prometheus.providers.InMemoryAuthenticationProvider">
        	<property name="userMap">
        		{
		        	"user1": ("password1", ["role1", "blue"], False),
		        	"user2": ("password2", ["role1", "orange"], False),
		  			"adminuser": ("password3", ["role1", "admin"], False),
		        	"disableduser": ("password4", ["role1", "blue"], True),
		        	"emptyuser": ("", [], False),
		        	"toomanyroles1": ("password5", ["blue", "orange"], False),
		        	"toomanyroles2": ("password6", ["orange", "admin"], False),
		        	"toomanyroles3": ("password7", ["blue", "admin"], False),
		        	"toomanyroles4": ("password8", ["blue", "admin"], False) 
	        	}
	        </property>
        </component>

        <component id="authenticationProvider2" class="prometheus.providers.InMemoryAuthenticationProvider">
        	<property name="userMap">{"user1": ("password1", ["role1", "blue"], False)}</property>
        </component>
        
        <component id="authenticationManager" class="prometheus.providers.AuthenticationManager">
        	<property name="authenticationProviderList">
        		<list local="authenticationProvider"/>
        		<list local="authenticationProvider2"/>
        	</property>
        </component>

  It should support having either the local attribute configured with a component name, or use
  the embedded value tag.

- Changed initialization default policy to NON-lazy. All components are created automatically, unless overridden.

	<component id="thisComponentWillBeEagerlyInstantiated"                           class="some.sample.component"/>
	<component id="thisComponentIsTheSameAsThePrevious"                              class="some.sample.component" lazy-init="False"/>
	<component id="thisComponentWillOnlyBeCreatedWhenRequestedOrReferencedByAnother" class="some.sample.component" lazy-init="True"/>

  Also moved the reading of one or more application context files into PyContainer. This was necessary because only
  after reading all app context files, should NON-lazy instantiation be performed. Now, springpython.context.ApplicationContext
  is nothing more than a wrapper to give PyContainer a Spring look-and-feel.

- Pulled out pieces of interceptor logic to decouple from the container. Now that it works separately, have removed all pieces of
  interceptor logic from this module.
  
- pxdom appears to only have been used by pieces now removed. I have thus removed pxdom from the code base, and updated
  license statements appropriately.