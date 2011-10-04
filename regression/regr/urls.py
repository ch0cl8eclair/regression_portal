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
RELEASE_URL2 = r'^%s/%s/%s/' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT)
PACKAGE_URL  = r'^%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT)
LAYER_URL    = r'^%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT)
DIR_URL      = r'^%s/%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT)
FILE_URL     = r'^%s/%s/%s/%s/%s/%s/%s/$' % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT, FILE_PAT)
FILE_URL2    = r'^%s/%s/%s/%s/%s/%s/%s/'  % (PROJECT_PAT, BRANCH_PAT, RELEASE_PAT, PACKAGE_PAT, LAYER_PAT, DIR_PAT, FILE_PAT)

urlpatterns = patterns('regr.views',
    (r'^$', 'list_projects'),
    (r'^help/$', 'help'),
    (PROJECT_URL, 'list_branches'),
    
    (BRANCH_URL2 + r'[Ll]atest/$', 'display_latest'),
    (BRANCH_URL2 + r'ReleaseTotals/$', 'display_totals_chart'),
    (BRANCH_URL2 + r'ReleasePassRate/$', 'display_pass_rate_chart'),
    (BRANCH_URL, 'list_releases'),

    (RELEASE_URL2 + r'[Cc]ompliance/$', 'display_compliance'),
    (RELEASE_URL, 'display_release_summary'),
    (PACKAGE_URL, 'display_layers'),
    (LAYER_URL, 'display_dirs'),
    (DIR_URL, 'display_results'),
    
    (FILE_URL2 + r'history$', 'display_file_history'),
    (FILE_URL, 'display_file_details'),
)

