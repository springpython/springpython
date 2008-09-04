#!/usr/bin/python
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
from datetime import datetime
import os
import sys
import getopt
import shutil

############################################################################
# Get external properties and load into a dictionary. NOTE: These properties
# files mimic Java props files.
############################################################################

properties = {}

# Default settings, before reading the properties file
properties["targetDir"] = "target"
properties["testDir"] = "%s/test-results/xml" % properties["targetDir"]
properties["packageDir"] = "%s/artifacts" % properties["targetDir"]

# Override defaults with a properties file
inputProperties = [property.split("=") for property in open("springpython.properties").readlines()
                   if not (property.startswith("#") or property.strip() == "")]
filter(properties.update, map((lambda prop: {prop[0]: prop[1]}), inputProperties))

############################################################################
# Read the command-line, and assemble commands. Any invalid command, print
# usage info, and EXIT.
############################################################################

def usage():
    """This function is used to print out help either by request, or if an invalid option is used."""
    print
    print "Usage: python build.py [command]"
    print
    print "\t--help\t\t\tprint this help message"
    print "\t--clean\t\t\tclean out this build by deleting the %s directory" % properties["targetDir"]
    print "\t--test\t\t\trun the test suite, leaving all artifacts in %s" % properties["testDir"]
    print "\t--package\t\tpackage everything up into a tarball for release to sourceforge in %s" % properties["packageDir"]
    print "\t--build-stamp [tag]\tfor --package, this specifies a special tag, generating version tag '%s-<tag>'" % properties["version"]
    print "\t\t\t\tIf this option isn't used, default will be tag will be '%s-<current time>'" % properties["version"]
    print "\t--publish\t\tpublish this release to the deployment server"
    print "\t--register\t\tregister this release with http://pypi.python.org/pypi"
    print

try:
    optlist, args = getopt.getopt(sys.argv[1:], "hct", ["help", "clean", "test", "package", "build-stamp="])
except getopt.GetoptError:
    # print help information and exit:
    print "Invalid command found in %s" % sys.argv
    usage()
    sys.exit(2)

############################################################################
# Pre-generate needed values
############################################################################

# Default build stamp value
buildStamp = "BUILD-%s" % datetime.now().strftime("%Y%m%d%H%M%S")
print "Commands: %s" % optlist

############################################################################
# Definition of operations this script can do.
############################################################################

def clean(dir):
    print "Removing '%s' directory" % dir
    if os.path.exists(dir):
        shutil.rmtree(dir)

def test(dir):
    os.makedirs(dir)
    os.system("nosetests --with-nosexunit --source-folder=src --where=test/springpythontest --xml-report-folder=%s" % dir)

def package(dir, version):
    os.makedirs(dir)
    os.system("cd src ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % version)
    #os.system("cd samples ; python setup.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % version)
    os.system("mv *.tar.gz %s" % dir)

def publish():
    """TODO(8/28/2008 GLT): Implement automated solution for this."""
    print "+++ Upload the tarballs using sftp manually to <user>@frs.sourceforge.net, into dir uploads and create a release."

def register(version):
    """TODO(8/28/2008 GLT): Test this part when making official release and registering to PyPI."""
    os.system("cd src ; python setup.py --version %s register" % version)
    #os.system("cd samples ; python setup.py --version %s register" % completeVersion)

############################################################################
# Pre-commands. Skim the options, and pick out commands the MUST be
# run before others.
############################################################################

# No matter what order the command are specified in, the build-stamp must be extracted first.
for option in optlist:
    if option[0] == "--build-stamp":
        buildStamp = option[1]   # Override build stamp with user-supplied version
completeVersion = properties["version"] + "-" + buildStamp

# Check for help requests, which cause all other options to be ignored. Help can offer version info, which is
# why it comes as the second check
for option in optlist:
    if option[0] in ("--help", "-h"):
        usage()
        sys.exit(1)
        
for option in optlist:
    if option[0] in ("--clean", "-c"):
        clean(properties["targetDir"])

############################################################################
# Main commands. Skim the options, and run each command as its found.
# Commands are run in the order found ON THE COMMAND LINE.
############################################################################

# Parse the arguments, in order
for option in optlist:
    if option[0] in ("--test"):
        test(properties["testDir"])
        package(properties["packageDir"], completeVersion)

    if option[0] in ("--package"):
        package(properties["packageDir"], completeVersion)
	
    if option[0] in ("--publish"):
        publish()

    if option[0] in  ("--register"):
        register(completeVersion)

