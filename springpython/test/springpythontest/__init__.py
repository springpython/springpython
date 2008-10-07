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
from springpythontest.aopTestCases import *
from springpythontest.contextTestCases import *
#from springpythontest.databaseCoreTestCases import MySQLDatabaseTemplateTestCase
#from springpythontest.databaseCoreTestCases import PostGreSQLDatabaseTemplateTestCase
from springpythontest.databaseCoreTestCases import SqliteDatabaseTemplateTestCase
from springpythontest.databaseCoreTestCases import DatabaseTemplateMockTestCase
#from springpythontest.databaseTransactionTestCases import MySQLTransactionTestCase
#from springpythontest.databaseTransactionTestCases import PostGreSQLTransactionTestCase
from springpythontest.databaseTransactionTestCases import SqliteTransactionTestCase
from springpythontest.remotingTestCases import PyroRemotingTestCase
#from springpythontest.remotingTestCases import HessianRemotingTestCase
from springpythontest.securityEncodingTestCases import *
from springpythontest.securityProviderTestCases import *
from springpythontest.securityUserDetailsTestCases import *
from springpythontest.securityVoteTestCases import *
from springpythontest.securityWebTestCases import *
