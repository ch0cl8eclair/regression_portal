from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'regr.views.list_projects'),
    (r'^(?P<project>\w{1,3})/$', 'regr.views.list_branches'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/ReleaseTotals/$', 'regr.views.display_totals_chart'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/ReleasePassRate/$', 'regr.views.display_pass_rate_chart'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/$', 'regr.views.list_releases'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/(?P<release>\d+\D\d+\D\d+)/$', 'regr.views.display_results'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/(?P<release>\d+\D\d+\D\d+)/(?P<package>\w+)/$', 'regr.views.display_results'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/(?P<release>\d+\D\d+\D\d+)/(?P<package>\w+)/(?P<layer>\w+)/$', 'regr.views.display_results'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/(?P<release>\d+\D\d+\D\d+)/(?P<package>\w+)/(?P<layer>\w+)/(?P<directory>.+)/$', 'regr.views.display_results'),    
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/(?P<release>\d+\D\d+\D\d+)/(?P<package>\w+)/(?P<layer>\w+)/(?P<directory>.+)/(?P<filename>.+)/history$', 'regr.views.display_file_history'),
    (r'^(?P<project>\w{1,3})/(?P<branch>\w+)/(?P<release>\d+\D\d+\D\d+)/(?P<package>\w+)/(?P<layer>\w+)/(?P<directory>.+)/(?P<filename>.+)$', 'regr.views.display_file_details'),
)

