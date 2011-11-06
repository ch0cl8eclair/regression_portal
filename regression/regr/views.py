# Django imports
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.http import last_modified
from django.views.decorators.cache import cache_control
from django.db.models import Count
from sets import Set

# Models imports
from regr.models import *
from regr.utils import process_package_stats_list, RegressionRequestWrapper, getNextReleaseFromId, getReleaseTotalStats, getReleasePosition

# Python imports
import random
import time
import urllib
from datetime import datetime, timedelta


###############################################################################
# Define main html template files
###############################################################################
WELCOME_HTML         = 'welcome.html'
HELP_HTML            = 'help.html'
LIST_CODEBASES_HTML  = 'listprojects.html'
LIST_RELEASES_HTML   = 'listreleases.html'
DISPLAY_CHART_HTML   = 'displaychart.html'
DISPLAY_CHART_PKG_HTML      = 'displaychartpkg.html'
DISPLAY_CHART_PKG_FAIL_HTML = 'displaychartpkgfail.html'
DISPLAY_FILEDETAILS_HTML    = 'displayfiledetails.html'
DISPLAY_FILEHISTORY_HTML    = 'displayfilehistory.html'
LIST_FILES_HTML       = 'listfiles.html'
RELEASE_SUMMARY_HTML  = 'releasesummary.html'
LIST_LAYERS_HTML = 'listlayers.html'
LIST_DIRS_HTML   = 'listdirs.html'
COMPLIANCE_HTML  = 'compliance.html'
SYNCHRO_HTML     = 'synchro.html'
COMPARISON_HTML  = 'regcomparison.html'

def latest_release(request, project, branch):
  '''Gets the date of the latest loaded release'''
  paramWrapper = RegressionRequestWrapper(project, branch)
  paramWrapper.getCodeBase()
  latest_release = paramWrapper.getLatestRelease()
  if latest_release is not None:
    return latest_release.date
  return None

###############################################################################
# Main list data requests
###############################################################################
def welcome(request):
    '''Request for the welcome page'''
    return render_to_response(WELCOME_HTML)

def help(request):
    '''Handle request for help'''
    return render_to_response(HELP_HTML)

def list_projects(request):
    '''Lists all projects in the system eg FM/CM'''
    paramWrapper = RegressionRequestWrapper()
    paramWrapper.getProjectsList()
    return render_to_response(LIST_CODEBASES_HTML, {'reg_params': paramWrapper})

def list_branches(request, project):
    '''Lists all branches for the selected project ie DEV/PROD'''
    paramWrapper = RegressionRequestWrapper(project)
    paramWrapper.getBranchList()
    return render_to_response(LIST_CODEBASES_HTML, {'reg_params': paramWrapper})

@last_modified(latest_release)
@cache_control(must_revalidate=True, max_age=3600)
def list_releases(request, project, branch):
    '''Lists all releases for the selected branch ie 24-0-219 etc'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    paramWrapper.getReleaseList()
    return render_to_response(LIST_RELEASES_HTML, {'reg_params': paramWrapper})

###############################################################################
# Chart Requests
###############################################################################
def display_totals_chart(request, project, branch, isValidate=False):
    '''Displays the release figures totals chart for the given codebase'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    paramWrapper.setValidate(isValidate)
    paramWrapper.getCodeBase()
    return render_to_response(DISPLAY_CHART_HTML, {'reg_params': paramWrapper, 'chart_type': 'bar'})

def display_pass_rate_chart(request, project, branch, isValidate=False):
    '''Displays the release pass rate chart for the given codebase'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    paramWrapper.setValidate(isValidate)
    paramWrapper.getCodeBase()
    return render_to_response(DISPLAY_CHART_HTML, {'reg_params': paramWrapper, 'chart_type': 'line'})

###############################################################################
# Get detailed file information
###############################################################################
def display_file_details(request, project, branch, release, package, layer, directory, filename, isValidate=False):
    '''Displays the details for the given scenario file'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer, directory, filename)
    paramWrapper.setValidate(isValidate)
    paramWrapper.getCodeBase()
    serverLogsUrl = paramWrapper.getServerLogsUrl()
    cvsUrl = paramWrapper.getCVSHistoryUrl()
    return render_to_response(DISPLAY_FILEDETAILS_HTML, {'reg_params': paramWrapper, 'serverLogsUrl' : serverLogsUrl, 'cvsUrl' : cvsUrl })

