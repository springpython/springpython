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
from datetime import datetime
import os
import sys
from optparse import OptionParser

# Read in the properties file, and parse it into a dictionary
properties = {}
inputProperties = [property.split("=") for property in open("springpython.properties").readlines()
                   if not (property.startswith("#") or property.strip() == "")]
filter(properties.update, map((lambda prop: {prop[0]: prop[1]}), inputProperties))

version = properties["version"]

parser = OptionParser(usage="usage: %prog [-h|--help] [options]")
parser.add_option("-c", "--clean", action="store_true", dest="clean", default=False, help="clean out current target build.")
parser.add_option("-b", "--build", action="store_true", dest="package", default=False, help="same as the package option.")
parser.add_option("", "--build-stamp", action="store", dest="buildStamp", default="BUILD-%s" % datetime.now().strftime("%Y%m%d%H%M%S"), help="for --package, this specifies a special tag, generating version tag '%s-<build-stamp>'. Default: '%s-<current time>'." % (version, version))
parser.add_option("-t", "--test", action="store_true", dest="test", default=False, help="test everything, generating JUnit-style XML outputs.")
parser.add_option("", "--package", action="store_true", dest="package", default=False, help="package everything up into a tarball for release to sourceforge.")
parser.add_option("", "--publish", action="store_true", dest="publish", default=False, help="publish this release to the deployment server.")
parser.add_option("-r", "--register", action="store_true", dest="register", default=False, help="register this release with http://pypi.python.org/pypi")
(options, args) = parser.parse_args()   # options is a dictionary, meaning we lost the order the commands came in

completeVersion = version + "-" + options.buildStamp

# NOTE: These options are listed in the order expected to run!!! For example,
# ./build.py --clean --test
# and
# ./build.py --test --clean
# ...will both run the same options, in the order of clean followed by test.

if options.clean:
    print "Cleaning out the target directory"
    os.system("rm -rf target")
            
if options.test:
    os.system("mkdir -p target/test-results/xml")
    os.system("nosetests --with-nosexunit --source-folder=src --where=test/springpythontest --xml-report-folder=target/test-results/xml")

if options.package:
    os.system("mkdir -p target/artifacts")
    os.system("cd src ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % completeVersion)
    os.system("cd samples ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % completeVersion)
    os.system("mv *.tar.gz target/artifacts")
	
if options.publish:
    # TODO(8/28/2008 GLT): Implement automated solution for this.
	print "+++ Upload the tarballs using sftp manually to <user>@frs.sourceforge.net, into dir uploads and create a release."

if options.register:
    # TODO(8/28/2008 GLT): Test this part when making official release and registering to PyPI.
	os.system("cd src ; python setup.py --version %s register" % completeVersion)
	os.system("cd samples ; python setup.py --version %s register" % completeVersion)

