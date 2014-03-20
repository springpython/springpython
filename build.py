#!/usr/bin/python
"""
   Copyright 2006-2011 SpringSource (http://springsource.com), All Rights Reserved 

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
from glob import glob
import logging
import mimetypes
import os
import pydoc
import re
import sys
import tarfile
import getopt
import shutil

try:
    import hashlib
    _sha = hashlib.sha1
except ImportError:
    import sha
    _sha = sha.new

############################################################################
# Get external properties and load into a dictionary. NOTE: These properties
# files mimic Java props files.
############################################################################

p = {}

# Default settings, before reading the properties file
p["targetDir"] = "target"
p["testDir"] = "%s/test-results/xml" % p["targetDir"]
p["packageDir"] = "%s/artifacts" % p["targetDir"]


def load_properties(prop_dict, prop_file):
    "This function loads standard, java-style properties files into a dictionary."
    if os.path.exists(prop_file):
        print "Reading property file " + prop_file
        [prop_dict.update({prop.split("=")[0].strip(): prop.split("=")[1].strip()})
         for prop in open(prop_file).readlines() if not (prop.startswith("#") or prop.strip() == "")]
    else:
        print "Unable to read property file " + prop_file

# Override defaults with a properties file
load_properties(p, "springpython.properties")

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
    print "\t--clean\t\t\tclean out this build by deleting the %s directory" % p["targetDir"]
    print "\t--test\t\t\trun the test suite, leaving all artifacts in %s" % p["testDir"]
    print "\t--suite [suite]\t\trun a specific test suite, leaving all artifacts in %s" % p["testDir"]
    print "\t--coverage\t\trun the test suite with coverage analysis, leaving all artifacts in %s" % p["testDir"]
    print "\t--debug-level [info|debug]\n\t\t\t\tthreshold of logging message when running tests or coverage analysis"
    print "\t--package\t\tpackage everything up into a tarball for release to sourceforge in %s" % p["packageDir"]
    print "\t--build-stamp [tag]\tfor --package, this specifies a special tag, generating version tag '%s.<tag>. springpython.properties can override with build.stamp'" % p["version"]
    print "\t\t\t\tIf this option isn't used, default will be tag will be '%s.<current time>'" % p["version"]
    print "\t--register\t\tregister this release with http://pypi.python.org/pypi"
    print "\t--docs-sphinx\t\tgenerate Sphinx documentation"
    print "\t--pydoc\t\t\tgenerate pydoc information"
    print

try:
    optlist, args = getopt.getopt(sys.argv[1:],
                                  "hct",
                                  ["help", "clean", "test", "suite=", "debug-level=", "coverage", "package", "build-stamp=", \
                                   "register", "docs-sphinx", "pydoc"])
except getopt.GetoptError:
    # print help information and exit:
    print "Invalid command found in %s" % sys.argv
    usage()
    sys.exit(2)

############################################################################
# Pre-generate needed values
############################################################################

# Default build stamp value
build_stamp = "BUILD-%s" % datetime.now().strftime("%Y%m%d%H%M%S")

############################################################################
# Definition of operations this script can do.
############################################################################

def clean(dir):
    print "Removing '%s' directory" % dir
    if os.path.exists(".coverage"):
       os.remove(".coverage")
    if os.path.exists(dir):
        shutil.rmtree(dir, True)
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            if name.endswith(".pyc") or name.endswith(".class"):
                os.remove(os.path.join(root, name))
                
def test(dir, test_suite, debug_level):
    """
    Run nose programmatically, so that it uses the same python version as this script uses
    
    Nose expects to receive a sys.argv, of which the first arg is the script path (usually nosetests). Since this isn't 
    being run that way, a filler entry was created to satisfy the library's needs.
    """
    if not os.path.exists(dir):
        os.makedirs(dir)
    
    try:
        import java
        if test_suite == "checkin": test_suite = "jython"
        _run_nose(argv=["", "--where=test/springpythontest", test_suite], debug_level=debug_level)
    except ImportError:
        _run_nose(argv=["", "--with-nosexunit", "--source-folder=src", "--where=test/springpythontest", "--xml-report-folder=%s" % dir, test_suite], debug_level=debug_level)
    
def test_coverage(dir, test_suite, debug_level):
    """
    Run nose programmatically, so that it uses the same python version as this script uses

    Nose expects to receive a sys.argv, of which the first arg is the script path (usually nosetests). Since this isn't
    being run that way, a filler entry was created to satisfy the library's needs.
    """

    if not os.path.exists(dir):
        os.makedirs(dir)

    _run_nose(argv=["", "--with-nosexunit", "--source-folder=src", "--where=test/springpythontest", "--xml-report-folder=%s" % dir, "--with-coverage", "--cover-package=springpython", test_suite], debug_level=debug_level)

def _run_nose(argv, debug_level):
    logger = logging.getLogger("springpython")
    loggingLevel = debug_level
    logger.setLevel(loggingLevel)
    ch = logging.StreamHandler()
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    # Running nose causes the stdout/stderr to get changed, and also it changes directories as well.
    _stdout, _stderr, _curdir = sys.stdout, sys.stderr, os.getcwd()

    import nose
    nose.run(argv=argv)

    # Restored these streams
    sys.stdout, sys.stderr = _stdout, _stderr
    os.chdir(_curdir)

def _substitute(input_file, output_file, patterns_to_replace):
    """Scan the input file, and do a pattern substitution, writing all results to output file."""
    input = open(input_file).read()
    output = open(output_file, "w")
    for pattern, replacement in patterns_to_replace:
        input = re.compile(r"\$\{%s}" % pattern).sub(replacement, input)
    output.write(input)
    output.close()

def build(dir, version, s3bucket, filepath):
    filename = filepath.split("/")[-1]
    s3key = "/".join([ p['release.type'],
                       p['project.key'],
                       filename ])

    patterns_to_replace = [("version", version)]

    _substitute(dir + "/setup-template.py", dir + "/setup.py", patterns_to_replace)
    
    os.chdir(dir)
    os.system("%s %s sdist" % (sys.executable, os.path.join(".", "setup.py")))
    os.chdir("..")
    
    dist_dir = os.path.join(os.getcwd(), dir, "dist")
    
    for name in os.listdir(dist_dir):
        old_location = os.path.join(dist_dir,name)
        new_location = "."
        shutil.move(old_location, new_location)
        
    os.rmdir(dist_dir)
    if os.path.exists(os.path.join(dir, "MANIFEST")):
        os.remove(os.path.join(dir, "MANIFEST"))
    
def package(dir, version, s3bucket, src_filename, sample_filename):
    if not os.path.exists(dir):
        os.makedirs(dir)

    _substitute("src/plugins/coily-template", "src/plugins/coily", [("version", version)])
    os.chmod("src/plugins/coily", 0755)
    build("src", version, s3bucket, src_filename)
    build("samples", version, s3bucket, sample_filename)
    #os.remove("src/plugins/coily")
    
    for name in glob("*.tar.gz"):
        old_location = os.path.join(".", name)
        shutil.move(old_location, dir)

    curdir = os.getcwd()
    os.chdir("src/plugins")
    for item in os.listdir("."):
        if item in ["coily-template", ".svn"]: continue
        t = tarfile.open("../../%s/springpython-plugin-%s.%s.tar.gz" % (dir, item, version), "w:gz")
        for path, dirs, files in os.walk(item):
            if ".svn" not in path:  # Don't want to include version information
                t.add(path, recursive=False)
                [t.add(path + "/" + file, recursive=False) for file in files]
        t.close()
    os.chdir(curdir)

def register():
    os.system("cd src     ; %s setup.py register sdist upload" % sys.executable)
    os.system("cd samples ; %s setup.py register sdist upload" % sys.executable)

def copy(src, dest, patterns):
    if not os.path.exists(dest):
        print "+++ Creating " + dest
        os.makedirs(dest)
    
    [shutil.copy(file, dest) for pattern in patterns for file in glob(src + pattern)]
    
def setup(root, stylesheets=True):
    copy(
         p["doc.ref.dir"]+"/src/images/",
         root + "/images/",
         ["*.gif", "*.svg", "*.jpg", "*.png"])

    docbook_images_dir = p["targetDir"] + "/" + p["dist.ref.dir"] + "/images"
    if not os.path.exists(docbook_images_dir):
        shutil.copytree(p["doc.ref.dir"]+"/images/", docbook_images_dir)

    if stylesheets:
        copy(
             p["doc.ref.dir"]+"/styles/",
             root,
             ["*.css", "*.js"])

def sub_version(cur, version):
    _substitute(cur + "/" + p["doc.ref.dir"] + "/src/index.xml", cur + "/" + p["doc.ref.dir"] + "/src/mangled.xml", [("version", version)])

def docs_sphinx():
    cur = os.getcwd()
    os.chdir("docs/sphinx")
    os.system("make clean html epub man")
    os.chdir(cur)
    shutil.copytree("docs/sphinx/build/html", "target/docs/sphinx/html")
    shutil.copytree("docs/sphinx/build/man", "target/docs/sphinx/man")
    shutil.copy("docs/sphinx/build/epub/SpringPython.epub", "target/docs/")

def create_pydocs():
    sys.path.append(os.getcwd() + "/src")
    import springpython

    if not os.path.exists("target/docs/pydoc"):
        os.makedirs("target/docs/pydoc")
 
    cur = os.getcwd()
    os.chdir("target/docs/pydoc")

    pydoc.writedoc("springpython")
    pydoc.writedoc("springpython.aop")
    pydoc.writedoc("springpython.aop.utils")
    pydoc.writedoc("springpython.config")
    pydoc.writedoc("springpython.config.decorator")
    pydoc.writedoc("springpython.container")
    pydoc.writedoc("springpython.context")
    pydoc.writedoc("springpython.context.scope")
    pydoc.writedoc("springpython.database")
    pydoc.writedoc("springpython.database.core")
    pydoc.writedoc("springpython.database.factory")
    pydoc.writedoc("springpython.database.transaction")
    pydoc.writedoc("springpython.factory")
    pydoc.writedoc("springpython.remoting")
    pydoc.writedoc("springpython.remoting.hessian")
    pydoc.writedoc("springpython.remoting.hessian.hessianlib")
    pydoc.writedoc("springpython.remoting.pyro")
    pydoc.writedoc("springpython.remoting.pyro.PyroDaemonHolder")
    pydoc.writedoc("springpython.security")
    pydoc.writedoc("springpython.security.cherrypy3")
    pydoc.writedoc("springpython.security.intercept")
    pydoc.writedoc("springpython.security.context")
    pydoc.writedoc("springpython.security.context.SecurityContextHolder")
    pydoc.writedoc("springpython.security.providers")
    pydoc.writedoc("springpython.security.providers.dao")
    pydoc.writedoc("springpython.security.providers.encoding")
    pydoc.writedoc("springpython.security.providers.Ldap")
    pydoc.writedoc("springpython.security.providers._Ldap_cpython")
    pydoc.writedoc("springpython.security.providers._Ldap_jython")
    pydoc.writedoc("springpython.security.userdetails")
    pydoc.writedoc("springpython.security.userdetails.dao")
    pydoc.writedoc("springpython.security.web")

    top_color = "#7799ee"
    pkg_color = "#aa55cc"
    class_color = "#ee77aa"
    class_highlight = "#ffc8d8"
    function_color = "#eeaa77"
    data_color = "#55aa55"

    for file in os.listdir("."):
        if "springpython" not in file: continue
        print "Altering appearance of %s" % file
        file_input = open(file).read()
        file_input = re.compile(top_color).sub("GREEN", file_input)
        file_input = re.compile(pkg_color).sub("GREEN", file_input)
        file_input = re.compile(class_color).sub("GREEN", file_input)
        file_input = re.compile(class_highlight).sub("LIGHTGREEN", file_input)
        file_input = re.compile(function_color).sub("LIGHTGREEN", file_input)
        file_input = re.compile(data_color).sub("LIGHTGREEN", file_input)
        file_output = open(file, "w")
        file_output.write(file_input)
        file_output.close()

    os.chdir(cur)


############################################################################
# Pre-commands. Skim the options, and pick out commands the MUST be
# run before others.
############################################################################

debug_levels = {"info":logging.INFO, "debug":logging.DEBUG}
debug_level = debug_levels["info"]  # Default debug level is INFO

# No matter what order the command are specified in, the build-stamp must be extracted first.
for option in optlist:
    if option[0] == "--build-stamp":
        build_stamp = option[1]   # Override build stamp with user-supplied version

    if option[0] in ("--debug-level"):
        debug_level = debug_levels[option[1]]    # Override with a user-supplied debug level

# However, a springpython.properties entry can override the command-line
if "build.stamp" in p:
    build_stamp = p["build.stamp"]
complete_version = p["version"] + "." + build_stamp

# However, a springpython.properties entry can override the command-line
if "debug.level" in p:
    debug_level = debug_levels[p["debug.level"]]

# Check for help requests, which cause all other options to be ignored. Help can offer version info, which is
# why it comes as the second check
for option in optlist:
    if option[0] in ("--help", "-h"):
        usage()
        sys.exit(1)
        
############################################################################
# Main commands. Skim the options, and run each command as its found.
# Commands are run in the order found ON THE COMMAND LINE.
############################################################################

# Parse the arguments, in order
for option in optlist:
    if option[0] in ("--clean", "-c"):
        clean(p["targetDir"])

    if option[0] in ("--test"):
        print "Running checkin tests..."
        test(p["testDir"], "checkin", debug_level)

    if option[0] in ("--suite"):
        print "Running test suite %s..." % option[1]
        test(p["testDir"], option[1], debug_level)

    if option[0] in ("--coverage"):
        test_coverage(p["testDir"], "checkin", debug_level)

    if option[0] in ("--package"):
        package(p["packageDir"], complete_version, p['s3.bucket'], "springpython", "springpython-samples")
	
    if option[0] in ("--register"):
        register()

    if option[0] in ("--docs-sphinx"):
        docs_sphinx()

    if option[0] in ("--pydoc"):
        create_pydocs()
    

