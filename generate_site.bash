#!/bin/bash
###################################################################################
#   Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.       
###################################################################################
# This script is staged on the host site, and is used to update the local copy of
# spring and then to rebuild the hosted site.
#
# NOTE: Do NOT alter this file without explicit permission from Project Lead
#       Greg Turnquist.
###################################################################################

. sp/bin/activate

cd ~/spring-python-1.2.x
git pull
python2.6 build.py --clean --docs-sphinx --pydoc

