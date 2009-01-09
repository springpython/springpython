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
import re
import os
import shutil

__description__ = "plugin to create skeleton CherryPy applications"

def create(plugin_path, name):
    if not os.path.exists(name):
        print "Creating CherryPy skeleton app %s" % name
        os.makedirs(name)

        # Copy/transform the template files
        for file_name in ["cherrypy-app.py", "controller.py", "view.py", "app_context.py"]:
            input_file = open(plugin_path + "/" + file_name).read()

            # Iterate over a list of patterns, performing string substitution on the input file
            patterns_to_replace = [("name", name), ("properName", name[0].upper() + name[1:])]
            for pattern, replacement in patterns_to_replace:
                input_file = re.compile(r"\$\{%s}" % pattern).sub(replacement, input_file)

            output_filename = name + "/" + file_name
            if file_name == "cherrypy-app.py":
                output_filename = name + "/" + name + ".py"

            app = open(output_filename, "w")
            app.write(input_file)
            app.close()

        # Recursively copy other parts
        shutil.copytree(plugin_path + "/images", name + "/" + "images")
    else:
        print "There is already something called %s. ABORT!" % name

