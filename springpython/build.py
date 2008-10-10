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
from glob import glob
import mimetypes
import os
import re
import sys
import getopt
import shutil
import S3

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
load_properties(p, p["s3.key_file"])  # Saves the user from having to manually input the keys

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
    print "\t--coverage\t\trun the test suite with coverage analysis, leaving all artifacts in %s" % p["testDir"]
    print "\t--package\t\tpackage everything up into a tarball for release to sourceforge in %s" % p["packageDir"]
    print "\t--build-stamp [tag]\tfor --package, this specifies a special tag, generating version tag '%s-<tag>'" % p["version"]
    print "\t\t\t\tIf this option isn't used, default will be tag will be '%s-<current time>'" % p["version"]
    print "\t--publish\t\tpublish this release to the deployment server"
    print "\t--register\t\tregister this release with http://pypi.python.org/pypi"
    print "\t--site\t\t\tcreate the site and all its related documents"
    print "\t--docs-html-multi\tgenerate HTML documentation, split up into separate sections"
    print "\t--docs-html-single\tgenerate HTML documentation in a single file"
    print "\t--docs-pdf\t\tgenerate PDF documentation"
    print "\t--docs-all\t\tgenerate all documents"
    print

try:
    optlist, args = getopt.getopt(sys.argv[1:],
                                  "hct",
                                  ["help", "clean", "test", "coverage", "package", "build-stamp=", \
                                   "publish", "register", \
                                   "site", "docs-html-multi", "docs-html-single", "docs-pdf", "docs-all"])
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

############################################################################
# Definition of operations this script can do.
############################################################################

def clean(dir):
    print "Removing '%s' directory" % dir
    if os.path.exists(dir):
        shutil.rmtree(dir)
    # TODO: Make this OS-independent
    os.system("find . -name '*.pyc' -exec rm -f {} \;")
    os.system("find . -name '*.class' -exec rm -f {} \;")

def test(dir):
    os.makedirs(dir)
    os.system("nosetests --with-nosexunit --source-folder=src --where=test/springpythontest --xml-report-folder=%s" % dir)
    
def test_coverage(dir):
    os.makedirs(dir)
    os.system("nosetests --with-nosexunit --source-folder=src --where=test/springpythontest --xml-report-folder=%s --with-coverage --cover-package=springpython" % dir)

