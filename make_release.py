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

def main(argv):
    """This script is a shortcut to making the python distribution releases. This should be run from the folder it is in."""
    
    parser = OptionParser(usage="usage: %prog [-h|--help] [options]")
    parser.add_option("-c", "--clean", action="store_true", dest="clean", default=False, help="Clean out current target build.")
    parser.add_option("-b", "--build", action="store", dest="build", help="Build everything, and optionally put a special tag on the end of the version.")
    parser.add_option("-t", "--test", action="store_true", dest="test", default=False, help="Test everything, generating JUnit-style XML outputs.")
    parser.add_option("", "--package", action="store_true", dest="package", default=False, help="Package everything up into a tarball for release to sourceforge.")
    parser.add_option("", "--publish", action="store_true", dest="publish", default=False, help="Publish this release to the deployment server.")
    parser.add_option("-r", "--register", action="store_true", dest="register", default=False, help="Register this release with http://pypi.python.org/pypi")
    (options, args) = parser.parse_args()

    parser.set_defaults(build="")

    if options.clean:
        print "Cleaning out the target directory"
        os.system("rm -rf target")
                
    elif options.build is not "":
        print "+++ Working on this option."

    elif options.build:
        print "+++ Working on this option."

    elif options.package:
    	# Make the main source code distribution
    	os.system("cd src ; python setup.py sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST ")
    
    	# Make the sample distribution
    	os.system("cd samples ; python setup.py sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST ")
    	
    elif options.publish:
    	print "+++ Upload the tarballs using sftp manually to <user>@frs.sourceforge.net, into dir uploads and create a release."
    
    elif options.register:
    	os.system("cd src ; python setup.py register")
    	os.system("cd samples ; python setup.py register")
		

if __name__ == "__main__":
	main(sys.argv[1:])
