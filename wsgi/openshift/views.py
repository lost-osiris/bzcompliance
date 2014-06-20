import os, datetime
import copy
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.urlresolvers import resolve
from django.utils.safestring import mark_safe
from Compliance import compliance

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
def rfe(request):
   if request.method == "POST":
      start = str(request.POST['start']).replace("/", "-")
      month = start[0:2]
      day = start[4:6]
      year = start[8:10]
   
      start = year + "-" + month + "-" + day

      end = str(request.POST['end']).replace("/", "-")
      month = end[0:2]
      day = end[4:6]
      year = end[8:10]

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
         "raw_data":data, "total_checked":total_checked, "total_ignored":total_ignored, "temp":temp})

   return render_to_response('bz/rfe/main.html')

class Problems:

   def display_results(self, is_id, search, username = None, password = None):
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

      status = temp[index]['data']['status']
      resolution = temp[index]['data']['resolution']
      
      num_sf = len(bug['data']['external_bugs'])

      if num_sf == "" or num_sf == 0:
         temp[index]['num_sf'] = 0
      else:   
         temp[index]['num_sf'] = num_sf

      if status == "CLOSED" and resolution == "ERRATA":
         comments = bug['data']['comments']
         for i in comments:
            if i['author'] == "errata-xmlrpc@redhat.com" and "resolution of ERRATA" in i['text'] and i['is_private'] == "False":
               
               text = i['text']
               link = text.split("bug report.\n\n")   
               temp[index]['errata_link'] = link[1]
               temp[index]['errata_text'] = text
               
               num_sf = len(bug['data']['external_bugs'])
               if num_sf == "" or num_sf == 0:
                  temp[index]['errata_sf'] = "No SF account set"
               else:   
                  temp[index]['errata_sf'] = num_sf

         temp[index]['errata'] = 1

      for i in bug['parents']:
         output = {}
         output['id'] = i
         output['data'] = temp[index]['parents'][i] 

         status = temp[index]['parents'][i]['status']
         resolution = temp[index]['parents'][i]['resolution']

         if status == "CLOSED" and resolution == "ERRATA":
            comments = temp[index]['parents'][i]['comments']
            for j in comments:
               if j['author'] == "errata-xmlrpc@redhat.com" and "resolution of ERRATA" in j['text'] and j['is_private'] == "False":

                  text = j['text']
                  link = text.split("bug report.\n\n")   
                  temp[index]['errata_link'] = link[1]
                  temp[index]['errata_text'] = text

                  num_sf = len(temp[index]['parents'][i]['external_bugs'])
                  if num_sf == "" or num_sf == 0:
                     temp[index]['errata_sf'] = "No SF account set"
                  else:   
                     temp[index]['errata_sf'] = num_sf

            temp[index]['errata_parent'] = 1
            output['errata'] = 1
         else:
            output['errata'] = 0 

         parents.append(output)

      for i in bug['clones']:
         output = {}
         output['id'] = i
         output['data'] = temp[index]['clones'][i]
         
         status = temp[index]['clones'][i]['status']
         resolution = temp[index]['clones'][i]['resolution']

         if status == "CLOSED" and resolution == "ERRATA":
            comments = temp[index]['clones'][i]['comments']
            for j in comments:
               if j['author'] == "errata-xmlrpc@redhat.com" and "resolution of ERRATA" in j['text'] and j['is_private'] == "False":
                  
                  text = j['text']
                  link = text.split("bug report.\n\n")   
                  temp[index]['errata_link'] = link[1]
                  temp[index]['errata_text'] = text

                  num_sf = len(temp[index]['clones'][i]['external_bugs'])
                  if num_sf == "" or num_sf == 0:
                     temp[index]['errata_sf'] = "No SF account set"
                  else:   
                     temp[index]['errata_sf'] = num_sf

            temp[index]['errata_clone'] = 1
            output['errata'] = 1
         else:
            output['errata'] = 0 

         clones.append(output)

      temp[index]['parents'] = parents
      temp[index]['clones'] = clones

   return temp

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
