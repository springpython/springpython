Transaction Management
======================

When writing a program with database operations, you may need to use
transactions. Your code can get ugly, and it often becomes hard to read the
business logic due to starting, committing, or rolling back for various reasons.
Another risk is that some of the transaction management code you write will
have all the necessary steps, while you may forget some important steps in
others. Spring Python offers a key level of abstraction that can remove that
burden and allow you to focus on the business logic.

External dependencies
---------------------

If you choose to use DatabaseTemplate along with Spring Python's support for
transaction management you need to install :doc:`an appropriate SQL database driver <dao>`
module. Depending on the IoC configuration format you're going to use you may
also need to install one of its :ref:`documented dependencies <dao-external-dependencies>`.

Solutions requiring transactions
--------------------------------

For simple transactions, you can embed them programmatically.

Seen anything like this before?::

    def transfer(transfer_amount, source_account_num, target_account_num):
        conn = MySQLdb.connection("springpython", "springpython", "localhost", "springpython")
        cursor = conn.cursor()
        cursor.execute("update ACCOUNT set BALANCE = BALANCE - %s where ACCOUNT_NUM = %s", (transfer_amount, source_account_num))
        cursor.execute("update ACCOUNT set BALANCE = BALANCE + %s where ACCOUNT_NUM = %s", (transfer_amount, target_account_num))
        cursor.close()

This business method defines a transfer between bank accounts. Notice any
issues here? What happens if the target account doesn't exist? What about
transferring a negative balance? What if the transfer amount exceeded the
source account's balance? All these things require checks, and if something
is wrong the entire transfer must be aborted, or you find the first bank account
leaking money.

To wrap this function transactionally, based on DB-2.0 API specifications,
we'll add some checks. I have also completed some refactorings and utilized
the *DatabaseTemplate* to clean up my database code::

    from springpython.database import *
    from springpython.database.core import *
    import types
    class Bank:
        def __init__(self):
            self.factory = factory.MySQLConnectionFactory("springpython", "springpython", "localhost", "springpython")
            self.dt = DatabaseTemplate(self.factory)

        def balance(self, account_num):
            results = self.dt.query_for_list("select BALANCE from ACCOUNT where ACCOUNT_NUM = %s", (account_num,))
            if len(results) != 1:
                raise InvalidBankAccount("There were %s accounts that matched %s." % (len(results), account_num))
            return results[0][0]

        def checkForSufficientFunds(self, source_balance, amount):
            if source_balance < amount:
                raise InsufficientFunds("Account %s did not have enough funds to transfer %s" % (source_account_num, amount))

        def withdraw(self, amount, source_account_num):
            self.checkForSufficientFunds(self.balance(source_account_num), amount)
            self.dt.execute("update ACCOUNT set BALANCE = BALANCE - %s where ACCOUNT_NUM = %s", (amount, source_account_num))

        def deposit(self, amount, target_account_num):
            # Implicitly testing for valid account number
            self.balance(target_account_num)
            self.dt.execute("update ACCOUNT set BALANCE = BALANCE + %s where ACCOUNT_NUM = %s", (amount, target_account_num))

        def transfer(self, transfer_amount, source_account_num, target_account_num):
            try:
                cursor = self.factory.getConnection().cursor() # DB-2.0 API spec says that creating a cursor implicitly starts a transaction
                self.withdraw(transfer_amount, source_account_num)
                self.deposit(transfer_amount, target_account_num)
                self.factory.getConnection().commit()
                cursor.close() # There wasn't anything in this cursor, but it is good to close an opened cursor
            except InvalidBankAccount, InsufficientFunds:
                self.factory.getConnection().rollback()

* This has some extra checks put in to protect from overdrafts and invalid accounts.
* *DatabaseTemplate* removes our need to open and close cursors.
* Unfortunately, we still have to tangle with them as well as the connection in
  order to handle transactions.

TransactionTemplate
-------------------

We still have to deal with exceptions. What if another part of the code raised
another exception that we didn't trap? It might escape our try-except block of
code, and then our data could lose integrity. If we plug in the
*TransactionTemplate*, we can really simplify this and also guarantee management
of any exceptions.

