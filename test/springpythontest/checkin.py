from springpythontest.aopTestCases import *
from springpythontest.contextTestCases import *
#from springpythontest.databaseCoreTestCases import MySQLDatabaseTemplateTestCase
#from springpythontest.databaseCoreTestCases import PostGreSQLDatabaseTemplateTestCase
from springpythontest.databaseCoreTestCases import SqliteDatabaseTemplateTestCase
#from springpythontest.databaseCoreTestCases import SQLServerDatabaseTemplateTestCase
from springpythontest.databaseCoreTestCases import DatabaseTemplateMockTestCase
#from springpythontest.databaseTransactionTestCases import MySQLTransactionTestCase
#from springpythontest.databaseTransactionTestCases import PostGreSQLTransactionTestCase
from springpythontest.databaseTransactionTestCases import SqliteTransactionTestCase
#from springpythontest.databaseTransactionTestCases import SQLServerTransactionTestCase
#from springpythontest.remotingTestCases import PyroRemotingTestCase
#from springpythontest.remotingTestCases import HessianRemotingTestCase
from springpythontest.securityEncodingTestCases import *
from springpythontest.securityProviderTestCases import *
from springpythontest.securityUserDetailsTestCases import *
from springpythontest.securityVoteTestCases import *
from springpythontest.securityWebTestCases import *

logger = logging.getLogger("springpython")
loggingLevel = logging.DEBUG
logger.setLevel(loggingLevel)
ch = logging.StreamHandler()
ch.setLevel(loggingLevel)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


