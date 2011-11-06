from django.conf.urls.defaults import *
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from regr.models import Developer
    
urlpatterns = patterns('validate.views',
    # General lists
    url(r'^$',
        TemplateView.as_view(template_name='basevalidate.html'), name="validate_home"),
    url(r'^charttest/$',
        TemplateView.as_view(template_name='charttest.html')),
        
    url(r'^developers/$',
        ListView.as_view(queryset=Developer.objects.all(),
                         template_name='vlistdevelopers.html'), name="validate_developers"),
    url(r'^teams/$', 
        ListView.as_view(queryset=Developer.objects.values('team').order_by('team').distinct(),
                         template_name='vlistteams.html'), name="validate_teams"),

    # Specific gets
    (r'^team/(?P<team>\w{3})/$', 'display_team'),
    (r'^developer/(?P<developer>\w+)/$', 'display_developer'),
    (r'^message/(?P<message>[\w\d_]+)/$', 'display_message'),
    (r'^message/$', 'search_message'),
    (r'^usermessage/$', 'search_user_message'),
)
