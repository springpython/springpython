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
import re
import types
import warnings
from springpython.database import ArgumentMustBeNamed
from springpython.database import DataAccessException
from springpython.database import IncorrectResultSizeDataAccessException
from springpython.database import InvalidArgumentType
from springpython.database import factory

class ConnectionFactory(factory.ConnectionFactory):
    def __init__(self):
        warnings.warn("springpython.database's core.ConnectionFactory has moved to factory.ConnectionFactory.",
            DeprecationWarning, 2)
        factory.ConnectionFactory.__init__(self)

class DaoSupport(object):
    """
    Any class that extends this one will be provided with a DatabaseTemplate class
    to help carry out database operations. It requires that a connection object be
    provided during instantion.
    """
    def __init__(self, connectionFactory = None):
        self.databaseTemplate = DatabaseTemplate()
        self.connectionFactory = connectionFactory
        
    def __setattr__(self, name, value):
        """When the connection factory is set, pass it on through to the database template."""
        self.__dict__[name] = value
        if name == "connectionFactory" and value:
            self.__dict__["databaseTemplate"].connectionFactory = value

class DatabaseTemplate(object):
    """
    This class is meant to mimic the Spring framework's JdbcTemplate class.
    Since Python doesn't use JDBC, the name is generalized to "Database"
    """
    def __init__(self, connectionFactory = None):
        self.connectionFactory = connectionFactory
        self.logger = logging.getLogger("springpython.database.core.DatabaseTemplate")

    def __setattr__(self, name, value):
        """When the connection factory is set, initialize a connection to the database."""
        self.__dict__[name] = value
        if name == "connectionFactory" and value:
            self.__db = value.getConnection()

    def convertFromJavaToPythonNotation(self, sqlQuery):
        """This is to help Java users migrate to Python. Java notation defines binding variables
        points with '?', while Python uses '%s', and this method will convert from one format
        to the other."""
        return re.sub(pattern="\?", repl="%s", string=sqlQuery)
        
    def execute(self, sqlStatement, args = None):
        """Issue a single SQL execute, typically a DDL statement."""
        sqlStatement = self.convertFromJavaToPythonNotation(sqlStatement)

        cursor = self.__db.cursor()
        error = None
        rowsAffected = 0
        try:
            try:
                if args:
                    cursor.execute(sqlStatement, args)
                    rowsAffected = cursor.rowcount
                else:
                    cursor.execute(sqlStatement)
                    rowsAffected = cursor.rowcount
            except Exception, e:
                self.logger.debug("execute.execute: Trapped %s while trying to execute '%s'" % (e, sqlStatement))
                error = e
        finally:
            try:
                cursor.close()
            except Exception, e:
                self.logger.debug("execute.close: Trapped %s, and throwing away." % e)
            
        if error:
            raise DataAccessException(error)
        
        return rowsAffected
    
    def query(self, sqlQuery, args = None, rowhandler = None):
        """Execute a query given static SQL, reading the ResultSet on a per-row basis with a RowCallbackHandler.
        If args is provided, bind the arguments (to avoid SQL injection attacks)."""

        # This is the case where only two, non-named arguments were provided, the sqlQuery and one other.
        # If the second argument was 'args', it is invalid since 'rowhandler' is required.
        # It is was 'rowhandler', it shifted into 'args' position, and requires naming.
        if args and not rowhandler:
            raise ArgumentMustBeNamed(argumentName="rowhandler")

        return [rowhandler.processRow(row) for row in self.queryForList(sqlQuery, args)]
    
    def queryForList(self, sqlQuery, args = None):
        """Execute a query for a result list, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""

        if args and type(args) not in self.connectionFactory.acceptableTypes:
            raise InvalidArgumentType(type(args), self.connectionFactory.acceptableTypes)

        sqlQuery = self.convertFromJavaToPythonNotation(sqlQuery)
        
        cursor = self.__db.cursor()
        error = None
        results = None
        try:
            try:
                if args:
                    cursor.execute(sqlQuery, args)
                else:
                    cursor.execute(sqlQuery)
                results = cursor.fetchall()
            except Exception, e:
                self.logger.debug("queryForList.execute: Trapped %s while trying to execute '%s'" % (e, sqlQuery))
                error = e
        finally:
            try:
                cursor.close()
            except Exception, e:
                self.logger.debug("queryForList.close: Trapped %s, and throwing away." % e)

        if error:
            self.logger.debug("queryForList: I thought about kicking this up the chain => %s" % error)

        # Convert multi-item tuple into list
        return [result for result in results]

    def queryForInt(self, sqlQuery, args = None):
        """Execute a query that results in an int value, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""
        return self.queryForObject(sqlQuery, args, types.IntType)
    
    def queryForLong(self, sqlQuery, args = None):
        """Execute a query that results in an int value, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""
        return self.queryForObject(sqlQuery, args, types.LongType)
    
    def queryForObject(self, sqlQuery, args = None, requiredType = None):
        """Execute a query that results in an int value, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""

        # This is the case where only two, non-named arguments were provided, the sqlQuery and one other.
        # If the second argument was 'args', it is invalid since 'requiredType' is required.
        # It is was 'requiredType', it shifted into 'args' position, and requires naming.
        if args and not requiredType:
            raise ArgumentMustBeNamed(argumentName="requiredType")

        results = self.queryForList(sqlQuery, args)
        
        if len(results) != 1:
            raise IncorrectResultSizeDataAccessException("Instead of getting one row, this query returned %s" % len(results))
        
        if len(results[0]) != 1:
            raise IncorrectResultSizeDataAccessException("Instead of getting one column, this query returned %s" % len(results[0]))

        if type(results[0][0]) != requiredType:
            raise DataAccessException("Expected %s, but instead got %s"% (requiredType, type(results[0][0])))

        return results[0][0]

    def update(self, sqlStatement, args = None):
        """Issue a single SQL update.  If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""
        return self.execute(sqlStatement, args)
    
    
class RowCallbackHandler(object):
    """
    This is an interface to handle one row of data.
    """
    def processRow(self, row):
        raise NotImplementedError()

