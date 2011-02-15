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
from springpython.database import ArgumentMustBeNamed
from springpython.database import DataAccessException
from springpython.database import IncorrectResultSizeDataAccessException
from springpython.database import InvalidArgumentType
from springpython.database import factory

class DaoSupport(object):
    """
    Any class that extends this one will be provided with a DatabaseTemplate class
    to help carry out database operations. It requires that a connection object be
    provided during instantion.
    """
    def __init__(self, connection_factory = None):
        self.database_template = DatabaseTemplate()
        self.connection_factory = connection_factory
        
    def __setattr__(self, name, value):
        """When the connection factory is set, pass it on through to the database template."""
        self.__dict__[name] = value
        if name == "connection_factory" and value:
            self.__dict__["database_template"].connection_factory = value

class DatabaseTemplate(object):
    """
    This class is meant to mimic the Spring framework's JdbcTemplate class.
    Since Python doesn't use JDBC, the name is generalized to "Database"
    """
    def __init__(self, connection_factory = None):
        self.connection_factory = connection_factory
        self.logger = logging.getLogger("springpython.database.core.DatabaseTemplate")

    def __del__(self):
        "When this template goes out of scope, need to close the connection it formed."
        if self.connection_factory is not None: self.connection_factory.close()
            
    def _execute(self, sql_statement, args = None):
        """Issue a single SQL execute, typically a DDL statement."""

        if args and type(args) not in self.connection_factory.acceptable_types:
            raise InvalidArgumentType(type(args), self.connection_factory.acceptable_types)

        sql_statement = self.connection_factory.convert_sql_binding(sql_statement)

        cursor = self.connection_factory.getConnection().cursor()
        error = None
        rows_affected = 0
        try:
            try:
                if args:
                    cursor.execute(sql_statement, args)
                    rows_affected = cursor.rowcount
                    lastrowid = cursor.lastrowid
                else:
                    cursor.execute(sql_statement)
                    rows_affected = cursor.rowcount
                    lastrowid = cursor.lastrowid
            except Exception, e:
                self.logger.debug("execute.execute: Trapped %s while trying to execute '%s'" % (e, sql_statement))
                error = e
        finally:
            try:
                cursor.close()
            except Exception, e:
                self.logger.debug("execute.close: Trapped %s, and throwing away." % e)
            
        if error:
            raise DataAccessException(error)
        
        return {"rows_affected":rows_affected, "lastrowid":lastrowid}

    def execute(self, sql_statement, args = None):
        """Execute a single SQL statement, and return the number of rows affected."""
        return self._execute(sql_statement, args)["rows_affected"]

    def insert_and_return_id(self, sql_statement, args = None):
        """Execute a single INSERT statement, and return the PK of the new row."""
        return self._execute(sql_statement, args)["lastrowid"]
    
    def query(self, sql_query, args = None, rowhandler = None):
        """Execute a query given static SQL, reading the ResultSet on a per-row basis with a RowMapper.
        If args is provided, bind the arguments (to avoid SQL injection attacks)."""

        # This is the case where only two, non-named arguments were provided, the sql_query and one other.
        # If the second argument was 'args', it is invalid since 'rowhandler' is required.
        # It is was 'rowhandler', it shifted into 'args' position, and requires naming.
        if args and not rowhandler:
            raise ArgumentMustBeNamed(arg_name="rowhandler")

        results, metadata = self.__query_for_list(sql_query, args)
        return [rowhandler.map_row(row, metadata) for row in results]

    def query_for_list(self, sql_query, args = None):
        results, metadata = self.__query_for_list(sql_query, args)
        return results
    
    def __query_for_list(self, sql_query, args = None):
        """Execute a query for a result list, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""

        if args and type(args) not in self.connection_factory.acceptable_types:
            raise InvalidArgumentType(type(args), self.connection_factory.acceptable_types)

        sql_query = self.connection_factory.convert_sql_binding(sql_query)
        
        cursor = self.connection_factory.getConnection().cursor()
        error = None
        results = None
        metadata = None
        try:
            try:
                if args:
                    cursor.execute(sql_query, args)
                else:
                    cursor.execute(sql_query)
                results = cursor.fetchall()
                metadata = [{"name":row[0], "type_code":row[1], "display_size":row[2], "internal_size":row[3], "precision":row[4], "scale":row[5], "null_ok":row[6]} for row in cursor.description]
            except Exception, e:
                self.logger.debug("query_for_list.execute: Trapped %s while trying to execute '%s'" % (e, sql_query))
                error = e
        finally:
            try:
                cursor.close()
            except Exception, e:
                self.logger.debug("query_for_list.close: Trapped %s, and throwing away." % e)

        if error:
            self.logger.debug("query_for_list: I thought about kicking this up the chain => %s" % error)

        # Convert multi-item tuple into list
        return [result for result in results or []], metadata

    def query_for_int(self, sql_query, args = None):
        """Execute a query that results in an int value, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""
        return self.query_for_object(sql_query, args, types.IntType)
    
    def query_for_long(self, sql_query, args = None):
        """Execute a query that results in an int value, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""
        return self.query_for_object(sql_query, args, types.LongType)
    
    def query_for_object(self, sql_query, args = None, required_type = None):
        """Execute a query that results in an int value, given static SQL. If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""

        # This is the case where only two, non-named arguments were provided, the sql_query and one other.
        # If the second argument was 'args', it is invalid since 'required_type' is required.
        # It is was 'required_type', it shifted into 'args' position, and requires naming.
        if args and not required_type:
            raise ArgumentMustBeNamed(arg_name="required_type")

        results = self.query_for_list(sql_query, args)
        
        if len(results) != 1:
            raise IncorrectResultSizeDataAccessException("Instead of getting one row, this query returned %s" % len(results))
        
        if len(results[0]) != 1:
            raise IncorrectResultSizeDataAccessException("Instead of getting one column, this query returned %s" % len(results[0]))

        equivalentTypes = [
                           [types.UnicodeType, types.StringType]
                           ]
        if type(results[0][0]) != required_type:
            foundEquivType = False
            for equivType in equivalentTypes:
                if type(results[0][0]) in equivType and required_type in equivType:
                    foundEquivType = True
                    break
            if not foundEquivType:
                raise DataAccessException("Expected %s, but instead got %s"% (required_type, type(results[0][0])))

        return results[0][0]

    def update(self, sql_statement, args = None):
        """Issue a single SQL update.  If args is provided, bind the arguments 
        (to avoid SQL injection attacks)."""
        return self.execute(sql_statement, args)
    
    
class RowMapper(object):
    """
    This is an interface to handle one row of data.
    """
    def map_row(self, row, metadata=None):
        raise NotImplementedError()

class DictionaryRowMapper(RowMapper):
    """
    This row mapper converts the tuple into a dictionary using the column names as the keys.
    """
    def map_row(self, row, metadata=None):
        if metadata is not None:
            obj = {}
            for i, column in enumerate(metadata):
                obj[column["name"]] = row[i]
            return obj
        else:
            raise DataAccessException("metadata is None, unable to convert result set into a dictionary")

class SimpleRowMapper(RowMapper):
    """
    This row mapper uses convention over configuration to create and populate attributes
    of an object.
    """
    def __init__(self, clazz):
        self.clazz = clazz

    def map_row(self, row, metadata=None):
        if metadata is not None:
            obj = self.clazz()
            for i, column in enumerate(metadata):
                setattr(obj, column["name"], row[i])
            return obj
        else:
            raise DataAccessException("metadata is None, unable to map result set into %s instance" % self.clazz)

