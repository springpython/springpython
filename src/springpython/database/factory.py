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

class SqliteConnectionFactory(ConnectionFactory):
    def __init__(self, db = None, autocommit=False):
        ConnectionFactory.__init__(self, [types.TupleType])
        self.db = db
        self.autocommit = autocommit

    def connect(self):
        """The import statement is delayed so the library is loaded ONLY if this factory is really used."""
        import sqlite
        return sqlite.connect(db=self.db, autocommit=self.autocommit)

    def inTransaction(self):
        return self.getConnection().inTransaction

    def countType(self):
        return types.FloatType

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
