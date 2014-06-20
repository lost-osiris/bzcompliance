from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'openshift.views.home', name='home'),
    url(r'^/$', 'openshift.views.home', name='home'),
    url(r'^rfe', 'views.rfe', name='rfe'),
    url(r'^(?P<bug_id>.+)/$', 'views.bug_id', name='bug_id'),
    url(r'^bugid/(?P<bug_id>.+)$', 'views.check_bug_id', name='bug_id'),
    url(r'^bugid/(?P<bug_id>.+)/$', 'views.check_bug_id', name='bug_id'),
    url(r'^saved$', 'views.saved', name='saved'),
)
