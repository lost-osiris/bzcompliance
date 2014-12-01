import os, sys, simplejson
from pymongo import MongoClient

import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

class Utils:
   PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
   ON_OPENSHIFT = False

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
      self.user = {  
         "login" : "mowens@redhat.com",
         "password" : "owenstest",
      }
      
      self.proxy = xmlrpclib.ServerProxy("https://bugzilla.redhat.com/xmlrpc.cgi",
         transport=None, encoding=None)
      
      self.token = self.proxy.User.login(self.user)
      
   def get_token(self):
      return self.token
   
   def get_products(self):
      data = self.proxy.Product.get_selectable_products()
   
      output = []
      for product in data['ids']:
         output.append(self.proxy.Product.get({"ids":product}))
      return output

if __name__ == "__main__":
   utils = Utils("test")
   data = utils.get_products()
   for index in data: 
      utils.db['product_info'].insert(index['products'])
   print "Done"
