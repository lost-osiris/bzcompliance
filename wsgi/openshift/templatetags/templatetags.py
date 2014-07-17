from django.template import loader, Context, Library, Node
from django import template
from pymongo import MongoClient
from bson.objectid import ObjectId
import simplejson

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





@register.filter('to_string')
def to_string(obj):
   output = str(obj).replace("\n", '<br>')
   return  str(output)      






@register.filter('json')
def json(obj):
   obj = json_compatible(obj)
   return  simplejson.dumps(obj, indent = 2)      

def json_compatible(data):
   if type(data) is dict:
      for i in data:
         data[i] = json_compatible(data[i])
      return data
   elif type(data) is list:
      for idx, val in enumerate(data):
         data[idx] = json_compatible(val)
      return data
   elif type(data) is str:
      return data.replace("'", "''")
   elif type(data) is unicode:
      return data
   else:
      return str(data)






class Nav(Node):
   def __init__(self, type, curser):
      self.type = template.Variable(type)
      self.data = template.Variable(curser)

   def render(self, context):
      type = self.type.resolve(context)
      data = self.data.resolve(context)
      return self.__build_tabs(type, data, context)
   
   def __build_tabs(self, type, data, context):
      if type == "groups":
         t = loader.get_template("bz/tabs/groups.html")
         context["group"] = data
         return t.render(context)

      if type == "messages":
         t = loader.get_template("bz/tabs/messages.html")
         context["message"] = data
         return t.render(context)

      if type == "details":
         t = loader.get_template("bz/tabs/details.html")
         context["details"] = data
         return t.render(context)

      if type == "tools":
         t = loader.get_template("bz/tabs/tools.html")
         context["tools"] = data
         return t.render(context)

def build_nav(parser, token):
   bits = token.contents.split()
   return Nav(bits[1], bits[2])   
register.tag(build_nav)





class LoadNav(Node):
   def __init__(self, type, curser, name):
      self.type = template.Variable(type)
      self.data = template.Variable(curser)
      self.name = name

   def render(self, context):
      type = self.type.resolve(context)
      data = self.data.resolve(context)
      name = self.name

      self.__load_tabs(type, data, name, context)
      return ""
 
   def __load_tabs(self, type, data, name, context):
      if name in context:
         context[name].append(type)
      else:
         context[name] = []
         context[name].append(type)

def load_nav(parser, token):
   bits = token.contents.split()
   return LoadNav(bits[1], bits[2], bits[4])  
     
register.tag(load_nav)
