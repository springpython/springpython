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
import logging
import os
import subprocess
import types
import unittest
from springpython.context import ApplicationContext
from springpython.database import factory
from springpython.database import DataAccessException
from springpython.database.core import DatabaseTemplate
from springpython.database.transaction import ConnectionFactoryTransactionManager
from springpython.database.transaction import TransactionTemplate
from springpython.database.transaction import TransactionCallback
from springpython.database.transaction import TransactionCallbackWithoutResult
from springpython.database.transaction import TransactionPropagationException
from springpythontest.support.testSupportClasses import DatabaseTxTestAppContext
from springpythontest.support.testSupportClasses import DatabaseTxTestDecorativeTransactions
from springpythontest.support.testSupportClasses import DatabaseTxTestDecorativeTransactionsWithNoArguments
from springpythontest.support.testSupportClasses import DatabaseTxTestDecorativeTransactionsWithLotsOfArguments
from springpythontest.support.testSupportClasses import DatabaseTxTestAppContextWithNoAutoTransactionalObject
from springpythontest.support.testSupportClasses import BankException
from springpythontest.support.testSupportClasses import TransactionalBank

class AbstractTransactionTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.factory = None
        self.createdTables = False

    def setUp(self):
        if not self.createdTables:
            self.createTables()
        self.createTables()
        self.dt = DatabaseTemplate(self.factory)
        self.dt.execute("DELETE FROM animal")
        self.dt.execute("DELETE FROM account")
        self.factory.commit()
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 0)
        self.transactionManager = ConnectionFactoryTransactionManager(self.factory)
        self.transactionTemplate = TransactionTemplate(self.transactionManager)

    def tearDown(self):
        self.factory.getConnection().rollback()

    def testInsertingRowsIntoTheDatabase(self):
        rows = self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('black mamba',))
        self.assertEquals(rows, 1)

        name = self.dt.query_for_object("SELECT name FROM animal WHERE name = 'black mamba'", required_type=types.StringType)
        self.assertEquals(name, "black mamba")

    def testInsertingRowsIntoTheDatabaseWithInsertApi(self):
        id = self.dt.insert_and_return_id("INSERT INTO animal (name) VALUES (?)", ('black mamba',))
        self.assertEquals(id, 1)

        name = self.dt.query_for_object("SELECT name FROM animal WHERE name = 'black mamba'", required_type=types.StringType)
        self.assertEquals(name, "black mamba")

    def testInsertingTwoRowsWithoutaTransactionButManuallyCommitted(self):
        self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('black mamba',))
        self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('copperhead',))
        self.factory.commit()
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 2)

    def testInsertingTwoRowsWithoutaTransactionButManuallyRolledBack(self):
        self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('black mamba',))
        self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('copperhead',))
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 2)
        self.dt.connection_factory.getConnection().rollback()
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 0)

    def testInsertingTwoRowsWithaTransactionAndNoErrorsAndNoResults(self):
        class txDefinition(TransactionCallbackWithoutResult):
            def do_in_tx_without_result(s, status):
                self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('black mamba',))
                self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('copperhead',))
                
        self.transactionTemplate.execute(txDefinition())
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 2)

    def testInsertingTwoRowsWithaTransactionAndAnIntermediateErrorAndNoResults(self):
        class txDefinition(TransactionCallbackWithoutResult):
            def do_in_tx_without_result(s, status):
                self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('black mamba',))
                self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 1)
                raise DataAccessException("This should break the transaction, and rollback the insert.")
                
        self.assertRaises(DataAccessException, self.transactionTemplate.execute, txDefinition())
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 0)

    def testInsertingTwoRowsWithaTransactionAndNoErrorsAndResults(self):
        class txDefinition(TransactionCallback):
            def do_in_transaction(s, status):
                self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('black mamba',))
                self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('copperhead',))
                results = self.dt.query_for_object("SELECT name FROM animal WHERE name like 'c%'", required_type=types.StringType)
                return results
                
        self.assertEquals(self.transactionTemplate.execute(txDefinition()), "copperhead")
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 2)

    def testInsertingTwoRowsWithaTransactionAndAnIntermediateErrorAndResults(self):
        class txDefinition(TransactionCallback):
            def do_in_transaction(s, status):
                self.dt.execute("INSERT INTO animal (name) VALUES (?)", ('black mamba'))
                self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 1)
                raise DataAccessException("This should break the transaction, and rollback the insert.")
                
        self.assertRaises(DataAccessException, self.transactionTemplate.execute, txDefinition())
        self.assertEquals(len(self.dt.query_for_list("SELECT * FROM animal")), 0)

    def testDeclarativeTransactions(self):
        appContext = ApplicationContext(DatabaseTxTestAppContext(self.factory))
        bank = appContext.get_object("bank")

        bank.open("Checking")
        bank.open("Savings")

        bank.deposit(125.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 125.00)

        bank.deposit(250.00, "Savings")
        self.assertEquals(bank.balance("Savings"), 250.00)

        bank.transfer(25.00, "Savings", "Checking")
        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 150.00)

        bank.withdraw(10.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 140.00)

        amount = 0.0
        try:
            amount = bank.withdraw(1000, "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass
        self.assertEquals(amount, 0.0)

        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 140.00)

        try:
            bank.transfer(200, "Checking", "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass

        self.assertEquals(bank.balance("Savings"), 225.00, "Bad transfer did NOT fail atomically!")
        self.assertEquals(bank.balance("Checking"), 140.00, "Bad transfer did NOT fail atomically!")

    def testDecoratorBasedTransactions(self):
        appContext = ApplicationContext(DatabaseTxTestDecorativeTransactions(self.factory))
        bank = appContext.get_object("bank")

        bank.open("Checking")
        bank.open("Savings")

        bank.deposit(125.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 125.00)

        bank.deposit(250.00, "Savings")
        self.assertEquals(bank.balance("Savings"), 250.00)

        bank.transfer(25.00, "Savings", "Checking")
        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 150.00)

        bank.withdraw(10.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 140.00)

        amount = 0.0
        try:
            amount = bank.withdraw(1000, "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass
        self.assertEquals(amount, 0.0)

        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 140.00)

        try:
            bank.transfer(200, "Checking", "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass
        self.assertEquals(bank.balance("Savings"), 225.00, "Bad transfer did NOT fail atomically!")
        self.assertEquals(bank.balance("Checking"), 140.00, "Bad transfer did NOT fail atomically!")

    def testDecoratorBasedTransactionsWithNoArguments(self):
        appContext = ApplicationContext(DatabaseTxTestDecorativeTransactionsWithNoArguments(self.factory))
        bank = appContext.get_object("bank")

        bank.open("Checking")
        bank.open("Savings")

        bank.deposit(125.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 125.00)

        bank.deposit(250.00, "Savings")
        self.assertEquals(bank.balance("Savings"), 250.00)

        bank.transfer(25.00, "Savings", "Checking")
        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 150.00)

        bank.withdraw(10.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 140.00)

        amount = 0.0
        try:
            amount = bank.withdraw(1000, "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass
        self.assertEquals(amount, 0.0)

        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 140.00)

        try:
            bank.transfer(200, "Checking", "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass

        self.assertEquals(bank.balance("Savings"), 225.00, "Bad transfer did NOT fail atomically!")
        self.assertEquals(bank.balance("Checking"), 140.00, "Bad transfer did NOT fail atomically!")
        
    def testDecoratorBasedTransactionsWithLotsOfArguments(self):
        appContext = ApplicationContext(DatabaseTxTestDecorativeTransactionsWithLotsOfArguments(self.factory))
        bank = appContext.get_object("bank")

        bank.open("Checking")
        bank.open("Savings")

        bank.deposit(125.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 125.00)

        bank.deposit(250.00, "Savings")
        self.assertEquals(bank.balance("Savings"), 250.00)

        bank.transfer(25.00, "Savings", "Checking")
        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 150.00)

        bank.withdraw(10.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 140.00)

        amount = 0.0
        try:
            amount = bank.withdraw(1000, "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass
        self.assertEquals(amount, 0.0)

        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 140.00)

        try:
            bank.transfer(200, "Checking", "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass

        self.assertEquals(bank.balance("Savings"), 225.00, "Bad transfer did NOT fail atomically!")
        logging.getLogger("springpythontest.databaseTransactionTestCases").debug(bank.balance("Checking"))
        self.assertEquals(bank.balance("Checking"), 140.00, "Bad transfer did NOT fail atomically!")
        
    def testOtherPropagationLevels(self):
        appContext = ApplicationContext(DatabaseTxTestDecorativeTransactionsWithLotsOfArguments(self.factory))
        bank = appContext.get_object("bank")

        # Call a mandatory operation outside a transaction, and verify it fails.
        try:
            bank.mandatoryOperation()
            self.fail("Expected a TransactionPropagationException!")
        except TransactionPropagationException:
            pass

        # Call a mandatory operation from within a transactional routine, and verify it works.
        bank.mandatoryOperationTransactionalWrapper()

        # Call a non-transactional operation from outside a transaction, and verify it works.
        bank.nonTransactionalOperation()

        # Call a non-tranactional operation from within a transaction, and verify it fails.
        try:
            bank.nonTransactionalOperationTransactionalWrapper()
            self.fail("Expected a TransactionPropagationException!")
        except TransactionPropagationException:
            pass

    def testTransactionProxyMethodFilters(self):
        appContext = ApplicationContext(DatabaseTxTestAppContext(self.factory))
        bank = appContext.get_object("bank")
 
        bank.open("Checking")
        bank.open("Savings")

        bank.deposit(125.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 125.00)

        bank.deposit(250.00, "Savings")
        self.assertEquals(bank.balance("Savings"), 250.00)

        bank.transfer(25.00, "Savings", "Checking")
        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 150.00)

        bank.withdraw(10.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 140.00)

        amount = 0.0
        try:
            amount = bank.withdraw(1000, "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass
        self.assertEquals(amount, 0.0)

        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 140.00)

        try:
            bank.transfer(200, "Checking", "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass

        self.assertEquals(bank.balance("Savings"), 225.00, "Bad transfer did NOT fail atomically!")
        self.assertEquals(bank.balance("Checking"), 140.00, "Bad transfer did NOT fail atomically!")
 
    def testTransactionalBankWithNoAutoTransactionalObject(self):
        appContext = ApplicationContext(DatabaseTxTestAppContextWithNoAutoTransactionalObject(self.factory))
        bank = appContext.get_object("bank")
 
        bank.open("Checking")
        bank.open("Savings")

        bank.deposit(125.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 125.00)

        bank.deposit(250.00, "Savings")
        self.assertEquals(bank.balance("Savings"), 250.00)

        bank.transfer(25.00, "Savings", "Checking")
        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 150.00)

        bank.withdraw(10.00, "Checking")
        self.assertEquals(bank.balance("Checking"), 140.00)

        amount = 0.0
        try:
            amount = bank.withdraw(1000, "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass
        self.assertEquals(amount, 0.0)

        self.assertEquals(bank.balance("Savings"), 225.00)
        self.assertEquals(bank.balance("Checking"), 140.00)

        try:
            bank.transfer(200, "Checking", "Nowhere")
            self.fail("Expected a BankException!")
        except BankException:
            pass

        self.assertEquals(bank.balance("Savings"), 225.00, "Bad transfer did NOT fail atomically!")
        self.assertEquals(bank.balance("Checking"), -60.00, "Bad transfer did NOT fail as expected (not atomically due to lack of AutoTransactionalObject)")
       
class MySQLTransactionTestCase(AbstractTransactionTestCase):

    def __init__(self, methodName='runTest'):
        AbstractTransactionTestCase.__init__(self, methodName)

    def createTables(self):
        self.createdTables = True
        try:
            self.factory = factory.MySQLConnectionFactory("springpython", "springpython", "localhost", "springpython")
            dt = DatabaseTemplate(self.factory)
            dt.execute("DROP TABLE IF EXISTS animal")
            dt.execute("""
                CREATE TABLE animal (
                  id serial PRIMARY KEY,
                  name VARCHAR(11),
                  category VARCHAR(20),
                  population SMALLINT
                ) ENGINE=innodb
            """)
            dt.execute("DROP TABLE IF EXISTS account")
            dt.execute("""
                CREATE TABLE account (
                    id INT(4) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    account_num VARCHAR(11),
                    balance FLOAT(10)
                ) ENGINE=innodb
            """)
            self.factory.commit()

        except Exception, e:
            print("""
                !!! Can't run MySQLDatabaseTemplateTestCase !!!

                This assumes you have executed some step like:
                % sudo apt-get install mysql (Ubuntu)
                % apt-get install mysql (Debian)

                And then created a database for the spring python user:
                % mysql -uroot
                mysql> DROP DATABASE IF EXISTS springpython;
                mysql> CREATE DATABASE springpython;
                mysql> GRANT ALL ON springpython.* TO springpython@localhost IDENTIFIED BY 'springpython';

                That should setup the springpython user to be able to create tables as needed for these test cases.
            """)
            raise e


class PostGreSQLTransactionTestCase(AbstractTransactionTestCase):

    def __init__(self, methodName='runTest'):
        AbstractTransactionTestCase.__init__(self, methodName)

    def createTables(self):
        self.createdTables = True
        try:
            self.factory = factory.PgdbConnectionFactory("springpython", "springpython", "localhost", "springpython")
            dt = DatabaseTemplate(self.factory)

            dt.execute("DROP TABLE IF EXISTS animal")
            dt.execute("""
                CREATE TABLE animal (
                  id serial PRIMARY KEY,
                  name VARCHAR(11)
                )
            """)
            dt.execute("DROP TABLE IF EXISTS account")
            dt.execute("""
                CREATE TABLE account (
                  id serial PRIMARY KEY,
                  account_num VARCHAR(11),
                  balance FLOAT(10)
                )
            """)
            self.factory.commit()

        except Exception, e:
            print("""
                !!! Can't run PostGreSQLTransactionTestCase !!!

                This assumes you have executed some step like:
                % sudo apt-get install postgresql (Ubuntu)
                % apt-get install postgresql (Debian)

                Next, you need to let PostGreSQL's accounts be decoupled from the system accounts.
                Find pg_hba.conf underneath /etc and add something like this:
                # TYPE  DATABASE    USER        IP-ADDRESS        IP-MASK           METHOD
                host    all         all         <your network>    <yournetworkmask>    md5

                Then, restart it.
                % sudo /etc/init.d/postgresql restart (Ubuntu)

                Then create a user database to match this account.
                % sudo -u postgres psql -f support/setupPostGreSQLSpringPython.sql

                From here on, you should be able to connect into PSQL and run SQL scripts.
            """)
            raise e


class SqliteTransactionTestCase(AbstractTransactionTestCase):

    def __init__(self, methodName='runTest'):
        AbstractTransactionTestCase.__init__(self, methodName)
        self.db_filename = "springpython.db"

    def createTables(self):
        self.createdTables = True
        try:
            try:
                os.remove(self.db_filename)
            except OSError, e:
                pass
            
            self.factory = factory.Sqlite3ConnectionFactory(self.db_filename)
            dt = DatabaseTemplate(self.factory)

            dt.execute("DROP TABLE IF EXISTS animal")
            dt.execute("DROP TABLE IF EXISTS account")
            
            dt.execute("""
                CREATE TABLE animal (
                  id serial PRIMARY KEY,
                  name VARCHAR(11)
                )
            """)
            dt.execute("""
                CREATE TABLE account (
                  id serial PRIMARY KEY,
                  account_num VARCHAR(11),
                  balance FLOAT(10)
                )
            """)
            self.factory.commit()

        except Exception, e:
            print e.message
            print e.args
            print type(e)
            print dir(e)
            print("""
                !!! Can't run SqliteTransactionTestCase !!!

            """)
            raise e

class SQLServerTransactionTestCase(AbstractTransactionTestCase):

    def __init__(self, methodName='runTest'):
        AbstractTransactionTestCase.__init__(self, methodName)

    def createTables(self):
        self.createdTables = True
        try:
            self.factory = factory.SQLServerConnectionFactory(DRIVER="{SQL Server}", 
                SERVER="localhost", DATABASE="springpython", UID="springpython", PWD="cdZS*RQRBdc9a")
            dt = DatabaseTemplate(self.factory)
            
            dt.execute("""IF EXISTS(SELECT 1 FROM sys.tables WHERE name='animal') 
                              DROP TABLE animal""")
            
            dt.execute("""
                CREATE TABLE animal (
                    id INTEGER IDENTITY(1,1) PRIMARY KEY,
                    name VARCHAR(11),
                    category VARCHAR(20),
                    population INTEGER
                )
            """)
            
            dt.execute("""IF EXISTS(SELECT 1 FROM sys.tables WHERE name='account') 
                              DROP TABLE account""")
            
            dt.execute("""
                CREATE TABLE account (
                  id INTEGER IDENTITY(1,1) PRIMARY KEY,
                  account_num VARCHAR(11),
                  balance FLOAT(10)
                )
            """)
            
            self.factory.commit()

        except Exception, e:
            print("""
                !!! Can't run SQLServerDatabaseTemplateTestCase !!!

                This assumes you have installed pyodbc (http://code.google.com/p/pyodbc/).

                And then created an SQL Server database for the 'springpython' 
                login and user.
                
                USE master;
                
                IF EXISTS(SELECT 1 FROM sys.databases WHERE name='springpython')
                    DROP DATABASE springpython;
                
                IF EXISTS(SELECT 1 FROM sys.syslogins WHERE name='springpython')
                    DROP LOGIN springpython;
                
                IF EXISTS(SELECT 1 FROM sys.sysusers WHERE name='springpython')
                    DROP USER springpython;
                
                CREATE DATABASE springpython;
                CREATE LOGIN springpython WITH PASSWORD='cdZS*RQRBdc9a',  DEFAULT_DATABASE=springpython;
                
                USE springpython;
                
                CREATE USER springpython FOR LOGIN springpython;
                EXEC sp_addrolemember 'db_owner', 'springpython';

                From here on, you should be able to connect into SQL Server and run SQL scripts.
            """)
            raise e