def build(dir, version):
    input = open(dir + "/build.py")
    output = open(dir + "/setup.py", "w") 
    for line in input.readlines():
        skip = ["sys.argv =", "parser = OptionParser", "parser.add_option", "(options, args)", "# NOTE:", "# Remove version argument", "from optparse"]
        if len([True for criteria in skip if criteria in line]) > 0:
            continue
        if "options.version" in line:
            output.write(re.sub("options.version", "'" + version + "'", line))
            continue
        output.write(line)
    output.close()
    os.system("cd %s ; python build.py --version %s sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % (dir, version))

def package(dir, version):
    os.makedirs(dir)
    build("src", version)
    build("samples", version)
    os.system("mv *.tar.gz %s" % dir)

def publish(filename, BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
    KEY_NAME = p["s3.key_prefix"] + filename.split("/")[-1]

    print "Reading in content from %s" % filename
    filedata = open(filename, "rb").read()

    content_type = mimetypes.guess_type(filename)[0]
    if content_type is None:
        content_type = 'text/plain'

    print "File appears to be %s" % content_type

    print "Connecting to S3..."
    conn = S3.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

    print "Checking if bucket %s exists..." % BUCKET_NAME
    check = conn.check_bucket_exists(BUCKET_NAME)
    if (check.status == 200):
        print "It does! Now uploading %s to %s/%s" % (filename, BUCKET_NAME, KEY_NAME)
        print conn.put(
            BUCKET_NAME,
            KEY_NAME,
            S3.S3Object(filedata),
            { 'Content-Type': content_type, 'x-amz-acl': 'public-read'}).message
    else:
        print "Error code %s: Unable to publish" % check.status

def register(version):
    os.system("cd src     ; python setup.py --version %s register" % version)
    os.system("cd samples ; python setup.py --version %s register" % version)

# Using glob, generate a list of files, then use map to go over each item, and copy it
# from source to destination.
def copy(src, dest, patterns):
    if not os.path.exists(dest):
        print "+++ Creating " + dest
        os.makedirs(dest)
    
    map(lambda pattern: [shutil.copy(file, dest) for file in glob(src + pattern)], patterns)

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

def sub_version(cur):
    f = open(cur + "/" + p["doc.ref.dir"] + "/src/index.xml")
    lines = "".join(f.readlines())
    changed = re.sub(r"{version}", p["version"], lines)
    f.close()
    f = open(cur + "/" + p["doc.ref.dir"] + "/src/mangled.xml", "w")
    f.write(changed)
    f.close()

def site(version):
    docs_all(version)
    cur = os.path.abspath(".")
    shutil.copy(cur + "/docs/spring.ico", p["targetDir"]+"/docs/favicon.ico")
    os.system("mvn -Dspringpython.version=%s site" % version)
    os.system("cp docs/resources/css/* target/docs/css/")

def docs_all(version):
    copy("xml/schema/context/", p["targetDir"] + "/docs/schema/context/", ["*.xsd"])

    docs_multi(version)
    docs_single(version)
    docs_pdf(version)
    
def docs_multi(version):
    root = p["targetDir"] + "/" + p["dist.ref.dir"] + "/html"
    print root

    setup(root)

    cur = os.path.abspath(".")
    sub_version(cur)
    os.chdir(root)
    ref = cur + "/" + p["doc.ref.dir"]
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx80M -XX:MaxPermSize=80m com.icl.saxon.StyleSheet " + \
        ref+"/src/mangled.xml " + ref+"/styles/html_chunk.xsl")
    os.remove(ref+"/src/mangled.xml")
    os.chdir(cur)

def docs_single(version):
    root = p["targetDir"] + "/" + p["dist.ref.dir"] + "/html_single"
    
    setup(root)
    
    cur = os.path.abspath(".")
    sub_version(cur)
    os.chdir(root)
    ref = cur + "/" + p["doc.ref.dir"]
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx80M -XX:MaxPermSize=80m com.icl.saxon.StyleSheet " + \
        "-o index.html " + ref+"/src/mangled.xml " + ref+"/styles/html.xsl")
    
    os.remove(ref+"/src/mangled.xml")
    os.chdir(cur)

def docs_pdf(version):
    root = p["targetDir"] + "/" + p["dist.ref.dir"] + "/pdf"
    
    setup(root, stylesheets=False)
   
    cur = os.path.abspath(".")
    sub_version(cur)
    os.chdir(root)
    ref = cur + "/" + p["doc.ref.dir"]
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx80M -XX:MaxPermSize=80m com.icl.saxon.StyleSheet " + \
        "-o docbook_fop.tmp " + ref+"/src/mangled.xml " + ref+"/styles/fopdf.xsl double.sided=" + p["double.sided"])
    os.system("java -classpath " + os.path.pathsep.join(glob(ref + "/lib/*.jar")) + \
        " -Xmx80M -XX:MaxPermSize=80m org.apache.fop.apps.Fop " + \
        "docbook_fop.tmp springpython-reference.pdf")
    os.remove("docbook_fop.tmp")
    os.remove(ref+"/src/mangled.xml")
    os.chdir(cur)


############################################################################
# Pre-commands. Skim the options, and pick out commands the MUST be
# run before others.
############################################################################

# No matter what order the command are specified in, the build-stamp must be extracted first.
for option in optlist:
    if option[0] == "--build-stamp":
        buildStamp = option[1]   # Override build stamp with user-supplied version

if "build.stamp" in p:
    completeVersion = p["build.stamp"]
else:
    completeVersion = p["version"] + "-" + buildStamp

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
        test(p["testDir"])

    if option[0] in ("--coverage"):
        test_coverage(p["testDir"])

    if option[0] in ("--package"):
        package(p["packageDir"], completeVersion)
	
    if option[0] in ("--publish"):
        BUCKET_NAME = p["s3.bucket"]
        if "accessKey" in p:
            AWS_ACCESS_KEY_ID = p["accessKey"]
        else: 
            AWS_ACCESS_KEY_ID = raw_input("Please enter the AWS_ACCESS_KEY_ID (NOT your secret key): ")
        if "secretKey" in p:
            AWS_SECRET_ACCESS_KEY = p["secretKey"]
        else:
            AWS_SECRET_ACCESS_KEY = raw_input("Please enter AWC_SECRET_ACCESS_KEY: ")

        [publish(filename, BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) for filename in glob("target/artifacts/*.tar.gz")]

    if option[0] in ("--register"):
        register(completeVersion)

    if option[0] in ("--site"):
        site(completeVersion)

    if option[0] in ("--docs-all"):
        docs_all(completeVersion)
                
    if option[0] in ("--docs-html-multi"):
        docs_multi(completeVersion)

    if option[0] in ("--docs-html-single"):
        docs_single(completeVersion)

    if option[0] in ("--docs-pdf"):
        docs_pdf(completeVersion)
    

