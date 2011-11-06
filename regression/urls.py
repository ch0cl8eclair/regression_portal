from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


# Define component URL patterns
PROJECT_PAT = r'(?P<project>\w{1,3})'
BRANCH_PAT  = r'(?P<branch>\w+)'
RELEASE_PAT = r'(?P<release>\d+\D\d+\D\d+\D?\d*)'
PACKAGE_PAT = r'(?P<package>\w+)'
LAYER_PAT   = r'(?P<layer>\w+)'
DIR_PAT     = r'(?P<directory>[\w\d_]+)'
FILE_PAT    = r'(?P<filename>.+)'

REG_APP     = r'^regression/'
VAL_APP     = r'^validate/'

# define complete URL patters
PROJECT_URL  = r'^%s/$' % PROJECT_PAT
BRANCH_URL   = r'^%s/%s/$' % (PROJECT_PAT, BRANCH_PAT)
BRANCH_URL2  = r'^%s/%s/'  % (PROJECT_PAT, BRANCH_PAT)
RELEASE_URL  = r'^%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT)
RELEASE_URL2 = r'^%s/%s/%s/' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT)
PACKAGE_URL  = r'^%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT)
LAYER_URL    = r'^%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT)
DIR_URL      = r'^%s/%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT)
FILE_URL     = r'^%s/%s/%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT, FILE_PAT)
FILE_URL2    = r'^%s/%s/%s/%s/%s/%s/%s/'  % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT, FILE_PAT)



# TODO need to merge this into one function
#(RELEASE_URL, 'display_user_release_summary'),

common_patterns = patterns('regr.views',
    (r'^help/$', 'help'),
    (BRANCH_URL2 + r'[Ll]atest/$', 'display_latest'),
    (BRANCH_URL2 + r'ReleaseTotals/$', 'display_totals_chart'),
    (BRANCH_URL2 + r'ReleasePassRate/$', 'display_pass_rate_chart'),
    (BRANCH_URL, 'list_releases'),

    (RELEASE_URL, 'display_release_summary'),
    (PACKAGE_URL, 'display_layers'),
    (LAYER_URL, 'display_dirs'),
    (DIR_URL, 'display_results'),
    
    (FILE_URL2 + r'history$', 'display_file_history'),
    (FILE_URL, 'display_file_details'),
)

regr_only_patterns = patterns('regr.views',
    (r'^$', 'list_projects'),
    (PROJECT_URL, 'list_branches'),
    (RELEASE_URL2 + r'RegComparison/$', 'display_release_diffs'),
    (RELEASE_URL2 + r'regcomparison/$', 'display_release_diffs'),
    (RELEASE_URL2 + r'[Cc]ompliance/$', 'display_compliance'),
    (RELEASE_URL2 + r'HostsSynchro/$', 'display_hosts_synchro'),
    (RELEASE_URL2 + r'hostssynchro/$', 'display_hosts_synchro'),
)

    
urlpatterns = patterns('',

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # index, main welcome page
    (r'^$', 'regr.views.welcome'),
    
    # regression specific app urls
    (REG_APP, include(regr_only_patterns)),
    
    # Common regression app urls
    (REG_APP, include(common_patterns, namespace="reg", app_name="regression")),
    
    # Common validate app urls
    (VAL_APP, include(common_patterns, namespace="val", app_name="validate"), {'isValidate': True}),
    
    # Include validate only urls
    (VAL_APP, include('validate.urls')),
    
    # Data urls
    (r'^data/$', 'regr.charts.chart_data'),
    (r'^data/(?P<type>\w+)/(?P<releaseID>\d+)$', 'regr.charts.chart_data'),
    (r'^data/(?P<type>\w+)/$', 'regr.charts.chart_data'),
    
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DOC_ROOT}),
)
