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
from springpython.config import PythonConfig
from springpython.config import Object
from springpython.context import scope
from springpython.database.core import DaoSupport
from springpython.database.core import DatabaseTemplate
from springpython.database.core import RowMapper
from springpython.database.factory import ConnectionFactory
from springpython.database.factory import MySQLConnectionFactory
from springpython.database import transaction
from springpython.database.transaction import AutoTransactionalObject
from springpython.database.transaction import ConnectionFactoryTransactionManager
from springpython.database.transaction import TransactionTemplate
from springpython.database.transaction import TransactionCallbackWithoutResult
from springpython.database.transaction import TransactionProxyFactoryObject
from springpython.database.transaction import Transactional

class Person(object):
    def __init__(self, name, phone):
        self.name = name
        self.phone = phone
        
class Animal(object):
    def __init__(self, name, category):
        self.name = name
        self.category = category
        
class SampleRowMapper(RowMapper):
    def map_row(self, row):
        return Person(name = row[0], phone = row[1])

class AnimalRowMapper(RowMapper):
    def map_row(self, row):
        return Animal(name = row[0], category = row[1])

class InvalidCallbackHandler(object):
    pass

class ImproperCallbackHandler(object):
    def map_row(self):
        raise Exception("You should not have made it this far.")

class ValidHandler(object):
    def map_row(self, row):
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
        
class MovieBasedApplicationContext(PythonConfig):
    """
    This is a test support class that inherits its functionality from the super class.
    """        
    def __init__(self):
        super(MovieBasedApplicationContext, self).__init__()
        
    @Object(scope.PROTOTYPE)
    def MovieLister(self):
        lister = MovieLister()
        lister.finder = self.MovieFinder()
        lister.description = self.SingletonString()
        self.logger.debug("Description = %s" % lister.description)
        return lister
    
    @Object(scope.SINGLETON)
    def MovieFinder(self):
        return ColonMovieFinder(filename="support/movies1.txt")
    
    @Object    # scope.SINGLETON is the default
    def SingletonString(self):
        return StringHolder("There should only be one copy of this string")
    
    def NotExposed(self):
        pass

class MixedApplicationContext(PythonConfig):
    def __init__(self):
        super(MixedApplicationContext, self).__init__()
        
    @Object(scope.SINGLETON)
    def MovieFinder(self):
        return ColonMovieFinder(filename="support/movies1.txt")

class MixedApplicationContext2(PythonConfig):
    def __init__(self):
        super(MixedApplicationContext2, self).__init__()
        
    @Object(scope.PROTOTYPE)
    def MovieLister(self):
        lister = MovieLister()
        lister.finder = self.app_context.get_object("MovieFinder")
        lister.description = self.SingletonString()
        self.logger.debug("Description = %s" % lister.description)
        return lister
    
    @Object    # scope.SINGLETON is the default
    def SingletonString(self):
        return StringHolder("There should only be one copy of this string")

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
        return "You made it! => %s" % data
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

class ImpFilePropsRowMapper(RowMapper):
    def map_row(self, row):
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

    def open(self, account_num):
        self.logger.debug("Opening account %s with $0 balance." % account_num)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (account_num, 0))

    def deposit(self, amount, account_num):
        self.logger.debug("Depositing $%s into %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)

    def withdraw(self, amount, account_num):
        self.logger.debug("Withdrawing $%s from %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)
        return amount

    def balance(self, account_num):
        return self.dt.query_for_object("SELECT balance FROM account WHERE account_num = ?", (account_num,), types.FloatType)

    def transfer(self, amount, from_account, to_account):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, from_account, to_account))
        self.withdraw(amount, from_account)
        self.deposit(amount, to_account)

