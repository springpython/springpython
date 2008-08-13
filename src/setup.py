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
import sys
from distutils.core import setup

if sys.version_info < (2, 3):
    print "Spring Python only supports Python 2.3 and higher"
    sys.exit(1)

setup(name='springpython',
      version='0.6.0',
      description='Spring Python',
      long_description='Spring Python is an offshoot of the Java-based SpringFramework, targeted for Python. Spring provides many useful features, and I wanted those same features available when working with Python.',
      author='Greg L. Turnquist',
      author_email='gregturn at mindspring dot com',
      url='https://springpython.webfactional.com',
      platforms = ["Python >= 2.3"],
      license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
      packages=['springpython', 
                'springpython.aop', 
                'springpython.context',
                'springpython.context.pycontainer', 
                'springpython.database', 
                'springpython.remoting', 
                'springpython.remoting.pyro', 
                'springpython.security',
                'springpython.security.context',
                'springpython.security.providers',
                'springpython.security.userdetails'
                ],
      package_data={'springpython': ["README", "NOTICE", "LICENSE.txt"]},
      download_url="http://sourceforge.net/projects/springpython/",
      classifiers=["License :: OSI Approved :: Apache Software License",
                   "Intended Audience :: Developers",
                   "Development Status :: 4 - Beta",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Programming Language :: Python",
                   "Operating System :: OS Independent"
                   ]
      
     )

