"""
   Copyright 2006-2008 Greg L. Turnquist, All Rights Reserved

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
import inspect
import logging
import re
import types
from springpython.aop import MethodInterceptor
from springpython.aop import ProxyFactoryComponent
from springpython.context import DecoratorBasedApplicationContext
from springpython.context.decorator import decorator

logger = logging.getLogger("springpython.database.transaction")

class TransactionException(Exception):
    pass

class TransactionPropagationException(TransactionException):
    pass

class TransactionStatus(object):
    pass

class DefaultTransactionStatus(TransactionStatus):
    pass

class PlatformTransactionManager(object):
    """This interface is used to define the operations necessary in handling transactions."""
    def commit(self, status):
        raise NotImplementedError()

    def getTransaction(self, definition):
        raise NotImplementedError()

    def rollback(self, status):
        raise NotImplementedError()

class ConnectionFactoryTransactionManager(PlatformTransactionManager):
    """
    This transaction manager is based upon using a connection factory to control transactions. Since
    connection factories are tied to vendor-specific databases, this allows delegation of various
    transactional functions on a per-vendor basis.
    """

    def __init__(self, connectionFactory):
        self.connectionFactory = connectionFactory
        self.logger = logging.getLogger("springpython.database.transaction.ConnectionFactoryTransactionManager")
        self.status = []

    def getTransaction(self, definition):
        """According to PEP 249, commits and rollbacks silently start new transactions. Until a more
        robust transaction manager is implemented to handle save points and so forth, this must suffice."""

        self.logger.debug("Analyzing %s" % definition.propagationBehavior)

        startTransaction = False

        if definition.propagationBehavior == "PROPAGATION_REQUIRED":
            if len(self.status) == 0:
                self.logger.debug("There is no current transaction, and one is required, so starting one.")
                startTransaction = True
            self.status.append(DefaultTransactionStatus())

        elif definition.propagationBehavior == "PROPAGATION_SUPPORTS":
            self.logger.debug("This code can execute inside or outside a transaction.")

        elif definition.propagationBehavior == "PROPAGATION_MANDATORY":
            if len(self.status) == 0:
                raise TransactionPropagationException("Trying to execute PROPAGATION_MANDATORY operation while outside TX")
            self.status.append(DefaultTransactionStatus())

        elif definition.propagationBehavior == "PROPAGATION_NEVER":
            if len(self.status) != 0:
                raise TransactionPropagationException("Trying to execute PROPAGATION_NEVER operation while inside TX")

        else:
            raise TransactionPropagationException("Transaction propagation level %s is not supported!" % definition.startTransaction)

        if startTransaction:
            self.logger.debug("START TRANSACTION")
            self.logger.debug("Creating a transaction, propagation = %s, isolation = %s, timeout = %s, readOnly = %s" % (definition.propagationBehavior, definition.isolationLevel, definition.timeout, definition.readOnly))
            self.connectionFactory.commit()

        return self.status

    def commit(self, status):
        self.status = status
        try:
            self.status.pop()
            if len(self.status) == 0:
                self.logger.debug("Commit the changes")
                self.connectionFactory.commit()
                self.logger.debug("END TRANSACTION")
        except IndexError:
            pass

    def rollback(self, status):
        self.status = status
        try:
            self.status.pop()
            if len(self.status) == 0:
                self.logger.debug("Rolling back the transaction.")
                self.connectionFactory.rollback()
                self.logger.debug("END TRANSACTION")
        except IndexError:
            pass

class TransactionDefinition(object):
    def __init__(self, isolationLevel = None, name = None, propagationBehavior = None, timeout = None, readOnly = None):
        self.isolationLevel = isolationLevel
        self.name = name
        self.propagationBehavior = propagationBehavior
        self.timeout = timeout
        self.readOnly = readOnly

class DefaultTransactionDefinition(TransactionDefinition):
    def __init__(self, isolationLevel = "ISOLATION_DEFAULT", name = "", propagationBehavior = "PROPAGATION_REQUIRED", timeout = "TIMEOUT_DEFAULT", readOnly = False):
        TransactionDefinition.__init__(self, isolationLevel, name, propagationBehavior, timeout, readOnly)

class TransactionTemplate(DefaultTransactionDefinition):
    """This utility class is used to simplify defining transactional blocks. Any exceptions thrown inside the
    transaction block will be propagated to whom ever is calling the template execute method."""

    def __init__(self, transactionManager):
        DefaultTransactionDefinition.__init__(self)	
        self.transactionManager = transactionManager
        self.logger = logging.getLogger("springpython.database.transaction.TransactionTemplate")

    def execute(self, transactionCallback):
        """Execute the action specified by the given callback object within a transaction."""

        status = self.transactionManager.getTransaction(self)
        result = None
        try:
            self.logger.debug("Execute the steps inside the transaction")
            result = transactionCallback.doInTransaction(status)
            self.transactionManager.commit(status)
        except Exception, e:
            self.logger.debug("Exception: (%s)" % e)
            self.transactionManager.rollback(status)
            raise e
        return result

    def setTxAttributes(self, txAttributes):
        for txDefProp in txAttributes:
            if txDefProp.startswith("ISOLATION"):
                if txDefDrop != self.isolationLevel:        self.isolationLevel = txDefProp
            elif txDefProp.startswith("PROPAGATION"):
                if txDefProp != self.propagationBehavior:   self.propagationBehavior = txDefProp
            elif txDefProp.startswith("TIMEOUT"):
                if txDefProp != self.timeout:               self.timeout = txDefProp
            elif txDefProp == "readOnly":
                if not self.readOnly:                       self.readOnly = True
            else:
                self.logger.debug("Don't know how to handle %s" % txDefProp)


class TransactionCallback(object):
    """This interface defines the basic action needed to plug into the TransactionTemplate"""
    def doInTransaction(self, status):
        raise NotImplementedError()

class TransactionCallbackWithoutResult(TransactionCallback):
    """This abstract class implements the TransactionCallback, but assumes no value is being returned."""
    def __init__(self):
        self.logger = logging.getLogger("springpython.database.transaction.TransactionCallbackWithoutResult")

    def doInTransaction(self, status):
        self.logger.debug("Starting a transaction without result")
        self.doInTransactionWithoutResult(status)
        self.logger.debug("Completing a transaction without result")
        return None

    def doInTransactionWithoutResult(self, status):
        pass

class TransactionalInterceptor(MethodInterceptor):
    """This interceptor is used by the TransactionProxyFactoryComponent in order to wrap
    method calls with transactions."""
    def __init__(self, txManager, transactionAttributes):
        self.logger = logging.getLogger("springpython.database.transaction.TransactionalInterceptor")
        self.transactionAttributes = transactionAttributes
        self.txManager = txManager

    def invoke(self, invocation):
        class txWrapper(TransactionCallback):
            def doInTransaction(s, status):
                return invocation.proceed()

        txTemplate = TransactionTemplate(self.txManager)

        # Iterate over the txAttributes, and when a method match is found, apply the properties
        for pattern, txDefProps in self.transactionAttributes:
            if re.compile(pattern).match(invocation.methodName):
                self.logger.debug("%s matches pattern %s, tx attributes = %s" % (invocation.methodName, pattern, txDefProps))
                txTemplate.setTxAttributes(txDefProps)
                break
            
        self.logger.debug("Call TransactionTemplate")
        try:
            results = txTemplate.execute(txWrapper())
        except Exception, e:
            self.logger.debug("Exception => %s" % e)
            raise e
        self.logger.debug("Return from TransactionTemplate")
        return results

class TransactionProxyFactoryComponent(ProxyFactoryComponent):
    """This class acts like the target object, and routes function calls through a
    transactional interceptor."""
    def __init__(self, txManager, target, transactionAttributes):
        self.logger = logging.getLogger("springpython.database.transaction.TransactionProxyFactoryComponent")
        ProxyFactoryComponent.__init__(self, target, TransactionalInterceptor(txManager, transactionAttributes))

def Transactional(txAttributes = None):
    """
    This decorator is actually a utility function that returns an embedded decorator, in order
    to handle whether it was called in any of the following ways:

    @Transactional()
    def foo():
        pass

    @Transactional
    def foo():
        pass

    The first two ways get parsed by Python as:

    foo = Transactional("some contextual string")(foo)      # first way
    foo = Transactional()(foo)                              # second way

    Since this is expected, they are granted direct access to the embedded transactional_wrapper.

    However, the third way ends up getting parsed by Python as:

    foo = Transactional(foo)

    This causes context to improperly get populated with a function instead of a string. This
    requires recalling this utility like:

    return Transactional()(context)
    """

    @decorator
    def transactional_wrapper(f, *args, **kwargs):
        """
        transactional_wrapper is used to wrap the decorated function in a TransactionTemplate callback,
        and then return the results.
        """
        class txDefinition(TransactionCallback):
            """TransactionTemplate requires a callback defined this way."""
            def doInTransaction(s, status):
                return f(*args, **kwargs)

        try:
            # Assumes transactionManager is supplied by AutoTransactionalComponent
            transactionTemplate = TransactionTemplate(transactionManager)
            if txAttributes is not None:
                transactionTemplate.setTxAttributes(txAttributes)
            else:
                logger.debug("There are NO txAttributes! %s" % txAttributes)
            return transactionTemplate.execute(txDefinition())
        except NameError:
            # If no AutoTransactionalComponent found in IoC container, then pass straight through.
            return txDefinition().doInTransaction(None)

    if type(txAttributes) == types.FunctionType:
        return Transactional()(txAttributes)
    else:
        return transactional_wrapper


class AutoTransactionalComponent(object):
    """
    This component is used to automatically scan objects in an IoC container, and if @Transaction
    is found applied to any of the component's methods, link it with a TransactionManager.
    """

    def __init__(self, transactionManager):
        self.transactionManager = transactionManager
        self.logger = logging.getLogger("springpython.database.transaction.AutoTransactionalComponent")

    def postProcessAfterInitialization(self, container):
        """This setup is run after all objects in the container have been created."""
        for component in container.components:
            # Check every method in the component...
            for name, method in inspect.getmembers(component, inspect.ismethod):
                try:
                    # If the method contains _call_, then you are looking at a wrapper...
                    wrapper = method.im_func.func_globals["_call_"]
                    if wrapper.func_name == "transactional_wrapper":  # name of @Transactional's wrapper method
                        self.logger.debug("Linking transactionManager with %s" % name)
                        wrapper.func_globals["transactionManager"] = self.transactionManager
                except KeyError, e:   # If the method is NOT wrapped, there will be no _call_ attribute
                    pass


