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
import inspect
import logging
import re
import types
from springpython.aop import MethodInterceptor
from springpython.aop import ProxyFactoryObject
from springpython.context import ObjectPostProcessor
from springpython.config.decorator import decorator

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

    def __init__(self, connection_factory):
        self.connection_factory = connection_factory
        self.logger = logging.getLogger("springpython.database.transaction.ConnectionFactoryTransactionManager")
        self.status = []

    def getTransaction(self, definition):
        """According to PEP 249, commits and rollbacks silently start new transactions. Until a more
        robust transaction manager is implemented to handle save points and so forth, this must suffice."""

        self.logger.debug("Analyzing %s" % definition.propagation)

        start_tx = False

        if definition.propagation == "PROPAGATION_REQUIRED":
            if len(self.status) == 0:
                self.logger.debug("There is no current transaction, and one is required, so starting one.")
                start_tx = True
            self.status.append(DefaultTransactionStatus())

        elif definition.propagation == "PROPAGATION_SUPPORTS":
            self.logger.debug("This code can execute inside or outside a transaction.")

        elif definition.propagation == "PROPAGATION_MANDATORY":
            if len(self.status) == 0:
                raise TransactionPropagationException("Trying to execute PROPAGATION_MANDATORY operation while outside TX")
            self.status.append(DefaultTransactionStatus())

        elif definition.propagation == "PROPAGATION_NEVER":
            if len(self.status) != 0:
                raise TransactionPropagationException("Trying to execute PROPAGATION_NEVER operation while inside TX")

        else:
            raise TransactionPropagationException("Transaction propagation level %s is not supported!" % definition.start_tx)

        if start_tx:
            self.logger.debug("START TRANSACTION")
            self.logger.debug("Creating a transaction, propagation = %s, isolation = %s, timeout = %s, read_only = %s" % (definition.propagation, definition.isolation, definition.timeout, definition.read_only))
            self.connection_factory.commit()

        return self.status

    def commit(self, status):
        self.status = status
        try:
            self.status.pop()
            if len(self.status) == 0:
                self.logger.debug("Commit the changes")
                self.connection_factory.commit()
                self.logger.debug("END TRANSACTION")
        except IndexError:
            pass

    def rollback(self, status):
        self.status = status
        try:
            self.status.pop()
            if len(self.status) == 0:
                self.logger.debug("Rolling back the transaction.")
                self.connection_factory.rollback()
                self.logger.debug("END TRANSACTION")
        except IndexError:
            pass

class TransactionDefinition(object):
    def __init__(self, isolation = None, name = None, propagation = None, timeout = None, read_only = None):
        self.isolation = isolation
        self.name = name
        self.propagation = propagation
        self.timeout = timeout
        self.read_only = read_only

class DefaultTransactionDefinition(TransactionDefinition):
    def __init__(self, isolation = "ISOLATION_DEFAULT", name = "", propagation = "PROPAGATION_REQUIRED", timeout = "TIMEOUT_DEFAULT", read_only = False):
        TransactionDefinition.__init__(self, isolation, name, propagation, timeout, read_only)

class TransactionTemplate(DefaultTransactionDefinition):
    """This utility class is used to simplify defining transactional blocks. Any exceptions thrown inside the
    transaction block will be propagated to whom ever is calling the template execute method."""

    def __init__(self, tx_manager):
        DefaultTransactionDefinition.__init__(self)	
        self.tx_manager = tx_manager
        self.logger = logging.getLogger("springpython.database.transaction.TransactionTemplate")

    def execute(self, transactionCallback):
        """Execute the action specified by the given callback object within a transaction."""

        status = self.tx_manager.getTransaction(self)
        result = None
        try:
            self.logger.debug("Execute the steps inside the transaction")
            result = transactionCallback.do_in_transaction(status)
            self.tx_manager.commit(status)
        except Exception, e:
            self.logger.debug("Exception: (%s)" % e)
            self.tx_manager.rollback(status)
            raise e
        return result

    def setTxAttributes(self, tx_attributes):
        for tx_def_prop in tx_attributes:
            if tx_def_prop.startswith("ISOLATION"):
                if tx_def_prop != self.isolation:       self.isolation = tx_def_prop
            elif tx_def_prop.startswith("PROPAGATION"):
                if tx_def_prop != self.propagation:     self.propagation = tx_def_prop
            elif tx_def_prop.startswith("TIMEOUT"):
                if tx_def_prop != self.timeout:         self.timeout = tx_def_prop
            elif tx_def_prop == "read_only":
                if not self.read_only:                  self.read_only = True
            else:
                self.logger.debug("Don't know how to handle %s" % tx_def_prop)


