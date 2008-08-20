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
import types
from pmock import *
from springpython.aop import MethodInterceptor
from springpython.context import DecoratorBasedApplicationContext
from springpython.context import component
from springpython.context import scope
from springpython.database.core import DaoSupport
from springpython.database.core import DatabaseTemplate
from springpython.database.core import RowCallbackHandler
from springpython.database.factory import ConnectionFactory
from springpython.database.factory import MySQLConnectionFactory
from springpython.database import transaction
from springpython.database.transaction import AutoTransactionalComponent
from springpython.database.transaction import ConnectionFactoryTransactionManager
from springpython.database.transaction import TransactionTemplate
from springpython.database.transaction import TransactionCallbackWithoutResult
from springpython.database.transaction import TransactionProxyFactoryComponent
from springpython.database.transaction import Transactional

class Person(object):
    def __init__(self, name, phone):
        self.name = name
        self.phone = phone
        
class Animal(object):
    def __init__(self, name, category):
        self.name = name
        self.category = category
        
class SampleRowCallbackHandler(RowCallbackHandler):
    def processRow(self, row):
        return Person(name = row[0], phone = row[1])

class AnimalRowCallbackHandler(RowCallbackHandler):
    def processRow(self, row):
        return Animal(name = row[0], category = row[1])

class InvalidCallbackHandler(object):
    pass

class ImproperCallbackHandler(object):
    def processRow(self):
        raise Exception("You should not have made it this far.")

class ValidHandler(object):
    def processRow(self, row):
        return {row[0]:row[1]}

class MovieLister(object):
    def __init__ (self):
        self.finder = None
    
class ColonMovieFinder(object):
    def __init__(self, filename = ""):
        self.filename = filename
    def findAll (self):
        return [line.strip() for line in open(self.filename).readlines()]

class StringHolder(object):
    def __init__(self, str=""):
        self.str = str
        
class MovieBasedApplicationContext(DecoratorBasedApplicationContext):
    """
    This is a test support class that inherits its functionality from the super class.
    """
    def __init__(self):
        DecoratorBasedApplicationContext.__init__(self)
        
    @component(scope.PROTOTYPE)
    def MovieLister(self):
        lister = MovieLister()
        lister.finder = self.MovieFinder()
        lister.description = self.SingletonString()
        return lister
    
    @component(scope.SINGLETON)
    def MovieFinder(self):
        return ColonMovieFinder(filename="support/movies1.txt")
    
    @component    # scope.SINGLETON is the default
    def SingletonString(self):
        return StringHolder("There should only be one copy of this string")
    
    def NotExposed(self):
        pass

class DuckTypedMovieBasedApplicationContext(object):
    """
    This is a test support class that inherits its functionality from the super class.
    """
    @component(scope.PROTOTYPE)
    def MovieLister(self):
        lister = MovieLister()
        lister.finder = self.MovieFinder()
        lister.description = self.SingletonString()
        return lister
    
    @component(scope.SINGLETON)
    def MovieFinder(self):
        return ColonMovieFinder(filename="support/movies1.txt")
    
    @component    # scope.SINGLETON is the default
    def SingletonString(self):
        return StringHolder("There should only be one copy of this string")
    
    def NotExposed(self):
        pass

class TheOtherMovieFinder(object):
    def __init__(self, filename = ""):
        self.filename = filename
    def findAll(self):
        return [line.strip()[0:3] for line in open(self.filename).readlines()]

class SampleBlockOfData:
    def __init__(self, data):
        self.data = data
    def getLabel(self):
        return self.data

class SampleService:
    def __init__(self):
        self.attribute = "sample"
    def method(self, data):
        return "You made it!"
    def doSomething(self):
        return "Alright!"
    def __str__(self):
        return "This is a sample service."

class RemoteService1(object):
    def getData(self, param):
        return "You got remote data => %s" % param
    def getMoreData(self, param):
        return "You got more remote data => %s" % param
    
class RemoteService2(object):
    def executeOperation(self, routine):
        return "Operation %s has been carried out" % routine
    def executeOtherOperation(self, routine):
        return "Other operation %s has been carried out" % routine
    
class BeforeAndAfterInterceptor(MethodInterceptor):
    def __init__(self):
        self.logger = logging.getLogger("springpythontest.testSupportClasses.BeforeAndAfterInterceptor")

    def invoke(self, invocation):
        results = "BEFORE => " + invocation.proceed() + " <= AFTER"
        return results

class WrappingInterceptor(MethodInterceptor):
    def __init__(self):
        self.logger = logging.getLogger("springpythontest.testSupportClasses.WrappingInterceptor")

    def invoke(self, invocation):
        results = "<Wrapped>" + invocation.proceed() + "</Wrapped>"
        return results

