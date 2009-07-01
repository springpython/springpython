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
import pydoc
import re
import sys
import tarfile
import getopt
import shutil
import S3

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
    print "\t--coverage\t\trun the test suite with coverage analysis, leaving all artifacts in %s" % p["testDir"]
    print "\t--package\t\tpackage everything up into a tarball for release to sourceforge in %s" % p["packageDir"]
    print "\t--build-stamp [tag]\tfor --package, this specifies a special tag, generating version tag '%s.<tag>. springpython.properties can override with build.stamp'" % p["version"]
    print "\t\t\t\tIf this option isn't used, default will be tag will be '%s.<current time>'" % p["version"]
    print "\t--publish\t\tpublish this release to the deployment server"
    print "\t--register\t\tregister this release with http://pypi.python.org/pypi"
    print "\t--site\t\t\tcreate the site and all its related documents"
    print "\t--docs-html-multi\tgenerate HTML documentation, split up into separate sections"
    print "\t--docs-html-single\tgenerate HTML documentation in a single file"
    print "\t--docs-pdf\t\tgenerate PDF documentation"
    print "\t--docs-all\t\tgenerate all documents"
    print "\t--pydoc\t\t\tgenerate pydoc information"
    print

try:
    optlist, args = getopt.getopt(sys.argv[1:],
                                  "hct",
                                  ["help", "clean", "test", "coverage", "package", "build-stamp=", \
                                   "publish", "register", \
                                   "site", "docs-html-multi", "docs-html-single", "docs-pdf", "docs-all", "pydoc"])
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
    if os.path.exists(dir):
        shutil.rmtree(dir, True)
    # TODO: Make this OS-independent
    os.system("find . -name '*.pyc' -exec rm -f {} \;")
    os.system("find . -name '*.class' -exec rm -f {} \;")

def test(dir):
    """
    Run nose programmatically, so that it uses the same python version as this script uses
    
    Nose expects to receive a sys.argv, of which the first arg is the script path (usually nosetests). Since this isn't 
    being run that way, a filler entry was created to satisfy the library's needs.
    """
    if not os.path.exists(dir):
        os.makedirs(dir)
    
    _run_nose(argv=["", "--with-nosexunit", "--source-folder=src", "--where=test/springpythontest", "--xml-report-folder=%s" % dir, "checkin"])
    
def test_coverage(dir):
    """
    Run nose programmatically, so that it uses the same python version as this script uses

    Nose expects to receive a sys.argv, of which the first arg is the script path (usually nosetests). Since this isn't
    being run that way, a filler entry was created to satisfy the library's needs.
    """

    if not os.path.exists(dir):
        os.makedirs(dir)

    _run_nose(argv=["", "--with-nosexunit", "--source-folder=src", "--where=test/springpythontest", "--xml-report-folder=%s" % dir, "--with-coverage", "--cover-package=springpython", "checkin"])

def _run_nose(argv):
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
                       p['natural.name'],
                       filename ])

    patterns_to_replace = [("version", version), ("download_url", "http://s3.amazonaws.com/%s/%s-%s.tar.gz" % (s3bucket, s3key, version))]

    _substitute(dir + "/build.py", dir + "/setup.py", patterns_to_replace)
    os.system("cd %s ; python setup.py sdist ; mv dist/* .. ; \\rm -rf dist ; \\rm -f MANIFEST" % dir)

def package(dir, version, s3bucket, src_filename, sample_filename):
    if not os.path.exists(dir):
        os.makedirs(dir)

    _substitute("src/plugins/coily-template", "src/plugins/coily", [("version", version)])
    os.system("chmod 755 src/plugins/coily")
    build("src", version, s3bucket, src_filename)
    build("samples", version, s3bucket, sample_filename)
    os.remove("src/plugins/coily")
    os.system("mv *.tar.gz %s" % dir)

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

