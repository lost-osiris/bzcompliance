from django.shortcuts import render_to_response, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.urlresolvers import resolve
from django.utils.safestring import mark_safe
from django.template import Context
from django.http import Http404

from pymongo import MongoClient
from bson.objectid import ObjectId
import simplejson, requests, datetime, copy, os, urllib

from dbManager import Manager
from Compliance import builder

import settings
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

manager = Manager.dbManager("bzcompliance")
client = MongoClient("seg-tools.hq.gsslab.rdu.redhat.com")
app_name = "bzcompliance"

@csrf_exempt
def add_requirement(request):
   req_type = ""
   id = ""
   name = ""
   edit = ""

   for i in request.GET:
      if i == "add_req":
         id = request.GET[i]
      if i == "req_type":
         req_type = request.GET[i]
         group = manager.get_group(id)
         name = group['name']

      if i == "edit":
         edit = request.GET[i]
        
   if edit != "" and req_type == "message":
      edit = manager.get_message(edit)
 
   if edit != "" and (req_type == "product" or req_type == "group"):
      edit = manager.get_group(edit)

   for i in request.POST:
      if i == "expression":
         expression = request.POST[i]
         
         if req_type == "message":
            message_name = request.POST['message_name']
            message_type = request.POST['message_type']
            message_description = request.POST['description']
            
            message = {
               "name": message_name,
               "message_type": message_type,
               "description": message_description,
            }

            if edit != "":
               message['message_id'] = edit['message_id']
               message['active'] = edit['active']
   
            manager.add_req(group, req_type, expression, message)

         if req_type == "product":
            req_name = str(name + "-main")
            manager.add_req(group, req_type, expression)

         if req_type == "group":
            req_name = str(name + "-main")
            manager.add_req(group, req_type, expression)

         return redirect(str("/" + app_name + "/compliance"))
         
   modal_input_boxes = [
      "Product",
      "Alias",
      "Assigned To",
      "Component", 
      "Reported",
      "Modified",
      "Summary",
      "Tags",
      "Url",
      "CC",
      "Keywords",
      "Devel Whiteboard",
      "Internal Whiteboard",
      "Whiteboard",
   ]
 
   requirement_list = [
      "Alias", 
      "Assigned To", 
      "Blocks", 
      "CC", 
      "Comments", 
      "Depends On", 
      "Devel Whiteboard",
      "External Trackers",
      "Flags", 
      "Internal Whiteboard",
      "Keywords",
      "Modified",
      "Priority",
      "Product",
      "Reported",
      "Resolution",
      "Severity",
      "Status",
      "Summary",
      "Tags",
      "Url",
      "Whiteboard"
   ]
   c = {
      "requirement_list": requirement_list, 
      "modal_input_boxes": modal_input_boxes, 
      "req_type":req_type,
      "add_to": name,
      "message": edit,
      "app_name": app_name,
   }

   return render_to_response("add_req/main.html", Context(c))
 
