#!/usr/bin/python

import argparse
import logging
import os
import sys
import sqlite3
import menu
from getch import _Getch as getch
from uuid import uuid4

class Entity(object):
  def __init__(self,name,id = uuid4(),parameters = None):
    self.id = id
    self.name = name
    self.post_init(parameters)

  def post_init(self,parameters):
    """This should be overriden to perform any class-specific
    init actions on the parameters."""
    if parameters and type(parameters) is dict:
      for key,value in parameters.iteritems():
        setattr(self,key,value)

  def __repr__(self):
    return "%s" % (str(self.name))

  def create(self):
    """Returns a dictionary with sql and parameters:
    {'insert into table values (?,?)': (self.param1,self.param2,)}
    """
    raise NotImplementedError

class Customer(Entity):
  def create(self):
    """Return the sql required to create this object"""
    return {"insert into customers values (?,?)":
      (str(self.id),str(self.name),)}

class Project(Entity):
  def create(self):
    """Return the sql required to create this object"""
    return {"insert into projects (id,name,parent_id) values (?,?,?)":
      (str(self.id),str(self.name),str(self.parent_id),)}

class Task(Entity):
  def create(self):
    """Return the sql required to create this object"""
    return {"insert into tasks (id,name,parent_id) values (?,?,?)":
      (str(self.id),str(self.name),str(self.parent_id),)}

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
    self.tasks = {}

    # Build the customers list
    cursor = self.database.execute("select * from customers")
    for row in cursor:
      self.customers[row['id']] = Customer(name = row['name'], id = row['id'])

    # Build the projects list
    cursor = self.database.execute("select * from projects")
    for row in cursor:
      self.projects[row['id']] = Project(name = row['name'],
                                         id = row['id'],
                                         parameters =
                                           {"parent_id": row['parent_id']}
                                        )

    # Build the tasks list
    cursor = self.database.execute("select * from tasks")
    for row in cursor:
      self.tasks[row['id']] = Task(name = row['name'],
                                         id = row['id'],
                                         parameters =
                                           {"parent_id": row['parent_id']}
                                        )

    return True

  def create(self,obj):
    # self.pre()
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
    """Return a list of the type specified.

    A filter is applied if provided.
    Filter is of the form:
      {"name": "value for name"}
    """
    self.pre()
    if "customer" in type:
      if filter:
        customers = []
        for id,customer in self.customers.iteritems():
          for key,value in filter.iteritems():
            if getattr(customer,key) == value:
              customers.append(customer)
        return customers
      else:
        return self.customers.values()
    if "project" in type:
      if filter:
        projects = []
        for id,project in self.projects.iteritems():
          for key,value in filter.iteritems():
            if getattr(project,key) == value:
              projects.append(project)
        return projects
      else:
        return self.projects.values()
    return []

if __name__ == "__main__":
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
  parser.add_argument('-t','--test', action='store_true', help='Run functionality test')
  parser.add_argument('--database', default='data/production.db', help='Specify a database file to use')
  parser.add_argument('-m','--migrate', action='store_true', help='Update database schema')
  parser.add_argument('--version', action='version', version='0')
  args = parser.parse_args()

  # Setup logging options
  log_level = logging.DEBUG if args.debug else logging.INFO
  log = logging.getLogger(os.path.basename(__file__))
  log.setLevel(log_level)
  formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')

  ## Console Logging
  if args.test or args.debug:
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

  log.debug("__main__:Opening database %s" % database_name)
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
    print "ERROR: %s" % error_message
    sys.exit(2)

  if args.migrate or args.test:
    # Schema v1
    if schema_version < 1:
      with db:
        log.info("__main__:Migrating to schema version 1")
        db.execute("CREATE TABLE customers (id text, name text)")
        db.execute("CREATE TABLE projects (id text, name text, parent_id text)")
        db.execute("CREATE TABLE tasks (id text, name text, parent_id text)")
        db.execute("PRAGMA user_version = 1")
    tableListQuery = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name"
    tables = map(lambda t: t[0], db.execute(tableListQuery).fetchall())
    log.debug("__main__:Tables in database are\n%s" % tables)
    assert len(tables) == 3
    assert db.execute("PRAGMA user_version").fetchone()[0] >= 1
    log.debug("__main__:Database schema v1 appears to be correct")

  manager = Manager(db)

  if args.test:
    log.info("__main__:Running functionality tests")
    try:
      # Customer
      log.info("__main__:Testing Customer")
      log.debug("__main__:Creating customer 'test'")
      manager.create(Customer("test"))
      log.debug("__main__:Customer list %s" % str(manager.customers))
      assert len(manager.customers) == 1
      customer = manager.get("customer",manager.customers.keys()[0])

      # Project
      log.info("__main__:Testing Project")
      log.debug("__main__:Creating project 'test project'")
      manager.create(Project("test project",parameters = {"parent_id": customer.id}))
      test_customer_project_list = manager.list("project",{"parent_id":customer.id})
      assert len(test_customer_project_list) == 1
      log.debug("__main__:Customer '%s' project list is %s" %
        (customer.name,test_customer_project_list))
      log.debug("__main__:Total project list is %s" % manager.projects)
      assert len(manager.projects) == 1
      project = manager.get("project",manager.projects.keys()[0])

      # Task
      log.info("__main__:Testing Task")
      log.debug("__main__:Creating task 'task 1'")
      manager.create(Task("task 1",parameters = {"parent_id": project.id}))
      test_project_task_list = manager.list("project",{"parent_id":project.id})
      assert len(test_project_task_list) == 1
      log.debug("__main__:Project '%s' task list is %s" %
        (project.name,test_project_task_list))
      log.debug("__main__:Total task list is %s" % manager.tasks)
      assert len(manager.tasks) == 1
    except AssertionError, e:
      log.critical("__main__:Test failed\n%s" % str(e))

    log.debug("__main__:Deleting data/test.db")
    os.remove('data/test.db')

  # Main Menu
  menu.MainMenu(manager).draw()

  # for menu in ['customers','projects','tasks']:
  #   # Print menu
  #   print "%s\n%s" % (menu,"=" * len(menu))
  #   print "\n".join(manager.list(menu))

  db.close()
