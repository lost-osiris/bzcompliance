import os
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from templatetags import app_filters
from django.core.urlresolvers import resolve

@csrf_exempt
def home(request):
   if request.method == "POST":
      password = request.POST['password']
      username = request.POST['username']

      if password == "" or username == "":
         return render_to_response("bz/error.html")

      saved_search = False
      search = ""

      if request.POST['id'] != "":
         search = request.POST['id']
         save_search = True

      if saved_search == False and request.POST['url'] != "":
         return render_to_response("bz/error.html")
      else:
         search = request.POST['url']
      
      return Problems().display_results(save_search, search, username=username, password=password)

   return render_to_response('bz/main.html', {"appname": resolve(request.path).app_name})

class Problems:

   def display_results(self, save_search, search, username = None, password = None):
      data = {
         "106769" : { 
            "bugdata": {
               "id": "67894", "product": "RHEL"}, 
               "problems": [{"type": "flag error", "message":"The flags are not properly set"}]
            }
         }

      return render_to_response("bz/results.html", {"data": data})