def publish(filepath, s3bucket, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, version):
    filename = filepath.split("/")[-1]
    s3key = "/".join([ p['release.type'],
                       p['project.key'],
                       p['natural.name'],
                       filename ])

    print "Reading in content from %s" % filepath
    filedata = open(filepath, "rb").read()

    filehash = _sha(filedata).hexdigest()

    print "Preparing to upload %s to %s/%s" % (filename, s3bucket, s3key)

    content_type = mimetypes.guess_type(filename)[0]
    if content_type is None:
        content_type = 'text/plain'

    print "File appears to be %s" % content_type

    print "Connecting to S3..."
    conn = S3.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

    print "Checking if bucket %s exists..." % s3bucket
    check = conn.check_bucket_exists(s3bucket)
    if (check.status == 200):
        print "Uploading %s to %s/%s" % (filename, s3bucket, s3key)
        print conn.put(
            s3bucket,
            s3key,
            S3.S3Object(filedata),
            { 'Content-Type': content_type,
              'x-amz-acl': 'public-read', 
              'x-amz-meta-project.name': 'Spring Python',
              'x-amz-meta-release.type': p['release.type'],
              'x-amz-meta-bundle.version': version,
              'x-amz-meta-package.file.name': filename } ).message

        print "Uploading SHA1 digest to %s/%s" % (s3bucket, s3key + '.sha1')
        print conn.put(
            s3bucket,
            s3key + '.sha1',
            S3.S3Object(filehash + ' ' + filename + "\n" ),
            { 'Content-Type': content_type, 'x-amz-acl': 'public-read'}).message
    else:
        print "Error code %s: Unable to publish" % check.status

def register():
    os.system("cd src     ; python setup.py register")
    os.system("cd samples ; python setup.py register")

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

def site(version):
    _substitute("pom-template.xml", "pom.xml", [("version", version)])

    docs_all(version)
    cur = os.path.abspath(".")
    shutil.copy(cur + "/docs/spring.ico", p["targetDir"]+"/docs/favicon.ico")
    os.system("mvn -Dspringpython.version=%s site" % version)
    os.remove("pom.xml")
    os.system("cp docs/resources/css/* target/docs/css/")
    create_pydocs()

def docs_all(version):
    copy("xml/schema/context/", p["targetDir"] + "/docs/schema/context/", ["*.xsd"])

    docs_multi(version)
    docs_pdf(version)
    
def docs_multi(version):
    root = p["targetDir"] + "/" + p["dist.ref.dir"] + "/html"
    print root

    setup(root)

    cur = os.getcwd()
    sub_version(cur, version)
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
    
    cur = os.getcwd()
    sub_version(cur, version)
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
   
    cur = os.getcwd()
    sub_version(cur, version)
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

def create_pydocs():
    sys.path.append(os.getcwd() + "/src")
    import springpython

    if not os.path.exists("target/docs/pydoc"):
        os.mkdir("target/docs/pydoc")
 
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
    pydoc.writedoc("springpython.security.cherrypy31")
    pydoc.writedoc("springpython.security.intercept")
    pydoc.writedoc("springpython.security.context")
    pydoc.writedoc("springpython.security.context.SecurityContextHolder")
    pydoc.writedoc("springpython.security.providers")
    pydoc.writedoc("springpython.security.providers.dao")
    pydoc.writedoc("springpython.security.providers.encoding")
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

# No matter what order the command are specified in, the build-stamp must be extracted first.
for option in optlist:
    if option[0] == "--build-stamp":
        build_stamp = option[1]   # Override build stamp with user-supplied version

# However, a springpython.properties entry can override the command-line
if "build.stamp" in p:
    build_stamp = p["build.stamp"]
complete_version = p["version"] + "." + build_stamp

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
        package(p["packageDir"], complete_version, p['s3.bucket'], "springpython", "springpython-samples")
	
    if option[0] in ("--publish"):
        print "Looking for local key file..."
        load_properties(p, p["s3.key_file"])  # Saves the user from having to manually input the keys

        print "Looking for user's key file, which can override local file..."
        load_properties(p, os.path.expanduser("~") + "/" + p["s3.key_file"])  # Saves the user from having to manually input the keys

        BUCKET_NAME = p["s3.bucket"]
        if "accessKey" in p:
            AWS_ACCESS_KEY_ID = p["accessKey"]
        else: 
            AWS_ACCESS_KEY_ID = raw_input("Please enter the AWS_ACCESS_KEY_ID (NOT your secret key): ")
        if "secretKey" in p:
            AWS_SECRET_ACCESS_KEY = p["secretKey"]
        else:
            AWS_SECRET_ACCESS_KEY = raw_input("Please enter AWC_SECRET_ACCESS_KEY: ")

        [publish(filename, BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, complete_version) for filename in glob("target/artifacts/*.tar.gz")]

    if option[0] in ("--register"):
        register()

    if option[0] in ("--site"):
        site(complete_version)

    if option[0] in ("--docs-all"):
        docs_all(complete_version)
                
    if option[0] in ("--docs-html-multi"):
        docs_multi(complete_version)

    if option[0] in ("--docs-html-single"):
        docs_single(complete_version)

    if option[0] in ("--docs-pdf"):
        docs_pdf(complete_version)

    if option[0] in ("--pydoc"):
        create_pydocs()
    

