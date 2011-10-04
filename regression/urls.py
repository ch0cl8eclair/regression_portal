from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # index, main welcome page
    (r'^$', 'regr.views.welcome'),
    
    # regression app urls
    (r'^regression/', include('regr.urls')),
    
    # validate app urls
    (r'^validate/', include('validate.urls')),
    
    # Data urls
    (r'^data/$', 'regr.views.chart_data'),
    (r'^data/(?P<type>\w+)/(?P<releaseID>\d+)$', 'regr.views.chart_data'),
    (r'^data/(?P<type>\w+)/$', 'regr.views.chart_data'),
    
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DOC_ROOT}),
)
