"""
WSGI config for dev_management project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
import sys
path = '/var/www/apps/bzcompliance-dev/'
if path not in sys.path:
    sys.path.append(path)

os.environ["DJANGO_SETTINGS_MODULE"] = "settings.settings"

from django.core.wsgi import get_wsgi_application
import django.core.handlers.wsgi
import settings.monitor as monitor

monitor.start(interval=1.0)
monitor.track(os.path.join(os.path.dirname(__file__), 'site.cf'))
application = django.core.handlers.wsgi.WSGIHandler()
