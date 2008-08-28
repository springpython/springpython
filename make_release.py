#!/usr/bin/python
"""
    Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved

    This script is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
from optparse import OptionParser

"""This script is a shortcut to making the python distribution releases. This should be run from the folder it is in."""

# This is the base version of this release.
version = "0.6.0"

parser = OptionParser(usage="usage: %prog [-h|--help] [options]")
parser.add_option("-c", "--clean", action="store_true", dest="clean", default=False, help="Clean out current target build.")
parser.add_option("-b", "--build", action="store_true", dest="package", default=False, help="Same as the package option.")
parser.add_option("-v", "--version", action="store", dest="version", default="", help="For --package, this specifies a special tag, generate version tag %s-<version>" % version)
parser.add_option("-t", "--test", action="store_true", dest="test", default=False, help="Test everything, generating JUnit-style XML outputs.")
parser.add_option("", "--package", action="store_true", dest="package", default=False, help="Package everything up into a tarball for release to sourceforge.")
parser.add_option("", "--publish", action="store_true", dest="publish", default=False, help="Publish this release to the deployment server.")
parser.add_option("-r", "--register", action="store_true", dest="register", default=False, help="Register this release with http://pypi.python.org/pypi")
(options, args) = parser.parse_args()

if options.version:
    version += "-%s" % options.version

if options.clean:
    print "Cleaning out the target directory"
    os.system("rm -rf target")
            
elif options.test:
    os.system("mkdir -p target/test-results")
    os.system("nosetests --with-nosexunit --source-folder=src --where=test/springpythontest --xml-report-folder=target/test-results")

elif options.package:
    os.system("mkdir -p target/test-results")
    os.system("cd src ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % version)
    os.system("cd samples ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % version)
    os.system("mv *.tar.gz target")
	
elif options.publish:
    # TODO(8/28/2008 GLT): Implement automated solution for this.
	print "+++ Upload the tarballs using sftp manually to <user>@frs.sourceforge.net, into dir uploads and create a release."

elif options.register:
    # TODO(8/28/2008 GLT): Test this part when making official release and registering to PyPI.
	os.system("cd src ; python setup.py --version %s register" % version)
	os.system("cd samples ; python setup.py --version %s register" % version)

