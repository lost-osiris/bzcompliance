from django.template import loader, Context, Library, Node
from django.utils.safestring import mark_safe
from django import template
from pymongo import MongoClient
from bson.objectid import ObjectId
import simplejson
from dbManager import Manager

manager = Manager.dbManager("dev-test")

data = []
register = Library()

class RequirementType(Node):
   def __init__(self, type, var):
      self.type = template.Variable(type)
      self.var = template.Variable(var)

   def render(self, context):
      t = loader.get_template("add_req/modal.html")

      name = self.var.resolve(context)
      context[name] = self.type.resolve(context)   

      return t.render(context)
   
def get_requirement_type(parser, token):
   bits = token.contents.split()
   return RequirementType(bits[1], bits[3])
register.tag(get_requirement_type)






class FindGroups(Node):
   def __init__(self, data, var, include_current = None):
      self.data = template.Variable(data)
      self.var = var
      self.groups = []
      self.current = include_current

   def render(self, context):
      name = self.var
      data = self.data.resolve(context)   
      self.__find_groups(data, self.current)
      data = self.groups
      context[name] = data
      
      return ""

   def __find_groups(self, data, include_current = None):
      if include_current == None:
         if type(data) == list:
            all_data = data
            for data in all_data:
               if "groups" in data:
                  for i in data['groups']:
                     new_group = { 
                        "group_id": str(i['group_id']),
                        "name": i['name']
                     }   
                     if new_group not in self.groups :
                        self.groups.append(new_group)
                        self.__find_groups(i)
               else:
                  new_group = { 
                     "group_id": str(data['group_id']),
                     "name": data['name']
                  }   
                  if new_group not in self.groups :
                     self.groups.append(new_group)
         else:
            if "groups" in data:
               for i in data['groups']:
                  new_group = { 
                     "group_id": str(i['group_id']),
                     "name": i['name']
                  }   
                  if new_group not in self.groups :
                     self.groups.append(new_group)
                     self.__find_groups(i)
            else:
               new_group = { 
                  "group_id": str(data['group_id']),
                  "name": data['name']
               }   
               if new_group not in self.groups :
                  self.groups.append(new_group)

      else:
         if type(data) == list:
            all_data = data
            for data in all_data:
               new_group = { 
                  "group_id": str(data['group_id']),
                  "name": data['name']
               }   

               self.groups.append(new_group)

               if "groups" in data:
                  for i in data['groups']:
                     new_group = { 
                        "group_id": str(i['group_id']),
                        "name": i['name']
                     }   
                     if new_group not in self.groups :
                        self.groups.append(new_group)
                        self.__find_groups(i)
               else:
                  new_group = { 
                     "group_id": str(data['group_id']),
                     "name": data['name']
                  }   
                  if new_group not in self.groups :
                     self.groups.append(new_group)
         else:
            new_group = { 
               "group_id": data['group_id'],
               "name": data['name']
            }   

            self.groups.append(new_group)

            if "groups" in data:
               for i in data['groups']:
                  new_group = { 
                     "group_id": str(i['group_id']),
                     "name": i['name']
                  }   
                  if new_group not in self.groups :
                     self.groups.append(new_group)
                     self.__find_groups(i)
            else:
               new_group = { 
                  "group_id": str(data['group_id']),
                  "name": data['name']
               }   
               if new_group not in self.groups :
                  self.groups.append(new_group)

def find_groups(parser, token):
   bits = token.contents.split()
   if len(bits) > 4:
      return FindGroups(bits[1], bits[3], bits[4])
   else:   
      return FindGroups(bits[1], bits[3])
register.tag(find_groups)





@register.filter('safe')
def safe(obj):
   output = mark_safe(obj)
   return output      





@register.filter('split')
def split(obj):
   output = mark_safe(obj.split("/"))
   return output      





@register.filter('replace')
def replace(obj):
   output = mark_safe(obj.replace(" ", "-"))
   return output      





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
   elif type(data) is int:
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
         t = loader.get_template("tabs/groups.html")
         context["group"] = data
         return t.render(context)

      if type == "messages":
         t = loader.get_template("tabs/messages.html")
         context["message"] = data
         return t.render(context)

      if type == "group-content":
         t = loader.get_template("tabs/details.html")
         context["details"] = data
         return t.render(context)

      if type == "configure":
         t = loader.get_template("tabs/configure.html")
         context["configure"] = data
         return t.render(context)

      if type == "edit-variables":
         t = loader.get_template("tabs/edit-variables.html")
         context["variables"] = data
         return t.render(context)

      if type == "raw-data":
         t = loader.get_template("tabs/raw-data.html")
         context["raw_data"] = data
         return t.render(context)

      if type == "add-group-view":
         t = loader.get_template("tabs/add-group.html")
         context["add_group"] = data
         return t.render(context)

      if type == "remove-group-view":
         t = loader.get_template("tabs/remove-group.html")
         context["remove_group"] = data
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





class SetContext(Node):
   def __init__(self, data, var):
      self.var = var
      self.data = template.Variable(data)

   def render(self, context):
      data = self.data.resolve(context)
      context[self.var] = data
      return ""

def set_context(parser, token):
   bits = token.contents.split()
   return SetContext(bits[1], bits[3])  
     
register.tag(set_context)





class AppendContext(Node):
   def __init__(self, data, var):
      self.var = var
      self.data = template.Variable(data)

   def render(self, context):
      data = self.data.resolve(context)
      key = self.var
      new_list = []
      new_list.append(context[key])
      new_list.append(data)
      context[key] = new_list
      return ""

def append_context(parser, token):
   bits = token.contents.split()
   return AppendContext(bits[1], bits[3])  
     
register.tag(append_context)





class AddVariableValue(Node):
   def __init__(self, var_id, value):
      self.id = template.Variable(var_id)
      self.value = value

   def render(self, context):
      id = ObjectId(self.id.resolve(context))
      var_value = self.value

      var = manager.get_variable(id)
      var['values'].append(var_value)
      manager.add_variable(manager.get_group(var['parent_id']), var)
      return True

def edit_variable(parser, token):
   bits = token.contents.split()
   return AddVariableValue(bits[1], bits[2])

register.tag(edit_variable)







class Results(Node):
   def __init__(self, bugdata):
      self.data = template.Variable(bugdata)

   def render(self, context):
      data = self.data.resolve(context)
      return self.__build_panel(data, context)
   
   def __build_panel(self, bugdata, context):
      if bugdata['is_passed'] and len(bugdata['messages']) == 0:
         t = loader.get_template("results/panel/main.html")
         context['content'] = bugdata
         context['panel_type'] = "passed"
         return t.render(context)

      elif bugdata['is_passed'] and len(bugdata['messages']) > 0:
         t = loader.get_template("results/panel/main.html")
         context['content'] = bugdata
         context['panel_type'] = "failed"
         return t.render(context)

      else:
         t = loader.get_template("results/panel/main.html")
         context['content'] = bugdata
         context['panel_type'] = "ignored"

         return t.render(context)
         
def build_results_panel(parser, token):
   bits = token.contents.split()
   return Results(bits[1])   
register.tag(build_results_panel)


