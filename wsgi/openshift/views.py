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

from templatetags import templatetags
from dbManager import Manager
from Compliance import builder

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
ON_OPENSHIFT = False
if os.environ.has_key('OPENSHIFT_REPO_DIR'):
      ON_OPENSHIFT = True
if ON_OPENSHIFT:
   import settings

   try:
      client = MongoClient(os.environ.get('OPENSHIFT_MONGODB_DB_URL'))
   except:
      raise Http404

else:
   import local_settings

   client = MongoClient("osiris.usersys.redhat.com")

manager = Manager.dbManager("test")

@csrf_exempt
def add_requirement(request):
   req_type = ""
   id = ""
   name = ""

   for i in request.GET:
      if i == "add_req":
         id = request.GET[i]
      if i == "req_type":
         req_type = request.GET[i]
         group = manager.get_group(id)
         name = group['name']

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
               "description": message_description
            }
            
            manager.add_req(group, req_type, expression, message)

            return redirect(str('/showgroup/' + id))

         if req_type == "product":
            req_name = str(name + "-main")
            manager.add_req(group, req_type, expression)

            return redirect("/compliance")

         if req_type == "group":
            req_name = str(name + "-main")
            manager.add_req(group, req_type, expression)

            return redirect(str('/showgroup/' + id))
         
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
   }

   return render_to_response("bz/add_req/main.html", Context(c))
 
@csrf_exempt
def compliance(request):
   db = client['test']
   products = manager.find_all_products()

   if request.method == "POST":

      for i in request.POST:

         if i == "delete_product":
            product_name = request.POST[i]
            value = manager.remove_product(product_name)

         if i == "add_product":
            product_name = request.POST['product_name']
            value = manager.add_group(product_name, isProduct = True)
             
         if i == "add_group":
            group_name = request.POST['name']
            product_id = request.POST['add_group']
            description = request.POST['description']
            manager.add_group_to_group(product_id, group_name, description)

         if i == "add_req":
            req_type = request.POST['req_type']
            group_name = request.POST['add_req']

            return redirect('/addrequirement?'+ urllib.urlencode(request.POST))

         if i == "nested_group":
           continue 

   return render_to_response("bz/products/main.html", {"products":products}) 

@csrf_exempt
def show_group(request, group_id):
   group = manager.get_group(group_id)

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

   return render_to_response("bz/groups/show_group/main.html", {"group":group})

@csrf_exempt
def home(request):
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

   return render_to_response('bz/core/main.html', {"appname": resolve(request.path).app_name})

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
   
   return render_to_response("bz/saved/main.html", {"searches":searches})



@csrf_exempt
def check_bug_id(request, bug_id):
   if request.method == "POST":
      password = request.POST['password']
      username = request.POST['username']

      if password == "" or username == "":
         return render_to_response("bz/error.html")

      is_id = True
       
      return Problems().display_results(is_id, bug_id, username=username, password=password)

   return render_to_response('bz/bugid/main.html', {"appname": resolve(request.path).app_name})
   

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
      "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored})
   
def run_report(request, report_name):
   if request.POST != "":
      db = client['reports']
      report = db.reports.find({"name":report_name})

      query = report.distinct("query")

      if report['is_date_range'] == True:
         start = str(request.POST['start']).replace("/", "-")
         month = start[0:2]
         day = start[3:5]
         year = start[8:12]
      
         start = year + "-" + month + "-" + day

         end = str(request.POST['end']).replace("/", "-")
         month = end[0:2]
         day = end[3:5]
         year = end[8:12]

         end = year + "-" + month + "-" + day

         #Fill in date ranges
         query = query.replace("***", start, 1)
         query = query.replace("***", end)

         data, passed, ignored = compliance.check_compliance(False, query, username, password)

         total_checked = len(data) + len(passed) + len(ignored)   
         total_ignored = len(ignored) 
         temp = data

         data = correct_parent_clones(data)
         ignored = correct_parent_clones(ignored)
         passed = correct_parent_clones(passed)

         return render_to_response("bz/exceptions/results.html", {"passed":passed, "ignored":ignored,
            "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "temp":temp,
            "query": start})

      else:
         data, passed, ignored = compliance.check_compliance(False, query, username, password)

         total_checked = len(data) + len(passed) + len(ignored)   
         total_ignored = len(ignored) 
         temp = data

         data = correct_parent_clones(data)
         ignored = correct_parent_clones(ignored)
         passed = correct_parent_clones(passed)

         return render_to_response("bz/exceptions/results.html", {"passed":passed, "ignored":ignored,
            "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "temp":temp,
            "query": start})


   else:

      db = client['reports']
      reports = db.reports.find()
      
      return render_to_response("bz/reports/main.html", {"reports":reports})

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

      suite = builder.build(manager.find_all_products())
      results = requests.post("https://findbugs-seg.itos.redhat.com", data=findbug_data, verify=False).text
      bugs = simplejson.loads(results)
      data = []

      for i in bugs['bugs']:
         suite.evaluate(i, True)
         data.append(suite.html_string())
     
      c = {
         "raw_data":mark_safe(data),
      }

      return render_to_response("bz/results/results.html", c)

def correct_parent_clones(data):
   temp = copy.deepcopy(data)

   for bug,index in zip(temp, range(0, len(data))):
      parents = []
      clones = []
      
      check_parent_clone(temp, parents, "parents", index, bug)
      check_parent_clone(temp, clones, "clones", index, bug)
      check_parent_clone(temp, None, "data", index, bug)
   
      temp[index]['parents'] = parents
      temp[index]['clones'] = clones

   return temp

def check_parent_clone(data, list, type, index, bug):
   if type == "data":
      status = data[index]['data']['status']
      resolution = data[index]['data']['resolution']

      data[index]['num_sf'] = find_num_sf(bug)

      if status == "CLOSED" and resolution == "ERRATA":
         comments = data[index]['data']['comments']
         for j in comments:
            if j['author'] == "errata-xmlrpc@redhat.com" and "resolution of ERRATA" in j['text'] and j['is_private'] == "False":
               
               text = j['text']
               link = text.split("bug report.\n\n")   
               data[index]['errata_link'] = link[1]
               data[index]['errata_text'] = text

               num_sf = find_num_sf(bug)

               if num_sf == "" or num_sf == 0:
                  data[index]['errata_sf'] = "No SF account set"
               else:   
                  data[index]['errata_sf'] = num_sf

         data[index]['errata'] = 1
   else:
      for i in bug[type]:
         output = {}
         output['id'] = i
         output['data'] = data[index][type][i]
         
         status = data[index][type][i]['status']
         resolution = data[index][type][i]['resolution']

         if status == "CLOSED" and resolution == "ERRATA":
            comments = data[index][type][i]['comments']
            for j in comments:
               if j['author'] == "errata-xmlrpc@redhat.com" and "resolution of ERRATA" in j['text'] and j['is_private'] == "False":
                  
                  text = j['text']
                  link = text.split("bug report.\n\n")   
                  data[index]['errata_link'] = link[1]
                  data[index]['errata_text'] = text

                  num_sf = find_num_sf(bug)

                  if num_sf == "" or num_sf == 0:
                     data[index]['errata_sf'] = "No SF account set"
                  else:   
                     data[index]['errata_sf'] = num_sf

            data[index][str('errata_' + type)] = 1
            output['errata'] = 1
         else:
            output['errata'] = 0 

         list.append(output)

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