class StubConnection(object):
    def __init__(self):
        self.mockCursor = None
    def cursor(self):
        return self.mockCursor
    
class StubDBFactory(ConnectionFactory):
    def __init__(self):
        ConnectionFactory.__init__(self, [types.TupleType])
        self.stubConnection = StubConnection()
    def connect(self):
        return self.stubConnection

class ImpFileProps(object):
    def __init__(self, paystat_work_dir, paystat_reload_dir, paystat_archive_dir, oid):
        self.paystat_work_dir = paystat_work_dir
        self.paystat_reload_dir = paystat_reload_dir
        self.paystat_archive_dir = paystat_archive_dir
        self.oid = oid

class ImpFilePropsRowCallbackHandler(RowCallbackHandler):
    def processRow(self, row):
        return ImpFileProps(row[0], row[1], row[2], row[3])

class BankException(Exception):
    pass

class Bank(object):
    """This sample application can be used to demonstrate the value of atomic operations. The transfer operation
    must be wrapped in a transaction in order to perform correctly. Otherwise, any errors in the deposit will
    allow the from-account to leak assets."""
    def __init__(self, factory):
        self.logger = logging.getLogger("springpythontest.testSupportClasses.Bank")
        self.dt = DatabaseTemplate(factory)

    def open(self, accountNum):
        self.logger.debug("Opening account %s with $0 balance." % accountNum)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (accountNum, 0))

    def deposit(self, amount, accountNum):
        self.logger.debug("Depositing $%s into %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)

    def withdraw(self, amount, accountNum):
        self.logger.debug("Withdrawing $%s from %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)
        return amount

    def balance(self, accountNum):
        return self.dt.queryForObject("SELECT balance FROM account WHERE account_num = ?", (accountNum,), types.FloatType)

    def transfer(self, amount, fromAccountNum, toAccountNum):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, fromAccountNum, toAccountNum))
        self.withdraw(amount, fromAccountNum)
        self.deposit(amount, toAccountNum)

