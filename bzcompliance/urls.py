from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'bzcompliance.views.home', name='home'),
    url(r'^/$', 'bzcompliance.views.home', name='home'),
    #url(r'^(?P<bug_id>.+)/$', 'bzcompliance.views.bug_id', name='bug_id'),
    #url(r'^bugid/(?P<bug_id>.+)$', 'bzcompliance.views.check_bug_id', name='bug_id'),
    #url(r'^saved$', 'bzcompliance.views.saved', name='saved'),

    url(r'^addrequirement', 'bzcompliance.views.add_requirement', name='addrequirement'),

    url(r'^compliance/$', 'bzcompliance.views.compliance', name='compliance'),
    url(r'^showgroup/(?P<group_id>.+)/$', 'bzcompliance.views.show_group', name='show_group'),
)