class DatabaseTxTestAppContext(PythonConfig):
    def __init__(self, factory):
        super(DatabaseTxTestAppContext, self).__init__()
        self.factory = factory

    @Object
    def bank_target(self):
        return Bank(self.factory)

    @Object
    def tx_object(self):
        return AutoTransactionalObject(self.tx_mgr())

    @Object
    def tx_mgr(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @Object
    def bank(self):
        transactionAttributes = []
        transactionAttributes.append((".*transfer", ["PROPAGATION_REQUIRED"]))
        transactionAttributes.append((".*", ["PROPAGATION_REQUIRED","readOnly"]))
        return TransactionProxyFactoryObject(self.tx_mgr(), self.bank_target(), transactionAttributes)


class DatabaseTxTestAppContextWithNoAutoTransactionalObject(PythonConfig):
    def __init__(self, factory):
        super(DatabaseTxTestAppContextWithNoAutoTransactionalObject, self).__init__()
        self.factory = factory

    @Object
    def bank_target(self):
        return Bank(self.factory)

    @Object
    def tx_mgr(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @Object
    def bank(self):
        return TransactionalBank(self.factory)

class TransactionalBank(object):
    """This sample application can be used to demonstrate the value of atomic operations. The transfer operation
    must be wrapped in a transaction in order to perform correctly. Otherwise, any errors in the deposit will
    allow the from-account to leak assets."""
    def __init__(self, factory):
        self.logger = logging.getLogger("springpythontest.testSupportClasses.TransactionalBank")
        self.dt = DatabaseTemplate(factory)

    def open(self, account_num):
        self.logger.debug("Opening account %s with $0 balance." % account_num)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (account_num, 0))

    def deposit(self, amount, account_num):
        self.logger.debug("Depositing $%s into %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)

    def withdraw(self, amount, account_num):
        self.logger.debug("Withdrawing $%s from %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)
        return amount

    def balance(self, account_num):
        return self.dt.query_for_object("SELECT balance FROM account WHERE account_num = ?", (account_num,), types.FloatType)

    @Transactional()
    def transfer(self, amount, from_account, to_account):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, from_account, to_account))
        self.withdraw(amount, from_account)
        self.deposit(amount, to_account)

class DatabaseTxTestDecorativeTransactions(PythonConfig):
    def __init__(self, factory):
        super(DatabaseTxTestDecorativeTransactions, self).__init__()
        self.factory = factory

    @Object
    def tx_object(self):
        return AutoTransactionalObject(self.tx_mgr())

    @Object
    def tx_mgr(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @Object
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

    def open(self, account_num):
        self.logger.debug("Opening account %s with $0 balance." % account_num)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (account_num, 0))

    def deposit(self, amount, account_num):
        self.logger.debug("Depositing $%s into %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)

    def withdraw(self, amount, account_num):
        self.logger.debug("Withdrawing $%s from %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)
        return amount

    def balance(self, account_num):
        return self.dt.query_for_object("SELECT balance FROM account WHERE account_num = ?", (account_num,), types.FloatType)

    @Transactional
    def transfer(self, amount, from_account, to_account):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, from_account, to_account))
        self.withdraw(amount, from_account)
        self.deposit(amount, to_account)

class DatabaseTxTestDecorativeTransactionsWithNoArguments(PythonConfig):
    def __init__(self, factory):
        super(DatabaseTxTestDecorativeTransactionsWithNoArguments, self).__init__()
        self.factory = factory

    @Object
    def tx_object(self):
        return AutoTransactionalObject(self.tx_mgr())

    @Object
    def tx_mgr(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @Object
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
    def open(self, account_num):
        self.logger.debug("Opening account %s with $0 balance." % account_num)
        self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (account_num, 0))

    @Transactional(["PROPAGATION_REQUIRED"])
    def deposit(self, amount, account_num):
        self.logger.debug("Depositing $%s into %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)

    @Transactional(["PROPAGATION_REQUIRED"])
    def withdraw(self, amount, account_num):
        self.logger.debug("Withdrawing $%s from %s" % (amount, account_num))
        rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, account_num))
        if rows == 0:
            raise BankException("Account %s does NOT exist" % account_num)
        return amount

    @Transactional(["PROPAGATION_SUPPORTS","readOnly"])
    def balance(self, account_num):
        self.logger.debug("Checking balance for %s" % account_num)
        return self.dt.query_for_object("SELECT balance FROM account WHERE account_num = ?", (account_num,), types.FloatType)

    @Transactional(["PROPAGATION_REQUIRED"])
    def transfer(self, amount, from_account, to_account):
        self.logger.debug("Transferring $%s from %s to %s." % (amount, from_account, to_account))
        self.withdraw(amount, from_account)
        self.deposit(amount, to_account)

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

class DatabaseTxTestDecorativeTransactionsWithLotsOfArguments(PythonConfig):
    def __init__(self, factory):
        super(DatabaseTxTestDecorativeTransactionsWithLotsOfArguments, self).__init__()
        self.factory = factory

    @Object
    def tx_mgr(self):
        return ConnectionFactoryTransactionManager(self.factory)

    @Object
    def tx_object(self):
        return AutoTransactionalObject(self.tx_mgr())

    @Object
    def bank(self):
        results = TransactionalBankWithLotsOfTransactionalArguments(self.factory)
        return results

class ValueHolder(object):
    def __init__(self, string_holder = None):
        self.some_dict = None
        self.some_list = None
        self.some_props = None
        self.some_set = None
        self.some_frozen_set = None
        self.some_tuple = None
        self.string_holder = string_holder
        
class MultiValueHolder(object):
    def __init__(self, a = "a", b = "b", c = "c"):
        self.a = a
        self.b = b
        self.c = c
        
class ConstructorBasedContainer(PythonConfig):
    @Object
    def MultiValueHolder(self):
        return MultiValueHolder(a="alt a", b="alt b")
    
    @Object
    def MultiValueHolder2(self):
        return MultiValueHolder(c="alt c", b="alt b")
