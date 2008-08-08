"""
    Copyright 2006-2007 Greg L. Turnquist, All Rights Reserved
    
    This file is part of PetClinic.

    PetClinic is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import re
import termios
import subprocess
from getpass import getpass
from springpython.database.core import DatabaseTemplate
from springpython.database.mysql import MySQLConnectionFactory

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
