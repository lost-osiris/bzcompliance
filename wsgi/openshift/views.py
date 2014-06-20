import os, datetime
import copy
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.urlresolvers import resolve
from django.utils.safestring import mark_safe
from Compliance import compliance
import pymongo
from pymongo import MongoClient
from django.http import Http404
import simplejson
import requests
import datetime

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

   client = MongoClient("127.0.0.1")

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

   return render_to_response('bz/main.html', {"appname": resolve(request.path).app_name})

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
         saved_data = {"bugs":simplejson.loads(results)}

         updated = datetime.datetime.now() 

         if len(db.saved_search.find().distinct("name")) == 0:
            db.saved_search.insert({"name":name, "results": saved_data,
                "last_updated":updated, "query":query})

         else:
            db.saved_search.update({"name":name},{"$set": {"name":name, "results": saved_data,
               "last_updated":updated, "query":query}})
   
   return render_to_response("bz/saved/main.html", {"searches":searches})

@csrf_exempt
def bug_id(request, bug_id):
   db = client['saved_searches']

   results = db.saved_search.find({"name": bug_id}).distinct("results")
   bugs = results[0]['bugs']

   data, passed, ignored = compliance.check_compliance(False, {}, results=bugs)

   total_checked = len(data) + len(passed) + len(ignored)   
   total_ignored = len(ignored) 
   temp = data

   data = correct_parent_clones(data)
   ignored = correct_parent_clones(ignored)
   passed = correct_parent_clones(passed)

   return render_to_response("bz/results.html", {"passed":passed, "ignored":ignored,
      "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "temp":temp})
   
@csrf_exempt
def rfe(request):
   if request.method == "POST":
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

      password = request.POST['password']
      username = request.POST['username']

      #RFE Query
      rfe_search = ( "https://bugzilla.redhat.com/"
                     "buglist.cgi?"
                     "f1=keywords"
                     "&f2=creation_ts"
                     "&f3=creation_ts"
                     "&o1=substring"
                     "&o2=greaterthaneq"
                     "&o3=lessthaneq"
                     "&query_format=advanced"
                     "&v1=FutureFeature"
                     "&v2=***"
                     "&v3=***")

      #Fill in date ranges
      new_search = rfe_search.replace("***", start, 1)
      new_search = new_search.replace("***", end)

      #Call script
      data, passed, ignored = compliance.check_compliance(False, new_search, username, password)

      total_checked = len(data) + len(passed) + len(ignored)   
      total_ignored = len(ignored) 
      temp = data

      data = correct_parent_clones(data)
      ignored = correct_parent_clones(ignored)
      passed = correct_parent_clones(passed)

      return render_to_response("bz/rfe/results.html", {"passed":passed, "ignored":ignored,
         "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "temp":temp,
         "query": start})

   return render_to_response('bz/rfe/main.html')

class Problems:

   def display_results(self, is_id, search, username = None, password = None, results = None):
      if results != None:
         data, passed, ignored = compliance.check_compliance(is_id, search, results)

         total_checked = len(data) + len(passed) + len(ignored)   
         total_ignored = len(ignored) 
         temp = data

         data = correct_parent_clones(data)
         ignored = correct_parent_clones(ignored)
         passed = correct_parent_clones(passed)

         return render_to_response("bz/results.html", {"passed":passed, "ignored":ignored,
            "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "temp":temp})

      else:
         usr = username
         psswd = password

         data, passed, ignored = compliance.check_compliance(is_id, search, email=usr, password=psswd)

         total_checked = len(data) + len(passed) + len(ignored)   
         total_ignored = len(ignored) 
         temp = data

         data = correct_parent_clones(data)
         ignored = correct_parent_clones(ignored)
         passed = correct_parent_clones(passed)

         return render_to_response("bz/results.html", {"passed":passed, "ignored":ignored,
            "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "temp":temp})

def correct_parent_clones(data):
   temp = copy.deepcopy(data)

   for bug,index in zip(temp, range(0, len(data))):
      parents = []
      clones = []
      
      check_parent_clone(temp, parents, "parents", index, bug)
      check_parent_clone(temp, clones, "clones", index, bug)
      check_parent_clone(temp, None, "bug", index, bug)
   
      temp[index]['parents'] = parents
      temp[index]['clones'] = clones

   return temp

def check_parent_clone(data, list, type, index, bug):
   if type == "bug":
      status = data[index]['data']['status']
      resolution = data[index]['data']['resolution']

      data[index]['num_sf'] = find_num_sf(bug)

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
