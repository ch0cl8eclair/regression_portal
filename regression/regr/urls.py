from django.conf.urls.defaults import *

# Define component URL patterns
PROJECT_PAT = r'(?P<project>\w{1,3})'
BRANCH_PAT  = r'(?P<branch>\w+)'
RELEASE_PAT = r'(?P<release>\d+\D\d+\D\d+\D?\d*)'
PACKAGE_PAT = r'(?P<package>\w+)'
LAYER_PAT   = r'(?P<layer>\w+)'
DIR_PAT     = r'(?P<directory>[\w\d_]+)'
FILE_PAT    = r'(?P<filename>.+)'

# define complete URL patters
PROJECT_URL  = r'^%s/$' % PROJECT_PAT
BRANCH_URL   = r'^%s/%s/$' % (PROJECT_PAT, BRANCH_PAT)
BRANCH_URL2  = r'^%s/%s/'  % (PROJECT_PAT, BRANCH_PAT)
RELEASE_URL  = r'^%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT)
PACKAGE_URL  = r'^%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT)
LAYER_URL    = r'^%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT)
DIR_URL      = r'^%s/%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT)
FILE_URL     = r'^%s/%s/%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT, FILE_PAT)
FILE_URL2    = r'^%s/%s/%s/%s/%s/%s/%s/'  % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT, FILE_PAT)

urlpatterns = patterns('',
    (r'^$', 'regr.views.list_projects'),
    (r'^help/$', 'regr.views.help'),
    (PROJECT_URL, 'regr.views.list_branches'),
    (BRANCH_URL2 + r'Latest/$', 'regr.views.display_latest'),
    (BRANCH_URL2 + r'ReleaseTotals/$', 'regr.views.display_totals_chart'),
    (BRANCH_URL2 + r'ReleasePassRate/$', 'regr.views.display_pass_rate_chart'),
    (BRANCH_URL, 'regr.views.list_releases'),

    (RELEASE_URL, 'regr.views.display_release_summary'),
    (PACKAGE_URL, 'regr.views.display_layers'),
    (LAYER_URL, 'regr.views.display_dirs'),
    (DIR_URL, 'regr.views.display_results'),
    
    (FILE_URL2 + r'history$', 'regr.views.display_file_history'),
    (FILE_URL, 'regr.views.display_file_details'),
)

