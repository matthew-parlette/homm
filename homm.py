#!/usr/bin/python

import argparse
import logging
import os
import sys
import sqlite3
from uuid import uuid4

class Entity(object):
  def __init__(self):
    raise NotImplementedError

  def migrate(self):
    pass

class Customer(object):
  def __init__(self,name,id = uuid4()):
    self.id = id
    self.name = name

  def __repr__(self):
    return "%s (%s)" % (str(self.name),str(self.id))

class Project(object):
  def __init__(self,name,id = uuid4(),customer_id = None):
    self.id = id
    self.name = name
    self.customer_id = customer_id

class Manager(object):
  def __init__(self, database):
    self.database = database
    self.refresh_customers()

  def refresh_customers(self):
    # Make sure we can access the columns by name
    self.database.row_factory = sqlite3.Row

    # Initialize the customers list
    self.customers = []

    # Build the customers list
    cust_cursor = self.database.execute("select * from customers")
    for row in cust_cursor:
      self.customers.append(Customer(name = row['name'], id = row['id']))

  def create_customer(self,customer):
    try:
      with self.database:
        self.database.execute("insert into customers(id,name) values (?,?)", (str(customer.id),str(customer.name),))
      return True
    except sqlite3.IntegrityError:
      print "Customer %s already exists" % customer.name
      return False

  def list_customers(self):
    customers = []
    cust_cursor = database.execute("select * from customers")
    for row in cust_cursor:
      customers[row['name']] = row['id']
    return customers

if __name__ == "__main__":
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
  parser.add_argument('-t','--test', action='store_true', help='Run functionality test')
  parser.add_argument('--database', default='data/production.db', help='Specify a database file to use')
  parser.add_argument('--migrate', action='store_true', help='Update database schema')
  parser.add_argument('--version', action='version', version='0')
  args = parser.parse_args()

  # Setup logging options
  log_level = logging.DEBUG if args.debug else logging.INFO
  log = logging.getLogger(os.path.basename(__file__))
  log.setLevel(log_level)
  formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')

  ## Console Logging
  if args.test:
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    log.addHandler(ch)

  ## File Logging
  fh = logging.FileHandler(os.path.basename(__file__) + '.log')
  fh.setLevel(log_level)
  fh.setFormatter(formatter)
  log.addHandler(fh)

  log.info("__main__:Initializing")

  if not os.path.exists("data"):
    os.makedirs("data")

  database_name = 'data/test.db' if args.test else args.database

  log.info("__main__:Opening database %s" % database_name)
  try:
    db = sqlite3.connect(database_name)
    # db = conn.cursor()
    log.info("__main__:%s opened" % database_name)
  except:
    log.critical("__main__:Error opening %s" % database_name)
    sys.exit(1)

  schema_version = db.execute("PRAGMA user_version").fetchone()[0]
  log.debug("__main__:Schema version is %s" % schema_version)
  if schema_version < 1 and not args.migrate:
    error_message = "Database is v%s, current is %s, run with -m" % (schema_version,str(1))
    log.critical(error_message)
    print error_message
    sys.exit(2)

  if args.migrate:
    # Schema v1
    if schema_version < 1:
      with db:
        log.info("__main__:Migrating to schema version 1")
        db.execute("CREATE TABLE customers (id text, name text)")
        db.execute("PRAGMA user_version = 1")
    tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
    tables = map(lambda t: t[0], db.execute(tableListQuery).fetchall())
    log.info("__main__:Tables in database are\n%s" % tables)

  manager = Manager(db)

  if args.test:
    log.info("__main__:Running functionality tests")
    log.info("__main__:Creating customer 'test'")
    manager.create_customer(Customer("test"))
    # log.info("__main__:Customer '%s' has id '%s'" % (customer.name,customer.id))
    log.info("__main__:Customer list %s" % str(manager.customers))
    # log.info("__main__:Creating project 'test project'")
    # project = Project("test project",customer_id = customer.id)
    # log.info("__main__:Project '%s' has id '%s'" % (project.name,project.id))

  db.close()
