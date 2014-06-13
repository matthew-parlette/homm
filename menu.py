import homm
from getch import _Getch as getch

class MainMenu(object):
  def __init__(self,manager):
    self.name = "Main Menu"
    self.manager = manager

  def draw(self):
    quit = False
    while not quit:
      print "%s\n%s" % (self.name,"=" * len(self.name))
      print "(c)ustomers"
      print "(p)rojects"
      print "(t)asks"
      print "(q)uit"
      print ""
      selection = getch()().lower()
      if selection == "q": quit = True
      if selection == "c": CustomersMenu(self.manager).draw()

class CustomersMenu(object):
  def __init__(self,manager):
    self.name = "Customers"
    self.manager = manager

  def draw(self):
    quit = False
    while not quit:
      customers = self.manager.list("customer")
      print "%s\n%s" % (self.name,"=" * len(self.name))
      for i,c in enumerate(customers):
        print "(%s) %s" % (i,c.name)
      print "(a)dd"
      print "(q)uit"
      print ""
      selection = getch()().lower()
      if selection == "a":
        print "%s\n%s" % ("New Customer","=" * len("New Customer"))
        name = raw_input("Name: ")
        self.manager.create(homm.Customer(name))
      if selection == "q": quit = True
      try:
        if int(selection) < len(customers): print "selected %s" % customers[int(selection)].name
      except ValueError:
        pass

class Item:
  def __init__(self, name, function, parent=None):
    self.name = name
    self.function = function
    self.parent = parent
    if parent:
        parent.add_item(self)

  def draw(self):
    print("    " + self.name)

class ItemEntity(object):
  def __init__(self, entity, parent = None):
    self.entity = entity
    self.name = entity.name
    self.parent = parent
    if parent:
      parent.add(self)

  def draw(self):
    print "    %s" % (self.entity)

class Menu(object):
  def __init__(self,name,items = None):
    self.name = name
    self.items = items or {}

  def add(self, item):
    self.items.append(item)
    if item.parent != self:
      item.parent = self

  def remove(self, item):
    self.items.remove(item)
    if item.parent == self:
      item.parent = None

  def draw(self):
    # while True:
    print "%s\n%s" % (self.name,"=" * len(self.name))
    for item in self.items:
      item.draw()

    print "\n"
    print "%s > " % (','.join(str(item) for item in self.items.keys()))
    selection = getch._Getch()()
    if self.verify(selection): return self.items[selection]

  def verify(self,pick):
    return True if pick in self.items.keys() else False
