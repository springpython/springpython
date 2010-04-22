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
class DataAccessException(Exception):
    pass

class IncorrectResultSizeDataAccessException(DataAccessException):
    pass

class ArgumentMustBeNamed(DataAccessException):
    def __init__(self, arg_name, msg = ""):
        DataAccessException.__init__(self, msg)
        self.arg_name = arg_name

class InvalidArgumentType(DataAccessException):
    def __init__(self, arg_type, valid_types, msg = ""):
        DataAccessException.__init__(self, msg)
        self.arg_type = arg_type
        self.valid_types = valid_types
