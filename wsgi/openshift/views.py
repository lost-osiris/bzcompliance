import os
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
      data = {
         "106769" : { 
            "bugdata": {"id": "106769", "product": "RHEL"}, 
            "problems": [{"id":"flag error"}, {"message":"The flags are not properly set"}],
            },
         "103578" : { 
            "bugdata": {"id": "106769", "product": "RHEL"}, 
            "problems": [{"id":"Bug does not have GSS tracker"}, 
                         {"message":"Must have a current NVR GSS tracker"}
                        ],
            },
         }
      usr = username
      psswd = password

      data = compliance.check_compliance(is_id, search, email=usr, password=psswd)

      return render_to_response("bz/results.html", {"data":data})

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