class DatabaseTxTestAppContext(DecoratorBasedApplicationContext):
    def __init__(self, factory):
        self.factory = factory
        DecoratorBasedApplicationContext.__init__(self)

    @component
    def bankTarget(self):
        return Bank(self.factory)

    @component
    def transactionalComponent(self):
        return AutoTransactionalComponent(self.transactionManager())

    @component
    def transactionManager(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @component
    def bank(self):
        transactionAttributes = []
        transactionAttributes.append((".*transfer", ["PROPAGATION_REQUIRED"]))
        transactionAttributes.append((".*", ["PROPAGATION_REQUIRED","readOnly"]))
        return TransactionProxyFactoryComponent(self.transactionManager(), self.bankTarget(), transactionAttributes)


class DatabaseTxTestAppContextWithNoAutoTransactionalComponent(DecoratorBasedApplicationContext):
    def __init__(self, factory):
        self.factory = factory
        DecoratorBasedApplicationContext.__init__(self)

    @component
    def bankTarget(self):
        return Bank(self.factory)

    @component
    def transactionManager(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @component
    def bank(self):
        return TransactionalBank(self.factory)

class TransactionalBank(object):
    """This sample application can be used to demonstrate the value of atomic operations. The transfer operation
    must be wrapped in a transaction in order to perform correctly. Otherwise, any errors in the deposit will
    allow the from-account to leak assets."""
    def __init__(self, factory):
        self.logger = logging.getLogger("springpythontest.testSupportClasses.TransactionalBank")
        self.dt = DatabaseTemplate(factory)

    def open(self, accountNum):
        self.logger.debug("Opening account %s with $0 balance." % accountNum)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (accountNum, 0))

    def deposit(self, amount, accountNum):
        self.logger.debug("Depositing $%s into %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)

    def withdraw(self, amount, accountNum):
        self.logger.debug("Withdrawing $%s from %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)
        return amount

    def balance(self, accountNum):
        return self.dt.queryForObject("SELECT balance FROM account WHERE account_num = ?", (accountNum,), types.FloatType)

    @Transactional()
    def transfer(self, amount, fromAccountNum, toAccountNum):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, fromAccountNum, toAccountNum))
        self.withdraw(amount, fromAccountNum)
        self.deposit(amount, toAccountNum)

class DatabaseTxTestDecorativeTransactions(DecoratorBasedApplicationContext):
    def __init__(self, factory):
        self.factory = factory
        DecoratorBasedApplicationContext.__init__(self)

    @component
    def transactionalComponent(self):
        return AutoTransactionalComponent(self.transactionManager())

    @component
    def transactionManager(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @component
    def bank(self):
        results = TransactionalBank(self.factory)
        return results

class TransactionalBankWithNoTransactionalArguments(object):
    """This sample application can be used to demonstrate the value of atomic operations. The transfer operation
    must be wrapped in a transaction in order to perform correctly. Otherwise, any errors in the deposit will
    allow the from-account to leak assets."""
    def __init__(self, factory):
        self.logger = logging.getLogger("springpythontest.testSupportClasses.TransactionalBankWithNoTransactionalArguments")
        self.dt = DatabaseTemplate(factory)

    def open(self, accountNum):
        self.logger.debug("Opening account %s with $0 balance." % accountNum)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (accountNum, 0))

    def deposit(self, amount, accountNum):
        self.logger.debug("Depositing $%s into %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)

    def withdraw(self, amount, accountNum):
        self.logger.debug("Withdrawing $%s from %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)
        return amount

    def balance(self, accountNum):
        return self.dt.queryForObject("SELECT balance FROM account WHERE account_num = ?", (accountNum,), types.FloatType)

    @Transactional
    def transfer(self, amount, fromAccountNum, toAccountNum):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, fromAccountNum, toAccountNum))
        self.withdraw(amount, fromAccountNum)
        self.deposit(amount, toAccountNum)

class DatabaseTxTestDecorativeTransactionsWithNoArguments(DecoratorBasedApplicationContext):
    def __init__(self, factory):
        self.factory = factory
        DecoratorBasedApplicationContext.__init__(self)

    @component
    def transactionalComponent(self):
        return AutoTransactionalComponent(self.transactionManager())

    @component
    def transactionManager(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @component
    def bank(self):
        results = TransactionalBankWithNoTransactionalArguments(self.factory)
        return results

class TransactionalBankWithLotsOfTransactionalArguments(object):
    """This sample application can be used to demonstrate the value of atomic operations. The transfer operation
    must be wrapped in a transaction in order to perform correctly. Otherwise, any errors in the deposit will
    allow the from-account to leak assets."""
    def __init__(self, factory):
        self.logger = logging.getLogger("springpythontest.testSupportClasses.TransactionalBankWithLotsOfTransactionalArguments")
        self.dt = DatabaseTemplate(factory)

    @Transactional(["PROPAGATION_REQUIRED"])
    def open(self, accountNum):
        self.logger.debug("Opening account %s with $0 balance." % accountNum)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (accountNum, 0))

    @Transactional(["PROPAGATION_REQUIRED"])
    def deposit(self, amount, accountNum):
        self.logger.debug("Depositing $%s into %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)

    @Transactional(["PROPAGATION_REQUIRED"])
    def withdraw(self, amount, accountNum):
        self.logger.debug("Withdrawing $%s from %s" % (amount, accountNum))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, accountNum))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % accountNum)
        return amount

    @Transactional(["PROPAGATION_SUPPORTS","readOnly"])
    def balance(self, accountNum):
        self.logger.debug("Checking balance for %s" % accountNum)
        return self.dt.queryForObject("SELECT balance FROM account WHERE account_num = ?", (accountNum,), types.FloatType)

    @Transactional(["PROPAGATION_REQUIRED"])
    def transfer(self, amount, fromAccountNum, toAccountNum):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, fromAccountNum, toAccountNum))
        self.withdraw(amount, fromAccountNum)
        self.deposit(amount, toAccountNum)

    @Transactional(["PROPAGATION_NEVER"])
    def nonTransactionalOperation(self):
        self.logger.debug("Executing non-transactional operation.")

    @Transactional(["PROPAGATION_MANDATORY"])
    def mandatoryOperation(self):
        self.logger.debug("Executing mandatory transactional operation.")

    @Transactional(["PROPAGATION_REQUIRED"])
    def mandatoryOperationTransactionalWrapper(self):
        self.mandatoryOperation()
        self.mandatoryOperation()

    @Transactional(["PROPAGATION_REQUIRED"])
    def nonTransactionalOperationTransactionalWrapper(self):
        self.nonTransactionalOperation()

class DatabaseTxTestDecorativeTransactionsWithLotsOfArguments(DecoratorBasedApplicationContext):
    def __init__(self, factory):
        self.factory = factory
        DecoratorBasedApplicationContext.__init__(self)

    @component
    def transactionManager(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @component
    def transactionalComponent(self):
        return AutoTransactionalComponent(self.transactionManager())

    @component
    def bank(self):
        results = TransactionalBankWithLotsOfTransactionalArguments(self.factory)
        return results


