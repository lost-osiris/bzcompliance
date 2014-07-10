from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'openshift.views.home', name='home'),
    url(r'^/$', 'openshift.views.home', name='home'),
    #url(r'^(?P<bug_id>.+)/$', 'views.bug_id', name='bug_id'),
    #url(r'^bugid/(?P<bug_id>.+)$', 'views.check_bug_id', name='bug_id'),
    url(r'^saved$', 'views.saved', name='saved'),

    url(r'^addrequirement', 'views.add_requirement', name='addrequirement'),

    url(r'^compliance$', 'views.compliance', name='compliance'),
    url(r'^showgroup/(?P<group_id>.+)/$', 'views.show_group', name='show_group'),
)
