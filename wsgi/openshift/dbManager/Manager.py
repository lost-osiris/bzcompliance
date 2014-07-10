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

      if "req" in curser:
         output['req'] = curser['req']

      if "product_name" in curser:
         output['product_name'] = curser['product_name']
         output['id'] = curser['_id']

         if "groups" in curser:
            output['groups'] = curser['groups']
            output['all_groups'] = []
            for i in output['groups']:
               new = {}
               new['group'] = i
               new['found_groups'] =  self.__find_all_groups(i)
               self.all_groups = []
               output['all_groups'].append(new)
               
      if "group_name" in curser:
         output['group_name'] = curser['group_name']
         output['group_id'] = curser['group_id']
 
         if "groups" in curser:
            output['groups'] = curser['groups']

      return output
      
   
   #all product functions
   def get_product(self, product_name):
      product = self.db.products.find_one({"product_name": product_name})
      return self.__parse_curser_object(product)

   def add_product(self, product_name):
      if self.db.products.find_one({"product_name":product_name}) == None:
         self.db.products.insert({"product_name": product_name})
         return True
      return False
   
   def remove_product(self, product_name):
      self.db.products.remove({"product_name": product_name})

   def find_all_products(self):
      products = self.db.products.find()
      output = []

      for product in products:
         output.append(self.__parse_curser_object(product))

      return output

   def __find_all_groups(self, group):
      id = ObjectId(group['group_id'])
      new_group = self.db.groups.find_one({"group_id":id})

      if "groups" in new_group:
         for j in new_group['groups']:
            self.all_groups.append(j)
            self.__find_all_groups(j)

      output = self.all_groups
      return output

   def get_group(self, group_id):
      id = ObjectId(group_id)
      group = self.db.groups.find_one({"group_id":id})
      
      return self.__parse_curser_object(group)

   def add_group_to_product(self, group_name, product_name):
      group_id = ObjectId()
      self.db.groups.insert({"group_id":group_id, "group_name":group_name})

      self.db.products.update({"product_name": product_name},
         {"$push" : {"groups": { "$each":
                                 [{"group_id": group_id, "group_name":group_name}]
                               }   
                    }   
         }) 

   def add_group_to_group(self, parent_id, group_name):
      new_id = ObjectId()
      id = ObjectId(parent_id)
      self.db.groups.insert({"group_id": new_id, "parent_group":id, "group_name": group_name})

      self.db.groups.update({"group_id": id},
         {"$push" : {"groups": { "$each":
                                 [{"group_id": new_id, "parent_group": id, "group_name":group_name}]
                              }
                     }
         })

   def add_req(self, req_name, group, type, expression):
      if type == "group":
         new_id = ObjectId()
         group = self.get_group(group)
         id = ObjectId(group['id'])

         req = {
            "req_name": req_name,
            "parent_id": id,
            "req_id": new_id,
            "expression": expression,
         }

         self.db.groups.update({"group_id":id}, {"$set": {"req":req}}) 

      if type == "product":
         new_id = ObjectId()
         product = self.get_product(group)
         id = ObjectId(product['id'])
         
         req = {
            "req_name": req_name,
            "parent_id": id,
            "req_id": new_id,
            "expression": expression,
         }

         self.db.products.update({"product_name":group}, {"$set": {"req":req}}) 

      if self.db.reqs.find_one({"req_name":req_name}) == None:
         self.db.reqs.insert(req)
      else:
         self.db.reqs.update({"req_name":req_name}, req)