@csrf_exempt
def compliance(request):
   if request.method == "POST":
      for i in request.POST:
         if i == "remove_message":
            id = request.POST[i]
            manager.remove_message(id) 

         if i == "remove_group":
            id = request.POST[i]
            manager.remove_group(id) 

         if i == "delete_product":
            product_id = request.POST[i]
            value = manager.remove_group(product_id)

         if i == "add_product":
            product_name = request.POST['product_name']
            value = manager.add_group(product_name, isProduct = True)
             
         if i == "add_group":
            group_name = request.POST['name']
            product_id = request.POST['add_group']
            description = request.POST['description']
            manager.add_group_to_group(product_id, group_name, description)

         if i == "remove_variable":
            var_id = ObjectId(request.POST[i])
            manager.remove_variable(var_id)

         if i == "add_variable":
            group_id = ObjectId(request.POST[i])
            group = manager.get_group(group_id)

            var = {
               "name": request.POST['name'],
               "var_id": ObjectId(),
               "values": request.POST['value'],
               "parent_id": group_id,
               "description": request.POST['description'],
               "type": request.POST['type'],
            }

            manager.add_variable(group, var)

         if i == "edit_variable":
            var_id = ObjectId(request.POST[i])
            var = manager.get_variable(var_id)

            var['name'] = request.POST['name']
            var['description'] = request.POST['description']

            manager.edit_variable(var_id, var)

         if i == "add_element_to_variable":
            var_id = ObjectId(request.POST[i])
            value = request.POST['value']

            manager.add_element_to_variable(var_id, value)

         if i == "remove_element_from_variable":
            var_id = ObjectId(request.POST[i])
            value = request.POST['value']
            index = request.POST['index']
            manager.remove_element_from_variable(var_id, value, index)

         if i == "edit_element_in_variable":
            var_id = ObjectId(request.POST[i])
            value = request.POST['value']
            index = request.POST['index']
            manager.edit_element_in_variable(var_id, value, index)

         if i == "add_req":
            req_type = request.POST['req_type']
            group_name = request.POST['add_req']

            return redirect('/bzcompliance/addrequirement?'+ urllib.urlencode(request.POST))

         if i == "active_message":
            manager.activate_message(request.POST[i])         

         if i == "active_group":
            manager.activate_group(request.POST[i])         
            

   db = client['test']
   products = manager.find_all_products()

   return render_to_response("products/main.html", {"products":products, "app_name": app_name}) 

@csrf_exempt
def show_group(request, group_id):
   if request.method == "POST":
      for i in request.POST:
         if i == "add_group":
            group_name = request.POST['name']
            description = request.POST['description']
            manager.add_group_to_group(group_id, group_name, description)
                        
         if i == "add_req":
            req_type = request.POST['req_type']
            group_name = request.POST['add_req']

            return redirect('/addrequirement?'+ urllib.urlencode(request.POST))

         if i == "add_message":
            req_type = request.POST['req_type']
            group_name = request.POST['add_req']

            return redirect('/addrequirement?'+ urllib.urlencode(request.POST))

         if i == "remove_message":
            id = request.POST[i]
            manager.remove_message(id) 

         if i == "remove_group":
            id = request.POST[i]
            manager.remove_group(id) 

            return redirect('/compliance')

   group = manager.get_group(group_id)
   return render_to_response("groups/show_group/main.html", {"group":group, "app_name": app_name})

@csrf_exempt
def home(request):
   print request.COOKIES['rh_user']

   if request.method == "POST":
      password = request.POST['password']
      username = request.POST['username']

      if password == "" or username == "":
         return render_to_response("bz/error.html")

      is_id = False
      extra_info = False
      search = ""

      if request.POST['id'] != "":
         search = request.POST['id']
         is_id = True

      if search != "" and request.POST['url'] != "":
         return render_to_response("bz/error.html")

      if search == "":
         search = request.POST['url']
     
      return Problems().display_results(is_id, search, username=username, password=password)

   return render_to_response('core/main.html', {"app_name": app_name})

@csrf_exempt
def saved(request):
   db = client['saved_searches']
   searches = db.saved_search.find()

   if request.method == "POST":
      try:
         delete = request.POST['delete']
         db.saved_search.remove({"name":delete})

      except:
         password = request.POST['password']
         username = request.POST['username']

         if password == "" or username == "":
            return render_to_response("bz/error.html")

         is_id = False
         extra_info = False
         search = ""
         name = ""

         if request.POST['id'] != "":
            search = request.POST['id']
            is_id = True

         if search != "" and request.POST['url'] != "":
            return render_to_response("bz/error.html")

         if search == "":
            search = request.POST['url']

         if request.POST['name'] != "":
            name = request.POST['name']

         id = search if is_id else ""
         url = "" if is_id else search
         fields = "flags, external_bugs, comments"

         values = {
            "username": username,
            "password": password,
            "id": id,
            "url" : url,
            "fields" : "flags, external_bugs, comments"
         }

         query = {
            "id": id,
            "url": url,
            "fields": fields
         }
      
         results = requests.post("https://findbugs-seg.itos.redhat.com", data=values, verify=False).text

         bugs = simplejson.loads(results)

         data, passed, ignored = compliance.check_compliance(False, {}, results=bugs)

         data = correct_parent_clones(data)

         passed = correct_parent_clones(passed)

         saved_data = {"data":data, "ignored": ignored, "passed": passed}

         updated = datetime.datetime.now() + datetime.timedelta(hours=1) 

         if len(db.saved_search.find({"name":name}).distinct("name")) == 0:
            db.saved_search.insert({"name":name, "results": saved_data,
                "last_updated":updated, "query":query})

         else:
            db.saved_search.update({"name":name},{"$set": {"name":name, "results": saved_data,
               "last_updated":updated, "query":query}})
   
   return render_to_response("saved/main.html", {"searches":searches, "app_name": app_name})



