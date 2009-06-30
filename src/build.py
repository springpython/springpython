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
import re
import sys
from distutils.core import setup

if sys.version_info < (2, 4):
    print "Spring Python only supports Python 2.4 and higher"
    sys.exit(1)

setup(name='springpython',
      version='${version}',
      description='Spring Python',
      long_description='Spring Python is an offshoot of the Java-based SpringFramework, targeted for Python. Spring provides many useful features, and I wanted those same features available when working with Python.',
      author='Greg L. Turnquist',
      author_email='gregturn at mindspring dot com',
      url='http://springpython.webfactional.com',
      platforms = ["Python >= 2.4"],
      license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
      scripts=['plugins/coily'],
      packages=['springpython', 
                'springpython.aop', 
                'springpython.config',
                'springpython.container',
                'springpython.context',
                'springpython.database', 
                'springpython.factory', 
                'springpython.remoting', 
                'springpython.remoting.hessian', 
                'springpython.remoting.pyro', 
                'springpython.security',
                'springpython.security.context',
                'springpython.security.providers',
                'springpython.security.userdetails'
                ],
      package_data={'springpython': ["README", "COPYRIGHT", "LICENSE.txt"]},
      download_url="${download_url}",
      classifiers=["License :: OSI Approved :: Apache Software License",
                   "Intended Audience :: Developers",
                   "Development Status :: 5 - Production/Stable",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Programming Language :: Python",
                   "Operating System :: OS Independent"
                   ]
      
     )

