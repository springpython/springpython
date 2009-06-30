#!/usr/bin/env python
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

"""
NOTE: This setup.py lists two licenses, Apache Server License and GPL. That is because
the stylesheet inside SpringWiki is GPL. Everything else is ASL.
"""
import re
import sys
from distutils.core import setup
from optparse import OptionParser

setup(name='springpython-samples',
      version='${version}',
      description='Spring Python samples',
      long_description='A collection of small samples utilizing the features of Spring Python.',
      author='Greg L. Turnquist',
      author_email='gregturn at mindspring dot com',
      url='http://springpython.webfactional.com',
      license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
      packages=['basic',
                'petclinic', 
                'petclinic.cherrypy',
                'petclinic.db',
                'springirc',
                'springwiki'],
      download_url="${download_url}",
      classifiers=["License :: OSI Approved :: GNU General Public License (GPL)",
                   "License :: OSI Approved :: Apache Software License",
                   "Intended Audience :: Developers",
                   "Development Status :: 5 - Production/Stable",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Programming Language :: Python",
                   "Operating System :: OS Independent"
                   ]
     )

