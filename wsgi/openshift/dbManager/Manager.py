import os, sys, pymongo, simplejson, datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from django.http import Http404

class dbManager:
   PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
   ON_OPENSHIFT = False
   all_groups = []

   def __init__(self, db_name):
      if os.environ.has_key('OPENSHIFT_REPO_DIR'):
            self.ON_OPENSHIFT = True
      if self.ON_OPENSHIFT:
         try:
            self.client = MongoClient(os.environ.get('OPENSHIFT_MONGODB_DB_URL'))
         except:
            raise Http404

      else:
         self.client = MongoClient("osiris.usersys.redhat.com")

      self.db = self.client[db_name]



   def __parse_curser_object(self, curser):
      output = {}

      output['name'] = curser['name']
      output['description'] = curser['description']
      output['active'] = curser['active']

      if "expression" in curser:
         output['expression'] = curser['expression']
      else:
         output['expression'] = ""

      if "message_id" in curser:
         output['message_id'] = curser['message_id']
         output['message_type'] = curser['message_type']
      else:
         output['group_id'] = curser['group_id']
         output['path'] = curser['path']
         output['isProduct'] = curser['isProduct']

         if "groups" in curser:
            groups = []
            for i in curser['groups']:
               groups.append(self.__parse_curser_object(self.get_group(i['group_id'])))
            output['groups'] = groups
         else:
            output['groups'] = ""

         if "messages" in curser:
            messages = []
            for i in curser['messages']:
               messages.append(self.__parse_curser_object(self.get_message(i['message_id'])))
            output['messages'] = messages
         else:
            output['messages'] = ""

      return output
      
   def remove_group(self, group_id):
      id = ObjectId(group_id)
      group = self.db.groups.find_one({"group_id":id})
      
      for key,value in group.items():
         if key == "req":
            self.remove_req(value['req_id'])
         if key == "groups":
            for i in group[key]:
               id = self.db.groups.find({"group_id":i['group_id']}).distinct("group_id")[0]
               self.remove_group(id)
         if key == "messages":
            for i in group[key]:
               id = self.db.messages.find({"_id": i['_id']}).distinct("_id")[0]
               self.remove_message(id)

      self.db.remove({"group_id":id})

   def remove_message(self, message_id):
      id = ObjectId(message_id)
      message = self.db.messages.find_one({"_id":id})
      self.db.messages.remove({"_id":id})

   def find_all_products(self):
      groups = self.db.groups.find({"isProduct":True})
      output = []

      for group in groups:
         output.append(self.__parse_curser_object(group))

      return output

   def get_group(self, group_id):
      id = ObjectId(group_id)
      group = self.db.groups.find_one({"group_id":id})
      
      return self.__parse_curser_object(group)

   def get_message(self, message_id):
      id = ObjectId(message_id)
      message = self.db.messages.find_one({"message_id":id})
      
      return self.__parse_curser_object(message)

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
         "path": str(group_name + "/"),
      }

      self.db.groups.insert(group)

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
         "active":False,
         "isProduct": product,
         "path": str(parent['path'] + group_name + "/")
      }

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
         new_id = ObjectId()
         group_id = ObjectId(group['group_id'])
         message['message_id'] = new_id
         message['parent_id'] = group_id
         message['expression'] = expression
         message['active'] = False

         self.db.messages.insert(message)
         
         self.db.groups.update({"group_id": group_id},
            {"$push" : {"messages": { "$each":
                                    [{"message_id":new_id}]
                                 }
                        }
            })
 