class TransactionCallback(object):
    """This interface defines the basic action needed to plug into the TransactionTemplate"""
    def do_in_transaction(self, status):
        raise NotImplementedError()

class TransactionCallbackWithoutResult(TransactionCallback):
    """This abstract class implements the TransactionCallback, but assumes no value is being returned."""
    def __init__(self):
        self.logger = logging.getLogger("springpython.database.transaction.TransactionCallbackWithoutResult")

    def do_in_transaction(self, status):
        self.logger.debug("Starting a transaction without result")
        self.do_in_tx_without_result(status)
        self.logger.debug("Completing a transaction without result")
        return None

    def do_in_tx_without_result(self, status):
        pass

class TransactionalInterceptor(MethodInterceptor):
    """This interceptor is used by the TransactionProxyFactoryObject in order to wrap
    method calls with transactions."""
    def __init__(self, tx_manager, tx_attributes):
        self.logger = logging.getLogger("springpython.database.transaction.TransactionalInterceptor")
        self.tx_attributes = tx_attributes
        self.tx_manager = tx_manager

    def invoke(self, invocation):
        class tx_def(TransactionCallback):
            def do_in_transaction(s, status):
                return invocation.proceed()

        tx_template = TransactionTemplate(self.tx_manager)

        # Iterate over the tx_attributes, and when a method match is found, apply the properties
        for pattern, tx_def_props in self.tx_attributes:
            if re.compile(pattern).match(invocation.method_name):
                self.logger.debug("%s matches pattern %s, tx attributes = %s" % (invocation.method_name, pattern, tx_def_props))
                tx_template.setTxAttributes(tx_def_props)
                break
            
        self.logger.debug("Call TransactionTemplate")
        try:
            results = tx_template.execute(tx_def())
        except Exception, e:
            self.logger.debug("Exception => %s" % e)
            raise e
        self.logger.debug("Return from TransactionTemplate")
        return results

class TransactionProxyFactoryObject(ProxyFactoryObject):
    """This class acts like the target object, and routes function calls through a
    transactional interceptor."""
    def __init__(self, tx_manager, target, tx_attributes):
        self.logger = logging.getLogger("springpython.database.transaction.TransactionProxyFactoryObject")
        ProxyFactoryObject.__init__(self, target, TransactionalInterceptor(tx_manager, tx_attributes))

def transactional(tx_attributes = None):
    """
    This decorator is actually a utility function that returns an embedded decorator, in order
    to handle whether it was called in any of the following ways:

    @transactional()
    def foo():
        pass

    @transactional
    def foo():
        pass

    The first two ways get parsed by Python as:

    foo = transactional("some contextual string")(foo)      # first way
    foo = transactional()(foo)                              # second way

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
        class tx_def(TransactionCallback):
            """TransactionTemplate requires a callback defined this way."""
            def do_in_transaction(s, status):
                return f(*args, **kwargs)

        try:
            # Assumes tx_manager is supplied by AutoTransactionalObject
            tx_template = TransactionTemplate(tx_manager)
            if tx_attributes is not None:
                tx_template.setTxAttributes(tx_attributes)
            else:
                logger.debug("There are NO tx_attributes! %s" % tx_attributes)
            return tx_template.execute(tx_def())
        except NameError:
            # If no AutoTransactionalObject found in IoC container, then pass straight through.
            return tx_def().do_in_transaction(None)

    if type(tx_attributes) == types.FunctionType:
        return transactional()(tx_attributes)
    else:
        return transactional_wrapper


class AutoTransactionalObject(ObjectPostProcessor):
    """
    This object is used to automatically scan objects in an IoC container, and if @Transaction
    is found applied to any of the object's methods, link it with a TransactionManager.
    """

    def __init__(self, tx_manager):
        self.tx_manager = tx_manager
        self.logger = logging.getLogger("springpython.database.transaction.AutoTransactionalObject")

    def post_process_after_initialization(self, obj, obj_name):
        """This setup is run after all objects in the container have been created."""
        # Check every method in the object...
        for name, method in inspect.getmembers(obj, inspect.ismethod):
            try:
                # If the method contains _call_, then you are looking at a wrapper...
                wrapper = method.im_func.func_globals["_call_"]
                if wrapper.func_name == "transactional_wrapper":  # name of @transactional's wrapper method
                    self.logger.debug("Linking tx_manager with %s" % name)
                    wrapper.func_globals["tx_manager"] = self.tx_manager
            except KeyError, e:   # If the method is NOT wrapped, there will be no _call_ attribute
                pass
        return obj


