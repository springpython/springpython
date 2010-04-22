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
import os
import re
import termios
import subprocess
from getpass import getpass
from springpython.database.core import DatabaseTemplate
from springpython.database.factory import MySQLConnectionFactory

def tryMySQL():
    """Try to setup the database through MySQL. If it fails, return None. Otherwise, return
    a handle on the database. Later on, other databases may be supported."""
    try:
        import MySQLdb
    except:
        print "You don't appear to have MySQLdb module."
        raise NotImplementedError("Can't setup the database")
    
    useGetPass = True
    for i in [1, 2, 3]:
        if useGetPass:
            try:
                password = getpass("Mysql 'root' password: ")
            except termios.error, e:
                print "Okay, we can't use that mechanism to ask for your password."
                useGetPass = False
                password = raw_input("Mysql 'root' password: ")
        else:
            password = raw_input("Mysql 'root' password: ")          
        
        try:
            connection = MySQLdb.connect(host="localhost", user="root", passwd=password, db="")
            connection.close()
            del(connection)
            break
        except:
            print "!!! Bad password!"
            if i >= 3:
                print "!!! Failed all attempts to connection to the database>"
                return None

    subprocess.Popen([r"mysql","-uroot", "-p%s" % password],
                     stdout=subprocess.PIPE,
                     stdin=file("db/mysql/dropDB.txt")).communicate()[0]

    subprocess.Popen([r"mysql","-uroot", "-p%s" % password],
                     stdout=subprocess.PIPE,
                     stdin=file("db/mysql/initDB.txt")).communicate()[0]
    connectionFactory = MySQLConnectionFactory()
    connectionFactory.username = "springpython"
    connectionFactory.password = "springpython"
    connectionFactory.hostname = "localhost"
    connectionFactory.db = "petclinic"
    return connectionFactory

def setupDatabase():
    """Figure out what type of database exists, and then set it up."""
    connectionFactory = tryMySQL()
    
    if connectionFactory is None:
        raise Exception("+++ Could not setup MySQL. We don't support any others yet.")
    
    databaseTemplate = DatabaseTemplate(connectionFactory)
    
    for sqlStatement in [line.strip() for line in open("db/populateDB.txt").readlines() 
                         if line.strip() != ""]:
        databaseTemplate.execute(sqlStatement)
        
    print "+++ Database is setup."
    
def main():
    print "+++ Setting up the Spring Python demo application 'petclinic'"
    
    setupDatabase()

if __name__ == "__main__":
    main()