@last_modified(latest_release)
@cache_control(must_revalidate=True, max_age=3600)
def display_file_history(request, project, branch, release, package, layer, directory, filename, isValidate=False):
    '''Gets the regression pass status for the selected file over all the releases'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer, directory, filename)
    paramWrapper.setValidate(isValidate)
    paramWrapper.getFileHistory()
    return render_to_response(DISPLAY_FILEHISTORY_HTML, {'reg_params': paramWrapper})

def display_release_summary(request, project, branch, release, isValidate=False):
    '''Display the results for the selected release'''
    paramWrapper = RegressionRequestWrapper(project, branch, release)
    paramWrapper.setValidate(isValidate)
    selected_release = paramWrapper.getRelease()

    # Process request to display the packages chart for the release
    if 'type' in request.REQUEST.keys() and request.REQUEST['type'] is not None:
        if request.REQUEST['type'] == 'package':
            return render_to_response(DISPLAY_CHART_PKG_HTML, {'reg_params': paramWrapper, 'chart_type': 'release_packages'})
        elif request.REQUEST['type'] == 'package_fail':
            return render_to_response(DISPLAY_CHART_PKG_FAIL_HTML, {'reg_params': paramWrapper, 'chart_type': 'release_packages_fail'})
        else:
            raise Http404

    pkgs_list = paramWrapper.getPackagesList()
    regQuerySet = RegressionResult.objects.filter(release__id__exact=selected_release.id)

    # Check if there are any compliance warnings and display a warning on screen
    cpFailures = regQuerySet.filter(file__package__startswith='ngcp', status='1')
    if cpFailures and cpFailures.count() > 0:
        paramWrapper.setComplianceWarning(True)

    # Get the status figures per package
    pkg_hash_list = process_package_stats_list(regQuerySet, pkgs_list, None, None)

    # Get top level stats for the release.
    paramWrapper.getReleaseStats()

    return render_to_response(RELEASE_SUMMARY_HTML, {'reg_params': paramWrapper, \
                                                     'pkg_hash_list' : pkg_hash_list})
                                                     
def display_compliance(request, project, branch, release):
    '''Display the compliance figures for the selected release'''
    paramWrapper = RegressionRequestWrapper(project, branch, release)
    selected_release = paramWrapper.getRelease()

    pkgs_list = paramWrapper.getPackagesList()
    regQuerySet = RegressionResult.objects.filter(release__id__exact=selected_release.id)

    # Check if there are any compliance warnings and display a warning on screen
    compliance_folders = regQuerySet.filter(file__package__startswith='ngcp', status='1').values('file__package', 'file__layer', 'file__directory_path').order_by('file__package').annotate(Count('file__directory_path'))

    # Get the compliance source file data
    compliance_files = ComplianceFile.objects.filter(release__exact=selected_release.id)

    # Get the status figures per package
    pkg_hash_list = process_package_stats_list(regQuerySet, pkgs_list, None, None)

    return render_to_response(COMPLIANCE_HTML, {'reg_params': paramWrapper, \
                                                'pkg_hash_list' : pkg_hash_list, \
                                                'compliance_folders' : compliance_folders, \
                                                'compliance_files' : compliance_files})
                                                
def display_hosts_synchro(request, project, branch, release):
    '''Displays the hosts synchro information for a given release'''
    paramWrapper = RegressionRequestWrapper(project, branch, release)
    selected_release = paramWrapper.getRelease()
    
    object_list = PackageSynchro.objects.filter(release__exact=selected_release.id)
    
    return render_to_response(SYNCHRO_HTML, {'reg_params': paramWrapper, \
                                             'object_list' : object_list})
                                                
def display_layers(request, project, branch, release, package, isValidate=False):
    '''Display the results for the selected package'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package)
    paramWrapper.setValidate(isValidate)
    selected_release = paramWrapper.getRelease()

    pkgs_list = paramWrapper.getPackagesList()
    regQuerySet = RegressionResult.objects.filter(release__id__exact=selected_release.id)
    
    # Get the status figures per package
    pkg_hash_list = process_package_stats_list(regQuerySet, pkgs_list, package, None)

    selected_pkg_hash = None
    if pkg_hash_list is not None:
        for x in pkg_hash_list:
            if x.items()[0][0] == package:
                selected_pkg_hash = x.items()[0][1]
    
    
    # Get top level stats for the release.
    paramWrapper.getReleaseStats()

    return render_to_response(LIST_LAYERS_HTML, {'reg_params': paramWrapper, \
                                                 'pkg_hash_list' : pkg_hash_list, \
                                                 'sel_pkg_hash' : selected_pkg_hash})

