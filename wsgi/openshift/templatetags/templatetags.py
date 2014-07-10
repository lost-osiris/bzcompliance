from django.template import loader, Context, Library, Node
from django import template
from pymongo import MongoClient
from bson.objectid import ObjectId

data = []
register = Library()

client = MongoClient("osiris.usersys.redhat.com")
db = client['test']
class RequirementType(Node):
   def __init__(self, type, var):
      self.type = template.Variable(type)
      self.var = template.Variable(var)

   def render(self, context):
      t = loader.get_template("bz/add_req/modal.html")

      name = self.var.resolve(context)
      context[name] = self.type.resolve(context)   

      return t.render(context)
   
def get_requirement_type(parser, token):
   bits = token.contents.split()

   return RequirementType(bits[1], bits[3])

register.tag(get_requirement_type)








class Products(Node):
   def __init__(self, name, var):
      self.name = template.Variable(name)
      self.var = var

   def render(self, context):

      context[self.var] = find_product_info(self.name.resolve(context))

      return ''

def find_product_info(name):
   if name == "classification":
      return db.product_info.find().distinct(name)
   else:
      return db.product_info.find({"classification":name}).distinct("name")

def get_product_info(parser, token):
   bits = token.contents.split()

   return Products(bits[1], bits[2])

get_product_info = register.tag(get_product_info)