The following code block shows swapping out manual transaction for
*TransactionTemplate*::

    from springpython.database.transaction import *

    class Bank:
        def __init__(self):
            self.factory = factory.MySQLConnectionFactory("springpython", "springpython", "localhost", "springpython")
            self.dt = DatabaseTemplate(self.factory)
            self.txManager = ConnectionFactoryTransactionManager(self.factory)
            self.txTemplate = TransactionTemplate(self.txManager)

        def transfer(self, transfer_amount, source_account_num, target_account_num):
            class txDefinition(TransactionCallbackWithoutResult):
                 def doInTransactionWithoutResult(s, status):
                        self.withdraw(transfer_amount, source_account_num)
                        self.deposit(transfer_amount, target_account_num)
            try:
                self.txTemplate.execute(txDefinition())
                print "If you made it to here, then your transaction has already been committed."
            except InvalidBankAccount, InsufficientFunds:
                print "If you made it to here, then your transaction has already been rolled back."

* We changed the init function to setup a *TransactionManager* (based on
  ConnectionFactory) and also a *TransactionTemplate*.
* We also rewrote the transfer function to generate a callback.

Now you don't have to deal with implicit cursors, commits, and rollbacks.
Managing commits and rollbacks can really complicated especially when dealing
with exceptions. By wrapping it into a nice callback, *TransactionTemplate* does
the work for us, and lets us focus on business logic, while encouraging us to
continue to define meaningful business logic errors.

@transactional
--------------

Another option is to use the @transactional decorator, and mark which methods
should be wrapped in a transaction when called::

    from springpython.database.transaction import *

    class Bank:
        def __init__(self, connectionFactory):
            self.factory = connectionFactory
            self.dt = DatabaseTemplate(self.factory)

        @transactional
        def transfer(self, transfer_amount, source_account_num, target_account_num):
            self.withdraw(transfer_amount, source_account_num)
            self.deposit(transfer_amount, target_account_num)

This needs to be wired together with a *TransactionManager* in an
*ApplicationContext*. The following example shows a :doc:`PythonConfig <objects-pythonconfig>`
with three objects:

* the bank
* a *TransactionManager* (in this case *ConnectionFactoryTransactionManager*)
* an *AutoTransactionalObject*, which checks all objects to see if they have
  *@transactional* methods, and if so, links them with the *TransactionManager*.

The name of the method (i.e. component name) for *AutoTransactionalObject* doesn't matter::

    class DatabaseTxTestDecorativeTransactions(PythonConfig):
        def __init__(self, factory):
            super(DatabaseTxTestDecorativeTransactions, self).__init__()
            self.factory = factory

        @Object
        def transactionalObject(self):
            return AutoTransactionalObject(self.tx_mgr())

        @Object
        def tx_mgr(self):
            return ConnectionFactoryTransactionManager(self.factory)

        @Object
        def bank(self):
            return TransactionalBank(self.factory)

.. highlight:: xml

This can also be configured using :doc:`XMLConfig <objects-xmlconfig>`::

    <?xml version="1.0" encoding="UTF-8"?>
    <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                   http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

        <object id="transactionalObject" class="springpython.database.transaction.AutoTransactionalObject">
            <constructor-arg ref="tx_mgr"/>
        </object>

        <object id="tx_mgr" class="springpython.database.transaction.ConnectionFactoryTransactionManager">
            <constructor-arg ref="factory"/>
        </object>

        <object id="factory" class="...your DB connection factory definition here..."/>

        <object id="bank" class="TransactionalBank">
            <constructor-arg ref="factory"/>
        </object>

    </objects>


PROPAGATION_REQUIRED ...
++++++++++++++++++++++++

Declarative transactions includes the ability to define transaction propagation.
This allows you to define when a transaction should be started, and which
operations need to be part of transactions. There are several levels of
propagation defined:

* PROPAGATION_SUPPORTS - Code can run inside or outside a transaction.
* PROPAGATION_REQUIRED - If there is no current transaction, one will be started.
* PROPAGATION_MANDATORY - Code MUST be run inside an already started transaction.
* PROPAGATION_NEVER - Code must NOT be run inside an existing transaction.

.. highlight:: python

The following code is a revision of the Bank class, with this attribute plugged in::

    class TransactionalBankWithLotsOfTransactionalArguments(object):
        """This sample application can be used to demonstrate the value of atomic operations. The transfer operation
        must be wrapped in a transaction in order to perform correctly. Otherwise, any errors in the deposit will
        allow the from-account to leak assets."""
        def __init__(self, factory):
            self.logger = logging.getLogger("springpython.test.testSupportClasses.TransactionalBankWithLotsOfTransactionalArguments")
            self.dt = DatabaseTemplate(factory)

        @transactional(["PROPAGATION_REQUIRED"])
        def open(self, accountNum):
            self.logger.debug("Opening account %s with $0 balance." % accountNum)
            self.dt.execute("INSERT INTO account (account_num, balance) VALUES (?,?)", (accountNum, 0))

        @transactional(["PROPAGATION_REQUIRED"])
        def deposit(self, amount, accountNum):
            self.logger.debug("Depositing $%s into %s" % (amount, accountNum))
            rows = self.dt.execute("UPDATE account SET balance = balance + ? WHERE account_num = ?", (amount, accountNum))
            if rows == 0:
                raise BankException("Account %s does NOT exist" % accountNum)

        @transactional(["PROPAGATION_REQUIRED"])
        def withdraw(self, amount, accountNum):
            self.logger.debug("Withdrawing $%s from %s" % (amount, accountNum))
            rows = self.dt.execute("UPDATE account SET balance = balance - ? WHERE account_num = ?", (amount, accountNum))
            if rows == 0:
                raise BankException("Account %s does NOT exist" % accountNum)
            return amount

        @transactional(["PROPAGATION_SUPPORTS","readOnly"])
        def balance(self, accountNum):
            self.logger.debug("Checking balance for %s" % accountNum)
            return self.dt.queryForObject("SELECT balance FROM account WHERE account_num = ?", (accountNum,), types.FloatType)

        @transactional(["PROPAGATION_REQUIRED"])
        def transfer(self, amount, fromAccountNum, toAccountNum):
            self.logger.debug("Transferring $%s from %s to %s." % (amount, fromAccountNum, toAccountNum))
            self.withdraw(amount, fromAccountNum)
            self.deposit(amount, toAccountNum)

        @transactional(["PROPAGATION_NEVER"])
        def nonTransactionalOperation(self):
            self.logger.debug("Executing non-transactional operation.")

        @transactional(["PROPAGATION_MANDATORY"])
        def mandatoryOperation(self):
            self.logger.debug("Executing mandatory transactional operation.")

        @transactional(["PROPAGATION_REQUIRED"])
        def mandatoryOperationTransactionalWrapper(self):
            self.mandatoryOperation()
            self.mandatoryOperation()

        @transactional(["PROPAGATION_REQUIRED"])
        def nonTransactionalOperationTransactionalWrapper(self):
            self.nonTransactionalOperation()

You will notice several levels are being utilized. This class was pulled
directly from the test suite, so some of the functions are deliberately written
to generate controlled failures.

If you look closely at *withdraw*, *deposit*, and *transfer*, which are all set to
PROPAGATION_REQUIRED, you can see what this means. If you use *withdraw* or
*deposit* by themselves, which require transactions, each will start and complete
a transaction. However, *transfer* works by re-using these business methods.
*Transfer* itself needs to be an entire transaction, so it starts one. When it
calls *withdraw* and *deposit*, those methods don't need to start another
transaction because they are already inside one. In comparison, *balance* is
defined as PROPAGATION_SUPPORTS. Since it doesn't update anything, it can
run by itself without a transaction. However, if it is called in the middle
of another transaction, it will play along.

You may have noticed that balance also has "readOnly" defined. In the future,
this may be passed onto the RDBMS in case the relational engine can optimize
the query given its read-only nature.