def display_dirs(request, project, branch, release, package, layer, isValidate=False):
    '''Display the results for the selected layer'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer)
    paramWrapper.setValidate(isValidate)
    selected_release = paramWrapper.getRelease()
    pkgs_list = paramWrapper.getPackagesList()
    regQuerySet = RegressionResult.objects.filter(release__id__exact=selected_release.id)

    # Get the status figures per package
    pkg_hash_list = process_package_stats_list(regQuerySet, pkgs_list, package, layer)

    selected_pkg_hash = None
    summaryHash = {}
    
    if pkg_hash_list is not None:
        for x in pkg_hash_list:
            if x.items()[0][0] == package:
                if x.items()[0][1]['layers'] is not None:

                    layersList = x.items()[0][1]['layers']
                    for l in layersList:
                        if l.items()[0][0] == layer:
                            selected_pkg_hash = l.items()[0][1]

    # Get top level stats for the release.
    paramWrapper.getReleaseStats()

    return render_to_response(LIST_DIRS_HTML, {'reg_params': paramWrapper, \
                                                'pkg_hash_list' : pkg_hash_list, \
                                                'sel_layer_hash' : selected_pkg_hash, \
                                                'summary_hash' : summaryHash})

def display_results(request, project, branch, release, package=None, layer=None, directory=None, isValidate=False):
    '''Display the results for the selected path ie for a release/package/layer'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer, directory)
    paramWrapper.setValidate(isValidate)
    selected_release = paramWrapper.getRelease()
    # Process request to display the packages chart for the release
    if 'type' in request.REQUEST.keys() and request.REQUEST['type'] is not None:
        if request.REQUEST['type'] == 'package':
            return render_to_response(DISPLAY_CHART_PKG_HTML, {'reg_params': paramWrapper, 'chart_type': 'release_packages'})
        elif request.REQUEST['type'] == 'package_fail':
            return render_to_response(DISPLAY_CHART_PKG_FAIL_HTML, {'reg_params': paramWrapper, 'chart_type': 'release_packages_fail'})
        else:
            raise Http404

    pkgs_list = paramWrapper.getPackagesList()
    regQuerySet = RegressionResult.objects.filter(release__id__exact=selected_release.id)

    # Get the status figures per package
    pkg_hash_list = process_package_stats_list(regQuerySet, pkgs_list, package, layer)

    # get the list of files for the directory
    files_list = RegressionResult.objects.filter(file__package__exact=package, file__layer__exact=layer, file__directory_path__exact=directory, release__id__exact=selected_release.id)

    return render_to_response(LIST_FILES_HTML, {'reg_params': paramWrapper, \
                                              'files_list' : files_list, \
                                              'pkg_hash_list' : pkg_hash_list})


@last_modified(latest_release)
@cache_control(must_revalidate=True, max_age=3600)
def display_latest(request, project, branch, isValidate=False):
    '''Redirects the user to the latest release for the given branch and project'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    paramWrapper.setValidate(isValidate)
    latest_release = paramWrapper.getCodeBase().release_set.all()[0]

    return redirect('regression:regr.views.display_release_summary', project=str(project), branch=str(branch), release=str(latest_release.name))

def display_release_diffs(request, project, branch, release):
    '''Display the results for the selected release'''
    paramWrapper = RegressionRequestWrapper(project, branch, release)
    selected_release = paramWrapper.getRelease()
    
    releaseQuerySet = paramWrapper.getReleaseQuerySet()
    # get the totals figures for the current release
    currentTotalsHash = getReleaseTotalStats(selected_release.id)
    currentRelPos = getReleasePosition(releaseQuerySet, selected_release.id)
    
    # now get previous release
    previousRelease = getNextReleaseFromId(releaseQuerySet, currentRelPos)
    previousReleaseName = previousRelease.name
    previousReleaseDate = previousRelease.date
    # get the totals figures for the previous release
    outputList = []
    if previousRelease is not None:
        previousTotalsHash = getReleaseTotalStats(previousRelease.id)
        
        pKeys = sorted(previousTotalsHash.keys())
        cKeys = sorted(currentTotalsHash.keys())
        # Find items only in previous set
        tSet = Set(cKeys)
        tSet.update(pKeys)
        
        # Now create a joint list
        totalKeys = []
        totalKeys.extend(tSet)
        
        for cItem in sorted(totalKeys):
            newDetailsHash = {'name':cItem}
            # populate current release details
            currentItemHash = currentTotalsHash.get(cItem, {})
            newDetailsHash['currentTotal'] = currentItemHash.get('total', 0)
            newDetailsHash['currentFail']  = currentItemHash.get(1, 0)
            newDetailsHash['currentPass']  = currentItemHash.get(0, 0)
            # populate previous release details
            # TODO this might be empty
            previousItemHash = previousTotalsHash.get(cItem,{})
            newDetailsHash['previousTotal'] = previousItemHash.get('total', 0)
            newDetailsHash['previousFail']  = previousItemHash.get(1, 0)
            newDetailsHash['previousPass']  = previousItemHash.get(0, 0)
            
            newDetailsHash['totalDiff'] = currentItemHash.get('total', 0) - previousItemHash.get('total', 0)
            newDetailsHash['failDiff']  = currentItemHash.get(1, 0) - previousItemHash.get(1, 0)
            newDetailsHash['passDiff']  = currentItemHash.get(0, 0) - previousItemHash.get(0, 0)
            outputList.append(newDetailsHash)
            
    return render_to_response(COMPARISON_HTML, {'reg_params': paramWrapper, \
                                                'previous_release' : previousReleaseName, \
                                                'previous_release_date' : previousReleaseDate, \
                                                'packages_comparison' : outputList})
