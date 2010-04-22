#############################################################
# This stand-alone utility is for starting up a directory
# server for test purposes.
#############################################################

import os
import shutil
import subprocess

cp = ":".join(["lib/" + item for item in os.listdir("lib") if item.endswith(".jar")])

subprocess.Popen("javac -cp %s org/springframework/springpython/ApacheDSContainer.java" % cp, shell=True).wait()

shutil.rmtree("apacheds-spring-security", ignore_errors=True)

subprocess.Popen("java -cp .:%s org.springframework.springpython.ApacheDSContainer &" % cp, shell=True)
