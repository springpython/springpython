Data Access
===========

DatabaseTemplate
----------------

Writing SQL-based programs has a familiar pattern that must be repeated over
and over. The DatabaseTemplate resolves that by handling the plumbing of these
operations while leaving you in control of the part that matters the most,
the SQL.

.. _dao-external-dependencies:

External dependencies
+++++++++++++++++++++

DatabaseTemplate requires the use of external libraries for connecting to
SQL databases. Depending on which SQL connection factory you're about to use,
you need to install following dependencies:

* *springpython.database.factory.MySQLConnectionFactory* -
  needs `MySQLdb <http://sourceforge.net/projects/mysql-python/>`_ for connecting to MySQL,

* *springpython.database.factory.PgdbConnectionFactory* -
  needs `PyGreSQL <http://www.pygresql.org/>`_ for connecting to PostgreSQL,

* *springpython.database.factory.Sqlite3ConnectionFactory* -
  needs `PySQLite <http://pypi.python.org/pypi/pysqlite/>`_ for connecting to SQLite 3, note that PySQLite is part
  of Python 2.5 and later so you need to install it separately only if you're
  using Python 2.4,

* *springpython.database.factory.cxoraConnectionFactory* -
  needs `cx_Oracle <http://pypi.python.org/pypi/cx_Oracle>`_ for connecting to Oracle,

* *springpython.database.factory.SQLServerConnectionFactory* -
  needs `PyODBC <http://pypi.python.org/pypi/pyodbc>`_ for connecting to SQL Server.

Traditional Database Query
++++++++++++++++++++++++++

If you have written a database SELECT statement following Python's
`DB-API 2.0 <http://www.python.org/dev/peps/pep-0249/>`_, it would something
like this (MySQL example)::

    conn = MySQL.connection(username="me", password="secret", hostname="localhost", db="springpython")
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute("select title, air_date, episode_number, writer from tv_shows where name = %s", ("Monty Python",))
        for row in cursor.fetchall():
            tvShow = TvShow(title=row[0], airDate=row[1], episodeNumber=row[2], writer=row[3])
            results.append(tvShow)
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    conn.close()
    return results

I know, you don't have to open and close a connection for every query, but
let's look past that part. In every definition of a SQL query, you must create
a new cursor, execute against the cursor, loop through the results, and most
importantly (and easy to forget) *close the cursor*. Of course you will wrap this
in a method instead of plugging in this code where ever you need the information.
But every time you need another query, you have to repeat this dull pattern over
and over again. The only thing different is the actual SQL code you must write
and converting it to a list of objects.

I know there are many object relational mappers (ORMs) out there, but sometimes
you need something simple and sweet. That is where *DatabaseTemplate* comes in.

Database Template
+++++++++++++++++

The same query above can be written using a *DatabaseTemplate*. The only thing
you must provide is the SQL and a *RowMapper* to process one row of data. The
template does the rest::

  """ The following part only has to be done once."""
  from springpython.database.core import *
  from springpython.database.factory import *
  connectionFactory = MySQLConnectionFactory(username="me", password="secret", hostname="localhost", db="springpython")
  dt = DatabaseTemplate(connectionFactory)

  class TvShowMapper(RowMapper):
      """This will handle one row of database. It can be reused for many queries if they
         are returning the same columns."""
      def map_row(self, row, metadata=None):
          return TvShow(title=row[0], airDate=row[1], episodeNumber=row[2], writer=row[3])


  results = dt.query("select title, air_date, episode_number, writer from tv_shows where name = %s", \
                     ("Monty Python",), TvShowMapper())

Well, no sign of a cursor anywhere. If you didn't have to worry about opening
it, you don't have to worry about closing it. I know this is about the same
amount of code as the traditional example. Where DatabaseTemplate starts to
shine is when you want to write ten different TV_SHOW queries::

  results = dt.query("select title, air_date, episode_number, writer from tv_shows where episode_number < %s", \
                     (100,), TvShowMapper())
  results = dt.query("select title, air_date, episode_number, writer from tv_shows where upper(title) like %s", \
                     ("%CHEESE%",), TvShowMapper())
  results = dt.query("select title, air_date, episode_number, writer from tv_shows where writer in ('Cleese', 'Graham')",
                     rowhandler=TvShowMapper())

