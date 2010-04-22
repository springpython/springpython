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

PROTOTYPE = "scope.PROTOTYPE"
SINGLETON = "scope.SINGLETON"

def convert(scope_str):
    "This function converts the string-version of scope into the internal, enumerated version."
    if scope_str == "prototype":
        return PROTOTYPE
    elif scope_str == "singleton":
        return SINGLETON
    else:
        raise Exception("Can not handle scope %s" % s)
    
