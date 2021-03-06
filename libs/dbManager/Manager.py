import os, sys, pymongo, simplejson, datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from django.http import Http404

class dbManager:
   PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
   all_groups = []

   def __init__(self, db_name):
      self.client = MongoClient("seg-tools.hq.gsslab.rdu.redhat.com")

      self.db = self.client[db_name]



   def __parse_curser_object(self, curser):
      output = {}

      if curser == None or curser == "":
         return

      output['name'] = curser['name']

      if "description" in curser:
         output['description'] = curser['description']

      if "active" in curser:
         output['active'] = curser['active']

      if "expression" in curser:
         output['expression'] = curser['expression']
      else:
         output['expression'] = ""

      if "message_id" in curser:
         output['message_id'] = curser['message_id']
         output['message_type'] = curser['message_type']
      if "group_id" in curser:
         output['group_id'] = curser['group_id']
         output['path'] = curser['path']
         output['isProduct'] = curser['isProduct']

         if "groups" in curser:
            groups = []
            for i in curser['groups']:
               new_group = self.get_group(i['group_id'])
               if new_group != None:
                  groups.append(new_group)

                  if new_group['name'] == "ZStream":
                      print new_group

            if len(groups) > 0:
               output['groups'] = groups
         
         if "messages" in curser:
            messages = []
            for i in curser['messages']:
               new_message = self.get_message(i['message_id'])
               if new_message != None:
                  messages.append(new_message)

            if len(messages) > 0:
               output['messages'] = messages

      if "variable_ids" in curser:
         variables = []

         for i in curser['variable_ids']:
            var_id = ObjectId(i['var_id'])
            var = self.get_variable(var_id)
            if var != None:
               variables.append(var)

         output['variables'] = variables

      if "var_id" in curser:
         output['var_id'] = curser['var_id']
         output['name'] = curser['name']
         output['parent_id'] = curser['parent_id']
         output['values'] = curser['values']
         output['value_count'] = curser['value_count']
         output['type'] = curser['type']

      return output
      
   def remove_group(self, group_id):
      id = ObjectId(group_id)
      group = self.get_group(group_id)

      if "groups" in group:
         for i in group['groups']:
            id = self.db.groups.find({"group_id":i['group_id']}).distinct("group_id")[0]
            self.remove_group(id)

      if "messages" in group:
         for i in group['messages']:
            id = self.db.messages.find({"message_id": i['message_id']}).distinct("message_id")[0]
            self.remove_message(id)
      if "variable_values" in group:
         for i in group['variable_values']:
            self.remove_variable(ObjectId(i['var_id']))
             
      self.db.groups.remove({"group_id":group['group_id']})

   def remove_message(self, message_id):
      id = ObjectId(message_id)
      message = self.get_message(message_id)
      self.db.messages.remove({"message_id":message['message_id']})

   def find_all_products(self):
      groups = self.db.groups.find({"isProduct":True})
      output = []
      
      for group in groups:
         data = self.__parse_curser_object(group)
         if "variables" in data:
            print data['name']

         output.append(data)

      return output

   def get_group(self, group_id):
      id = ObjectId(group_id)
      group = self.db.groups.find_one({"group_id":id})
      
      return self.__parse_curser_object(group)

   def activate_message(self, message_id):
      message = self.get_message(message_id)
      value = ""

      if message['active'] == "False":
         value = "True"
      else:
         value = "False"

      self.db.messages.update({"message_id":ObjectId(message_id)}, { "$set": {"active": value} })

   def get_message(self, message_id):
      id = ObjectId(message_id)
      message = self.db.messages.find_one({"message_id":id})
      
      return self.__parse_curser_object(message)
   
   def activate_group(self, group_id):
      group = self.get_group(group_id)
      value = ""

      if group['active'] == "False":
         value = "True"
      else:
         value = "False"

      self.db.groups.update({"group_id":ObjectId(group_id)}, { "$set": {"active": value }})

   def add_group(self, group_name, description = None, isProduct = None):
      group_id = ObjectId()
      product = False

      if isProduct == True:
         product = True
      
      if description == None:
         description = ""

      group = {
         "group_id": group_id,
         "name": group_name,
         "description": description,
         "active":False,
         "isProduct": product,
         "path": [{ "name": group_name, "group_id": group_id }]
      }

      self.db.groups.insert(group)

   def add_description_to_group(self, id, description):
      self.db.groups.update({"group_id": ObjectId(id)}, {"$set": {"description": description }})

   def add_group_to_group(self, parent_id, group_name, description = None, isProduct = None):
      new_id = ObjectId()
      id = ObjectId(parent_id)
      product = False
      
      if isProduct == True:
         product = True

      if description == None:
         description = ""

      parent = self.get_group(parent_id)
      
      group = {
         "group_id": new_id,
         "name": group_name,
         "parent_group": id,
         "description": description,
         "active":True,
         "isProduct": product,
      }

      path = { 
         "name": group_name, 
         "group_id": new_id, 
      }

      if "path" in parent:
         parent_path = parent['path']
         parent_path.append(path)
         path = parent_path
      
      group['path'] = path

      self.db.groups.insert(group)

      self.db.groups.update({"group_id": id},
         {"$push" : {"groups": { "$each":
                                 [{"group_id":new_id}]
                              }
                     }
         })

   def add_req(self, group, type, expression, message = None):
      if type == "group" or type == "product":
         id = ObjectId(group['group_id'])
         self.db.groups.update({"group_id":id}, {"$set": {"expression":expression}}) 

      if type == "message":
         group_id = ObjectId(group['group_id'])
         message['parent_id'] = group_id
         message['expression'] = expression

         if "message_id" in message:
            new_id = ObjectId(message['message_id'])
            message['active'] = self.get_message(new_id)['active']
            message['message_id'] = new_id
            self.db.messages.update({"message_id":new_id}, message)
         else:
            new_id = ObjectId()
            message['active'] = True
            message['message_id'] = new_id
            self.db.messages.insert(message)

            self.db.groups.update({"group_id": group_id},
               {"$push" : {"messages": { "$each":
                                       [{"message_id":new_id}]
                                    }
                           }
               })

   def add_variable(self, group, var):
      if var != None: 
         var_id = ObjectId(var['var_id'])
         
         first = str(var['values']).find("@")
         last = str(var['values']).rfind("@")

         if first == last:
            value = {
               "value": str(var['values']).replace("@", "\@"),
               "index": 0,
            }

            var['values'] = [value]
         else:
            value = {
               "value": var['values'],
               "index": 0,
            }
            var['values'] = [value]

         var['value_count'] = 1

         self.db.variables.insert(var)
         
         if "variable_ids" not in group or var_id not in group['variable_ids']:
            self.db.groups.update({"group_id":group['group_id']}, 
               {"$push": { "variable_ids": {"$each" : [{'var_id': var_id }]
                                             }
                        }
            })

   def edit_variable(self, var_id, var):
      self.db.variables.update({"var_id":var_id}, {"$set": {
         "name": var['name'], "parent_id": var['parent_id'], "values": var['values'], 
         "description": var['description']}})

   def edit_element_in_variable(self, var_id, value, index):
      var = self.get_variable(var_id)

      if var != None:
         for i in var['values']:
            if str(i['index']) == index:
               self.remove_element_from_variable(var_id, i['value'], index) 
               self.add_element_to_variable(var_id, value)


   def add_element_to_variable(self, var_id, value):
      var_id = ObjectId(var_id)

      var = self.get_variable(var_id)

      value = {
         "value": value,
         "index": var['value_count'],
      }

      if var != None:
         count = var['value_count'] + 1
         self.db.variables.update({"var_id":var_id}, 
            {"$push": { "values": value}, 
            "$set" : { "value_count": count}}, multi=True)
        
   def remove_element_from_variable(self, var_id, value, index):
      var_id = ObjectId(var_id)

      var = self.get_variable(var_id)

      value = {
         "value": value,
         "index": int(index),
      }

      if var != None:
         count = var['value_count'] - 1
         if count < 0:
            count = 0

         self.db.variables.update({"var_id":var_id}, {"$pull": { "values": value }, 
            "$set": {"value_count": count }}, multi=True)
 
   def get_variable(self, var_id):
      id = ObjectId(var_id)
      data = self.db.variables.find_one({"var_id":id})
      return self.__parse_curser_object(data)


   def remove_variable(self, id):
      new_id = ObjectId(id)
      var = self.get_variable(new_id)
      if var != None:
         parent_id = var['parent_id']
         self.db.groups.update({"group_id":parent_id}, { "$pull": { "variable_ids" : var } })
         self.db.variables.remove({"var_id": var['var_id']})

