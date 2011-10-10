from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template
from regr.models import Developer

developers_dict = {
    'queryset': Developer.objects.all(),
    'allow_empty': True,
    'template_name': 'vlistdevelopers.html',
}
teams_dict = {
    'queryset': Developer.objects.values('team').order_by('team').distinct(),
    'template_name':'vlistteams.html',
}

urlpatterns = patterns('validate.views',
    # General lists
    (r'^$', direct_to_template, {'template': 'basevalidate.html'}),
    (r'^developers/$', list_detail.object_list, developers_dict),
    (r'^teams/$', list_detail.object_list, teams_dict),

    # Specific gets
    (r'^team/(?P<team>\w{3})/$', 'display_team'),
    (r'^developer/(?P<developer>\w+)/$', 'display_developer'),
    (r'^message/(?P<message>[\w\d_]+)/$', 'display_message'),
    (r'^message/$', 'search_message'),
    (r'^usermessage/$', 'search_user_message'),
    # Other
    (r'^help/$', 'help'),
)
