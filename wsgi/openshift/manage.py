#!/usr/bin/env python
import os

ON_OPENSHIFT = False
if os.environ.has_key('OPENSHIFT_REPO_DIR'):
   ON_OPENSHIFT = True

if ON_OPENSHIFT:
   from django.core.management import execute_manager
   import imp

   try:
       imp.find_module('settings') # Assumed to be in the same directory.
   except ImportError:
       import sys
       sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
       sys.exit(1)

   import settings

   if __name__ == "__main__":
       execute_manager(settings)
else:
   from django.core.management import execute_manager
   import imp

   try:
       imp.find_module('local_settings') # Assumed to be in the same directory.
   except ImportError:
       import sys
       sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
       sys.exit(1)

   import local_settings

   if __name__ == "__main__":
       execute_manager(local_settings)
