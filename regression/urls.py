from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^regression/', include('regression.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # index, main welcome page
    (r'^$', 'regr.views.welcome'),
    
    # the front page
                       
    # index, winapproach welcome page
    (r'^winapproach$', 'regr.views.winapproach'),
                       
    # index, code paths welcome page
    (r'^codepaths$', 'regr.views.code_paths'),
                       
    # index, regression welcome page
    (r'^regression/', include('regr.urls')),
                       
    # index, code paths welcome page
    (r'^links$', 'regr.views.links'),

    (r'^data/$', 'regr.views.chart_data'),
    (r'^data/barPackages/$', 'regr.views.chart_data2'),
    (r'^data/(?P<type>\w+)/$', 'regr.views.chart_data'),
    
    
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DOC_ROOT}),
)