@csrf_exempt
def check_bug_id(request, bug_id):
   if request.method == "POST":
      password = request.POST['password']
      username = request.POST['username']

      if password == "" or username == "":
         return render_to_response("bz/error.html")

      is_id = True
       
      return Problems().display_results(is_id, bug_id, username=username, password=password)

   return render_to_response('bugid/main.html', {"app_name": app_name})
   

@csrf_exempt
def bug_id(request, bug_id):
   db = client['saved_searches']

   results = db.saved_search.find({"name": bug_id}).distinct("results")[0]

   data = results['data']
   passed = results['passed']
   ignored = results['ignored']

   total_checked = len(data) + len(passed) + len(ignored)   
   total_ignored = len(ignored) 

   return render_to_response("bz/results.html", {"passed":passed, "ignored":ignored,
      "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "app_name": app_name})
   
class Problems:

   def display_results(self, is_id, search, username = None, password = None):
      usr = username
      psswd = password

      findbug_data = { 
         "username":usr,
         "password":psswd,
         "fields":"external_bugs,flags,comments",
         "id": "", 
         "url":"",
      }

      if is_id == True:
         findbug_data['id'] = search
      else:
         findbug_data['url'] = search
      all_products = manager.find_all_products()
      suite = builder.build(all_products)
      results = requests.post("https://findbugs-seg.itos.redhat.com", data=findbug_data, verify=False).text
      bugs = simplejson.loads(results)
      data = {}
      raw_data = []
      for bug in bugs['bugs']:
         suite.evaluate(bug)
         
         bug_info = {}
         messages = []
 
         for message in suite.get_messages():
            message_data = {}
            message_data['message_name'] = message['name']
            message_data['message_type'] = message['message_type']
            message_data['message'] = message['description']
            message_data['expression'] = message['expression']
            message_data['details'] = message['evaluator']
            message_data['path'] = message['absolute_path']

            message_data['raw_message_data'] = message

            if "error" in message:
               message_data['error'] = message['error']
            else:
               message_data['error'] = "No Error"
            messages.append(message_data)
            
         bug_info['messages'] = messages
         bug_info['all_data'] = suite.reduce()
      
         is_passed = None
         evaluated_data = []
         is_zstream = False

         for eval in bug_info['all_data']:
            output = {}
            if eval['result'] == True:
               is_passed = True
            elif eval['result'] == False:
               is_passed = False

            output['result'] = eval['result']
            output['expression'] = eval['expression']
            output['groups'] = eval['groups']
            evaluated_data.append(output)
   
         bug_info['is_passed'] = is_passed
         bug_info['evaluated_data'] = evaluated_data

         bug_info['bug_data'] = bug

         data[bug['id']] = bug_info

      c = {
         "raw_data":raw_data,
         "output":data,
         "built_structer":manager.find_all_products(),
         "app_name": app_name,
      }

      return render_to_response("results/main.html", c)

def find_num_sf(bug):
   count = 0
   for i in bug['data']['external_bugs']:
      if i['type']['type'] == "SFDC":
         count += 1

   return count

class Struct(object):
   def __init__(self, data):
      for name, value in data.iteritems():
         setattr(self, name, self.__wrap(value))
   def __wrap(self, value):
      if isinstance(value, (tuple, list, set, frozenset)): 
         return type(value)([self.__wrap(v) for v in value])
      else:
         return Struct(value) if isinstance(value, dict) else value
   
def classify(data):
   for i in xrange(len(data)):
      data[i] = Struct(data[i])
   return data

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
