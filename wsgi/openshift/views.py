import os
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

      for i in bug['parents']:
         output = {}
         output['id'] = i
         output['data'] = temp[index]['parents'][i] 
         parents.append(output)

      for i in bug['clones']:
         output = {}
         output['id'] = i
         output['data'] = temp[index]['clones'][i] 
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
