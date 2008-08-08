#!/usr/bin/env python
"""
    Copyright 2007 Greg L. Turnquist, All Rights Reserved

    This script gathers together various Spring Python examples, and packages them
    for release. You must read each example to understand the licensing involved.
"""

from distutils.core import setup

setup(name='springpython-examples',
      version='0.5.0',
      description='Spring Python examples',
      long_description='A collection of small examples utilizing the features of Spring Python.',
      author='Greg L. Turnquist',
      author_email='gregturn at mindspring dot com',
      url='https://springpython.webfactional.com',
      license='GPLv3 (http://www.gnu.org/licenses/gpl.txt) and LGPLv3 (http://www.gnu.org/licenses/lgpl.html)',
      packages=['petclinic', 
                'petclinic.cherrypy',
                'petclinic.db',
                'springirc',
                'springwiki'],
      download_url="http://sourceforge.net/projects/springpython/",
      classifiers=["License :: OSI Approved :: GNU General Public License (GPL)",
                   "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
                   "Intended Audience :: Developers",
                   "Development Status :: 4 - Beta",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   "Programming Language :: Python",
                   "Operating System :: OS Independent"
                   ]
     )