You don't have to reimplement the rowhandler. For these queries, you can focus
on the SQL you want to write, not the mind-numbing job of managing database
cursors.

Mapping rows into objects using convention over configuration
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

A powerful feature provided by databases is the ability to look up column names.
Spring Python harnesses this by providing an out-of-the-box row mapper that
will automatically try matching a query column name to an class attribute name.
This is known as *convention over configuration* because it relieves you of the
need to code the *RowMapper* provided you follow the convention of naming the
attributes of your :abbr:`POPO (Plain Old Python Object)` after query columns.
The only requirement is that class have a default constructor that doesn't
require any arguments::

  results = dt.query("select title, air_date, episode_number, writer from tv_shows where episode_number < %s", \
                     (100,), SimpleRowMapper(TvShow))
  results = dt.query("select title, air_date, episode_number, writer from tv_shows where upper(title) like %s", \
                     ("%CHEESE%",), SimpleRowMapper(TvShow))
  results = dt.query("select title, air_date, episode_number, writer from tv_shows where writer in ('Cleese', 'Graham')",
                     rowhandler=SimpleRowMapper(TvShow))

.. note::

  Convention is based on query, not tables

  Query metadata is based on the column names as defined in the query, NOT what
  is in the table. This is important when you use expressions like COUNT(*).
  These columns should be aliased to fit the attribute name.


Mapping rows into dictionaries
++++++++++++++++++++++++++++++

A convenient alternative to mapping database rows into python objects, it
to map them into dictionaries. Spring Python offers *springpython.database.DictionaryRowMapper*
as an out-of-the-box way to query the database, and return a list of dictionary
entries, based on the column names of the queries. Using this mapper, you don't
have to code a *TvRowMapper* as shown earlier::

  results = dt.query("select title, air_date, episode_number, writer from tv_shows where episode_number < %s", \
                     (100,), DictionaryRowMapper())
  results = dt.query("select title, air_date, episode_number, writer from tv_shows where upper(title) like %s", \
                     ("%CHEESE%",), DictionaryRowMapper())
  results = dt.query("select title, air_date, episode_number, writer from tv_shows where writer in ('Cleese', 'Graham')",
                     rowhandler=DictionaryRowMapper())


.. note::

  Dictionary keys are based on query not original tables

  Query metadata is based on the column names as defined in the query, NOT what
  is in the table. This is important when you use expressions like COUNT(*).
  These columns should be aliased in order to generate a useful key in the
  dictionary.


What is a Connection Factory?
+++++++++++++++++++++++++++++

You may have noticed I didn't make a standard connection in the example above.
That is because to support `Dependency Injection <http://en.wikipedia.org/wiki/Dependency_injection>`_,
I need to setup my credentials in an object before making the actual connection.
*MySQLConnectionFactory* holds credentials specific to the MySQL DB-API, but
contains a common function to actually create the connection. I don't have
to use it myself. *DatabaseTemplate* will use it when necessary to create a
connection, and then proceed to reuse the connection for subsequent database
calls.

That way, I don't manage database connections and cursors directly, but instead
let Spring Python do the heavy lifting for me.

Creating/altering tables, databases, and other DDL
++++++++++++++++++++++++++++++++++++++++++++++++++

Data Definition Language includes the database statements that involve creating
and altering tables, and so forth. DB-API defines an execute function for this.
*DatabaseTemplate* offers the same. Using the execute() function will pass
through your request to a cursor, along with the extra exception handler
and cursor management.

SQL Injection Attacks
+++++++++++++++++++++

You may have noticed in the first three example queries I wrote with the
*DatabaseTemplate*, I embedded a "%s" in the SQL statement. These are called
*binding variables*, and they require a tuple argument be included after the SQL
statement. Do *NOT* include quotes around these variables. The database connection
will handle that. This style of SQL programming is *highly recommended* to avoid
`SQL injection attacks <http://en.wikipedia.org/wiki/SQL_injection>`_.

