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

  def create(self):
    """Returns a dictionary with sql and parameters:
    {'insert into table values (?,?)': (self.param1,self.param2,)}
    """
    raise NotImplementedError

class Customer(Entity):
  def __init__(self,name,id = uuid4()):
    self.id = id
    self.name = name

  def __repr__(self):
    return "%s" % (str(self.name))

  def create(self):
    """Return the sql required to create this object"""
    return {"insert into customers values (?,?)":
      (str(self.id),str(self.name),)}

class Project(Entity):
  def __init__(self,name,id = uuid4(),customer_id = None):
    self.id = id
    self.name = name
    self.customer_id = customer_id

  def __repr__(self):
    return "%s" % (str(self.name))

  def create(self):
    """Return the sql required to create this object"""
    return {"insert into projects (id,name,customer_id) values (?,?,?)":
      (str(self.id),str(self.name),str(self.customer_id),)}

class Manager(object):
  def __init__(self, database):
    self.database = database
    self.refresh()

  def pre(self):
    """Executed before any manager command"""
    self.refresh()

  def refresh(self):
    # Make sure we can access the columns by name
    self.database.row_factory = sqlite3.Row

    # Initialize the lists
    self.customers = {}
    self.projects = {}

    # Build the customers list
    cursor = self.database.execute("select * from customers")
    for row in cursor:
      self.customers[row['id']] = Customer(name = row['name'], id = row['id'])

    # Build the projects list
    cursor = self.database.execute("select * from projects")
    for row in cursor:
      self.projects[row['id']] = Project(name = row['name'],
                                         id = row['id'],
                                         customer_id = row['customer_id'])

    return True

  def create(self,obj):
    self.pre()
    try:
      with self.database:
        for sql,parameters in obj.create().iteritems():
          self.database.execute(sql, parameters)
      self.refresh()
      return True
    except sqlite3.IntegrityError:
      print "%s already exists" % obj.id
      return False

  def get(self,type,id = ""):
    self.pre()
    if type == "customer":
      return self.customers[id] if id in self.customers else None
    if type == "project":
      return self.projects[id] if id in self.projects else None

  def list(self,type,filter = None):
    self.pre()
    if "customer" in type:
      if filter:
        customers = {}
        for id,customer in self.customers.iteritems():
          for key,value in filter.iteritems():
            if getattr(customer,key) == value:
              customers[id] = customer
        return customers
      else:
        return self.customers
    if "project" in type:
      if filter:
        projects = {}
        for id,project in self.projects.iteritems():
          for key,value in filter.iteritems():
            if getattr(project,key) == value:
              projects[id] = project
        return projects
      else:
        return self.projects
    return None

  def project_list(self,customer = None):
    raise DeprecationWarning
    # Make sure we can access the columns by name
    self.database.row_factory = sqlite3.Row

    # Initialize the projects list
    projects = {}

    # Build the projects list
    if customer:
      cursor = self.database.execute("select * from projects where customer_id = ?", (customer.id,))
      for row in cursor:
        projects[row['id']] = row['name']

    return projects

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
  if schema_version < 1 and not (args.migrate or args.test):
    error_message = "Database is v%s, current is %s, run with -m" % (schema_version,str(1))
    log.critical(error_message)
    print error_message
    sys.exit(2)

  if args.migrate or args.test:
    # Schema v1
    if schema_version < 1:
      with db:
        log.info("__main__:Migrating to schema version 1")
        db.execute("CREATE TABLE customers (id text, name text)")
        db.execute("CREATE TABLE projects (id text, name text, customer_id text)")
        db.execute("PRAGMA user_version = 1")
    tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
    tables = map(lambda t: t[0], db.execute(tableListQuery).fetchall())
    log.info("__main__:Tables in database are\n%s" % tables)

  manager = Manager(db)

  if args.test:
    log.info("__main__:Running functionality tests")
    log.info("__main__:Creating customer 'test'")
    manager.create(Customer("test"))
    log.info("__main__:Customer list %s" % str(manager.customers))
    customer = manager.get("customer",manager.customers.keys()[0])

    log.info("__main__:Creating project 'test project'")
    manager.create(Project("test project",customer_id = customer.id))
    log.info("__main__:Customer '%s' project list is %s" %
      (customer.name,manager.list("project",{"customer_id":customer.id})))

    log.info("__main__:Total project list is %s" % manager.projects)
    log.info("__main__:Deleting data/test.db")
    os.remove('data/test.db')

  db.close()
