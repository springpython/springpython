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
import re
import sys
import types

class ConnectionFactory(object):
    def __init__(self, acceptableTypes):
        self.__db = None
        self.acceptableTypes = acceptableTypes

    """This interface defines an object that is able to make database connections.
    This allows database connections to be defined inside application contexts, and
    fed to DAO and DatabaseTemplates."""
    def connect(self):
        raise NotImplementedError()

    def getConnection(self):
        if self.__db is None:
            self.__db = self.connect()
        return self.__db

    def commit(self):
        if self.inTransaction():
            self.getConnection().commit()

    def rollback(self):
        if self.inTransaction():
            self.getConnection().rollback()

    def inTransaction(self):
        raise NotImplementedError()

    def countType(self):
        raise NotImplementedError()
    
    def convertFromJavaToPythonNotation(self, sqlQuery):
        """This is to help Java users migrate to Python. Java notation defines binding variables
        points with '?', while Python uses '%s', and this method will convert from one format
        to the other."""
        return re.sub(pattern="\?", repl="%s", string=sqlQuery)

class MySQLConnectionFactory(ConnectionFactory):
    def __init__(self, username = None, password = None, hostname = None, db = None):
        ConnectionFactory.__init__(self, [types.TupleType])
        self.username = username
        self.password = password
        self.hostname = hostname
        self.db = db
        
    def connect(self):
        """The import statement is delayed so the library is loaded ONLY if this factory is really used."""
        import MySQLdb
        return MySQLdb.connect(self.hostname, self.username, self.password, self.db)

    def inTransaction(self):
        return True

    def countType(self):
        return types.LongType

class PgdbConnectionFactory(ConnectionFactory):
    def __init__(self, user = None, password = None, host = None, database = None):
        ConnectionFactory.__init__(self, [types.TupleType])
        self.user = user
        self.password = password
        self.host = host
        self.database = database
        
    def connect(self):
        """The import statement is delayed so the library is loaded ONLY if this factory is really used."""
        import pgdb
        return pgdb.connect(user=self.user, password=self.password, database=self.database, host=self.host)

    def inTransaction(self):
        return True

    def countType(self):
        return types.LongType

class Sqlite3ConnectionFactory(ConnectionFactory):
    def __init__(self, db = None):
        ConnectionFactory.__init__(self, [types.TupleType])
        self.db = db

    def connect(self):
        """The import statement is delayed so the library is loaded ONLY if this factory is really used."""
        import sqlite3
        return sqlite3.connect(self.db)               

    def inTransaction(self):
        return True

    def countType(self):
        return types.IntType

    def convertFromJavaToPythonNotation(self, sqlQuery):
        """sqlite3 uses the ? notation, like Java's JDBC."""
        return re.sub(pattern="%s", repl="?", string=sqlQuery)

class cxoraConnectionFactory(ConnectionFactory):
    def __init__(self, username = None, password = None, hostname = None, db = None):
        ConnectionFactory.__init__(self, [types.DictType])
        self.username = username
        self.password = password
        self.hostname = hostname
        self.db = db

    def connect(self):
        """The import statement is delayed so the library is loaded ONLY if this factory is really used."""
        import cx_Oracle
        return cx_Oracle.connect(self.username, self.password, self.db)