For users who are familiar with Java database APIs, the binding variables are
cited using "?" instead of "%s". To make both parties happy and help pave the
way for existing Java programmers to use this framework, I have included
support for both. You can mix-and-match these two binding variable types
as you wish, and things will still work.

Have you used Spring Framework's JdbcTemplate?
++++++++++++++++++++++++++++++++++++++++++++++

If you are a user of Java's `Spring framework <http://www.springsource.org/>`_
and have used the `JdbcTemplate <http://static.springsource.org/spring/docs/1.2.x/api/org/springframework/jdbc/core/JdbcTemplate.html>`_,
then you will find this template has a familiar feel.

=================================================================  ================================================================================================
execute(sql_statement, args = None)                                execute any statement, return number of rows affected
insert_and_return_id(sql_statement, args = None)                   insert, return id of new row inserted
query(sql_query, args = None, rowhandler = None                    query, return list converted by rowhandler
query_for_list(sql_query, args = None)                             query, return list of DB-API tuplesTrue
query_for_int(sql_query, args = None)                              query for a single column of a single row, and return an integer (throws exception otherwise)
query_for_long(sql_query, args = None)                             query for a single column of a single row, and return a long (throws exception otherwise)
query_for_object(sql_query, args = None, required_type = None)     query for a single column of a single row, and return the object with possibly no checking
update(sql_statement, args = None)                                 update the database, return number of rows updated
=================================================================  ================================================================================================

*Inserts* have classically been implemented through the **execute()** function, just like in JdbcTemplate. In Spring Python 1.2, we added **insert_and_return_id()**
to give the option of returning the id of the newly created row. It has the same signature as **execute()**. This is very useful when you plan to insert one row in one table, and then insert
several rows in another table that reference the first row created.

Notes on using SQLServerConnectionFactory
+++++++++++++++++++++++++++++++++++++++++

*SQLServerConnectionFactory* uses ODBC for connecting to SQL Server instances
and it expects you to pass the ODBC parameters when creating connection
factories or when injecting factory settings through IoC. The ODBC parameters
you provide are directly translated into an ODBC connection string.

That means that you use the exact ODBC parameters your ODBC provider understands
and not the standard username, password, hostname and db parameters as with
other connection factories.

A simple example will demonstrate this. Here's how you would create
a *DatabaseTemplate* on Windows for running queries against an SQL Server
instance::

  from springpython.database.core import DatabaseTemplate
  from springpython.database.factory import SQLServerConnectionFactory

  driver = "{SQL Server}"
  server = "localhost"
  database = "springpython"
  uid = "springpython"
  pwd = "cdZS*RQRBdc9a"

  factory = SQLServerConnectionFactory(DRIVER=driver, SERVER=server, DATABASE=database, UID=uid, PWD=pwd)
  dt = DatabaseTemplate(factory)

.. note::

  SQLServerConnectionFactory is dictionary driven

  Due to SQLServerConnectionFactory's pass-through nature, it is coded to
  accept a dictionary. For pure python, this means you MUST name the arguments
  and NOT rely on argument position.

.. highlight:: xml

For an XML-based application context, you must populate the argument
odbc_info with a dictionary. See the following example::

  <?xml version="1.0" encoding="UTF-8"?>
  <objects xmlns="http://www.springframework.org/springpython/schema/objects/1.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.springframework.org/springpython/schema/objects/1.1
                 http://springpython.webfactional.com/schema/context/spring-python-context-1.1.xsd">

      <object id="connection_factory" class="springpython.database.factory.SQLServerConnectionFactory">
          <property name="odbc_info">
              <dict>
                  <entry>
                      <key><value>DRIVER</value></key>
                      <value>{SQL Server}</value>
                  </entry>
                  <entry>
                      <key><value>SERVER</value></key>
                      <value>localhost</value>
                  </entry>
                  <entry>
                      <key><value>DATABASE</value></key>
                      <value>springpython</value>
                  </entry>
                  <entry>
                      <key><value>UID</value></key>
                      <value>springpython</value>
                  </entry>
                  <entry>
                      <key><value>PWD</value></key>
                      <value>cdZS*RQRBdc9a</value>
                  </entry>
              </dict>
          </property>
      </object>

  </objects>
