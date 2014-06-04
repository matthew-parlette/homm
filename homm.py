#!/usr/bin/python

import argparse
import logging
import os
from uuid import uuid4

class Customer(object):
  def __init__(self,name,id = uuid4()):
    self.id = id
    self.name = name

class Project(object):
  def __init__(self,name,id = uuid4(),customer_id = None):
    self.id = id
    self.name = name
    self.customer_id = customer_id

if __name__ == "__main__":
  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('-d','--debug', action='store_true', help='Enable debug logging')
  parser.add_argument('-t','--test', action='store_true', help='Run functionality test')
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

  if args.test:
    log.info("__main__:Running functionality tests")
    log.info("__main__:Creating customer 'test'")
    customer = Customer("test")
    log.info("__main__:Customer '%s' has id '%s'" % (customer.name,customer.id))
    log.info("__main__:Creating project 'test project'")
    project = Project("test project",customer_id = customer.id)
    log.info("__main__:Project '%s' has id '%s'" % (project.name,project.id))
