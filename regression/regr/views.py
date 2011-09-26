from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from regr.models import *
from regr.utils import process_package_stats_list
from converttocsv import StatusTotals
from django.db.models import Count
# for the pie chart generation
from pyofc2  import *
import random
import time
from datetime import datetime, timedelta
import urllib

class RegressionRequestWrapper:
    '''This class wraps the http url parameters and aids with the retrieval of the appropriate model objects'''

    def __init__(self, projectStr=None, branchStr=None, releaseStr=None, packageStr=None, layerStr=None, directoryStr=None, filenameStr=None):
        self.projectStr    = projectStr
        self.branchStr     = branchStr
        self.releaseStr    = releaseStr
        self.packageStr    = packageStr
        self.layerStr      = layerStr
        self.directoryStr  = directoryStr
        self.filenameStr   = filenameStr
        self.compliance_warning = False
        if filenameStr is not None:
            self.lognameStr    = filenameStr.replace('.scn', '.log')
            self.diffnameStr   = filenameStr.replace('.scn', '.diff')

    def getProjectsList(self):
        '''Returns a list of all projects in the system'''
        self.project_list = get_list_or_404(CodeBase)
        return self.project_list

    def getBranchList(self):
        '''Returns a list of branches for the given project'''
        if (self.projectStr):
            self.project_list = get_list_or_404(CodeBase, project__exact=self.projectStr)
            return self.project_list
        return None ##TODO return 404

    def getCodeBase(self):
        '''Gets the specific codebase object ie project-branch eg FM-DEV'''
        self.project = get_object_or_404(CodeBase, project__exact=self.projectStr, branch__exact=self.branchStr)
        return self.project

    def getReleaseList(self):
        '''Gets the list of release for the select project'''
        self.getCodeBase()
        ## TODO again check for null and return 404
        self.release_list = self.project.release_set.values()[:5]
        return self.release_list

    def getRelease(self):
        '''Gets the specific release object'''
        self.getCodeBase()
        ## TODO check for null release
        self.release = self.project.release_set.get(name__exact=self.releaseStr)
        return self.release

    def getFileHistory(self):
        '''Gets the regression run history per release for a given file'''
        self.getCodeBase()
        release_result_list = RegressionResult.objects.filter(release__code_base__id__exact=self.project.id,
                                                                 file__package__exact=self.packageStr,
                                                                 file__layer__exact=self.layerStr,
                                                                 file__directory_path__exact=self.directoryStr,
                                                                 file__file_name__exact=self.filenameStr).values('release__name', 'status')
        stats_class = StatusTotals()
        self.historical_status_list = []
        for stat_item in release_result_list:
            new_hash = {}
            new_hash['release_name'] = str(stat_item['release__name'])
            new_hash['status'] = stats_class.getStatusStr(stat_item['status'])
            self.historical_status_list.append(new_hash)

        return self.historical_status_list

    def getCVSHistoryUrl(self):
      '''Creates the URL str for the cvs change viewer'''
      # The forward slashed need to be translated for the url, so do this first
      dirQuoted = urllib.quote("%s/%s/%s" % (self.packageStr, self.layerStr, self.directoryStr) , '')

      urlStr= "http://ncecvsgco/viewvc/bin/cgi/viewvc.cgi/asl_ngd/%s/?view=query&\
pathrev=%s&\
branch=%s&\
branch_match=exact&\
dir=%s&\
file=%s&\
file_match=exact&\
who=&\
who_match=exact&\
querysort=date&\
hours=2&\
date=all&\
mindate=&\
maxdate=&\
limit_changes=100" % (self.projectStr, self.branchStr, self.branchStr, dirQuoted, self.filenameStr)

      return urlStr

    def generateServerLogsUrl(self, branch, release, package, host, scenarioStartDateObj, scenarioEndDateObj):
        '''Creates the URL str for the log viewer server logs retrieve'''
        scenarioStartDate = ""
        scenarioStartTime = ""
        scenarioEndDate = ""
        scenarioEndTime = ""

        if scenarioStartDateObj is not None:
          scenarioStartDate = scenarioStartDateObj.strftime("%Y%m%d")
          scenarioStartTime = scenarioStartDateObj.strftime("%H%M%S")

        if scenarioEndDateObj is not None:
          scenarioEndDate = scenarioEndDateObj.strftime("%Y%m%d")
          scenarioEndTime = scenarioEndDateObj.strftime("%H%M%S")

        urlStr = "http://%s/logviewer/cgi-bin/getfelog.cgi?\
app=fml&\
phase=UT&\
filter=edi&\
getreply=on&\
showDuplicateConvIDs=off&\
mode=AND&\
expression1=&\
expression2=&\
expression3=&\
expression4=&\
expression5=&\
expression6=&\
mode2=AND&\
expression2_1=&\
expression2_2=&\
expression2_3=&\
expression2_4=&\
expression2_5=&\
expression2_6=&\
begindate=%s&\
begintime=%s&\
enddate=%s&\
endtime=%s&\
machine=UT%s&\
obeapp_dir=/vtmp/ngdfmbld/%s/%s/internal/%s/edi&\
file=feFML_otf*\
" % (host, scenarioStartDate, scenarioStartTime, scenarioEndDate, scenarioEndTime, host, branch, release, package)
        return urlStr

    def getServerLogsUrl(self):
        '''Generates the server logs url'''
        self.getCodeBase()
        self.getRelease()
        BAD_URL = "/doesnotexist.html"

        # Retrieve the regression result object - there should just be the one file
        file_list = RegressionResult.objects.filter(release__code_base__id__exact=self.project.id,
                                                                         file__package__exact=self.packageStr,
                                                                         file__layer__exact=self.layerStr,
                                                                         file__directory_path__exact=self.directoryStr,
                                                                         file__file_name__exact=self.filenameStr)
        file_start_time = None
        if file_list is not None and len(file_list) > 0:
          file_start_time = file_list[0].start_time
          file_duration = file_list[0].duration
        else:
          return BAD_URL

        # Now retrieve the pacakge synchro info ie the host on which the package was run
        packageList = PackageSynchro.objects.filter(release__exact=self.release.id, package__exact=self.packageStr, layer__exact=self.layerStr);
        if packageList is None or len(packageList) == 0 or packageList[0] is None:
            return BAD_URL
        pkgSync = packageList[0]

        # check if we have a start date and a host
        if pkgSync.start_date is None or file_start_time is None or pkgSync.host is None:
          return BAD_URL

        # Since the regression ran across midnight, we must identify the scenarion start time with the correct day.
        # So we place the scenario start time within the package run window to id the date, however we may not have all the value for this
        # So it is possible to generate the wrong value, but the chances of this happening should be slim ;-)

        # generate the package start date obj
        # if the package start time is missing then we can use the time from the release.
        pkg_start_time = pkgSync.start_time
        if pkg_start_time is None:
          pkg_start_time = self.release.date.strftime("%H%M%S")
        pkg_start_obj = datetime.strptime("%s %s"%(pkgSync.start_date, pkg_start_time.rjust(6, '0')), '%Y%m%d %H%M%S')

        # generate the scenario start date obj
        scenario_start_date_obj = datetime.strptime("%s %s"%(pkgSync.start_date, file_start_time.rjust(6, '0')), '%Y%m%d %H%M%S')

        # Check if the scenario fall on the next day and adjust
        if scenario_start_date_obj < pkg_start_obj:
          scenario_start_date_obj = scenario_start_date_obj +  timedelta(days=1)

        # generate the scenario end date
        scenario_end_date_obj = None
        if file_duration is not None:
          (hour, min, sec) = file_duration.split(",")
          scenario_end_date_obj = scenario_start_date_obj + timedelta(hours=int(hour), minutes=int(min), seconds=float(sec))

        url = self.generateServerLogsUrl(self.branchStr, self.releaseStr, self.packageStr, pkgSync.host, scenario_start_date_obj, scenario_end_date_obj)

        return url


    def getPackagesList(self):
        '''Gets a list of the packages for the current release'''
        selected_release = self.getRelease()
        packages_hash = selected_release.files.values('package').order_by('package').distinct()
        self.packages_list = [str(x.get('package')) for x in packages_hash]
        return self.packages_list

    def getPackageStats(self, releaseQuerySet):
        '''Gets the package stats for a given release, this reuses a queryset which just has the results for the matched release'''
        '''
        { pkgname: {pass: int,
                    fail: int,
                    layers: { layername : { pass: int,
                                            fail: int,
                                            dirs: { dirname : { pass: int,
                                                                fail: int }
                                                  }
                                          }
                            }
                    }
        }
        '''
        stats = releaseQuerySet.values('status').annotate(Count('status')).order_by('status')
        total_cases = 0
        pass_cases = 0
        fail_cases = 0
        if releaseQuerySet:
            for stat_item in stats:
                total_cases = total_cases + stat_item['status__count']
                self.release_stats[stat_item['status']] = str(stat_item['status__count'])
                if stat_item['status'] == 0:
                    pass_cases = int(stat_item['status__count'])
                elif stat_item['status'] == 1:
                    fail_cases = int(stat_item['status__count'])

    def getReleaseStats(self):
        '''Gets the top level stats for the current release'''
        self.release_stats = {}
        stats = RegressionResult.objects.filter(release__id__exact=self.release.id).values('status').annotate(Count('status')).order_by('status')
        total_cases = 0
        pass_cases = 0
        fail_cases = 0
        if stats:
            for stat_item in stats:
                total_cases = total_cases + stat_item['status__count']
                self.release_stats[stat_item['status']] = str(stat_item['status__count'])
                if stat_item['status'] == 0:
                    pass_cases = int(stat_item['status__count'])
                elif stat_item['status'] == 1:
                    fail_cases = int(stat_item['status__count'])
            self.release_stats[5] = total_cases
            # Remember that the pass rate should include pass, void and new, and not just pass!
            self.release_stats[6] = round((float(total_cases - fail_cases) / total_cases) * 100, 2)
        return self.release_stats

    def setComplianceWarning(self, complianceFailureExist):
        '''Sets the compliance failure warnings exist'''
        self.compliance_warning = complianceFailureExist



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
LIST_DIRS_HTML = 'listdirs.html'

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

def list_releases(request, project, branch):
    '''Lists all releases for the selected branch ie 24-0-219 etc'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    paramWrapper.getReleaseList()
    return render_to_response(LIST_RELEASES_HTML, {'reg_params': paramWrapper})

###############################################################################
# Chart Requests
###############################################################################
def display_totals_chart(request, project, branch):
    '''Displays the release figures totals chart for the given codebase'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    paramWrapper.getCodeBase()
    return render_to_response(DISPLAY_CHART_HTML, {'reg_params': paramWrapper, 'chart_type': 'bar'})

def display_pass_rate_chart(request, project, branch):
    '''Displays the release pass rate chart for the given codebase'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    paramWrapper.getCodeBase()
    return render_to_response(DISPLAY_CHART_HTML, {'reg_params': paramWrapper, 'chart_type': 'line'})

###############################################################################
# Get detailed file information
###############################################################################
def display_file_details(request, project, branch, release, package, layer, directory, filename):
    '''Displays the details for the given scenario file'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer, directory, filename)
    paramWrapper.getCodeBase()
    serverLogsUrl = paramWrapper.getServerLogsUrl()
    cvsUrl = paramWrapper.getCVSHistoryUrl()
    return render_to_response(DISPLAY_FILEDETAILS_HTML, {'reg_params': paramWrapper, 'serverLogsUrl' : serverLogsUrl, 'cvsUrl' : cvsUrl })

def display_file_history(request, project, branch, release, package, layer, directory, filename):
    '''Gets the regression pass status for the selected file over all the releases'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer, directory, filename)
    paramWrapper.getFileHistory()
    return render_to_response(DISPLAY_FILEHISTORY_HTML, {'reg_params': paramWrapper})

def display_release_summary(request, project, branch, release):
    '''Display the results for the selected release'''
    paramWrapper = RegressionRequestWrapper(project, branch, release)
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

def display_layers(request, project, branch, release, package):
    '''Display the results for the selected package'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package)
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

def display_dirs(request, project, branch, release, package, layer):
    '''Display the results for the selected layer'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer)
    selected_release = paramWrapper.getRelease()
    pkgs_list = paramWrapper.getPackagesList()
    regQuerySet = RegressionResult.objects.filter(release__id__exact=selected_release.id)

    # Get the status figures per package
    pkg_hash_list = process_package_stats_list(regQuerySet, pkgs_list, package, layer)

    selected_pkg_hash = None
    if pkg_hash_list is not None:
        for x in pkg_hash_list:
            if x.items()[0][0] == package:
                if x.items()[0][1]['layers'] is not None:

                    layersList = x.items()[0][1]['layers']
                    for l in layersList:
                        if l.items()[0][0] == layer:
                            #print l.items()[0][1]
                            selected_pkg_hash = l.items()[0][1]

    # Get top level stats for the release.
    paramWrapper.getReleaseStats()

    return render_to_response(LIST_DIRS_HTML, {'reg_params': paramWrapper, \
                                                     'pkg_hash_list' : pkg_hash_list, \
                                                     'sel_layer_hash' : selected_pkg_hash})

def display_results(request, project, branch, release, package=None, layer=None, directory=None):
    '''Display the results for the selected path ie for a release/package/layer'''
    paramWrapper = RegressionRequestWrapper(project, branch, release, package, layer, directory)
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
                                              'files_list' : files_list,
                                              'pkg_hash_list' : pkg_hash_list})

def display_latest(request, project, branch):
    '''Redirects the user to the latest release for the given branch and project'''
    paramWrapper = RegressionRequestWrapper(project, branch)
    latest_release = paramWrapper.getCodeBase().release_set.all()[0]

    return redirect('regr.views.display_release_summary', project=str(project), branch=str(branch), release=str(latest_release.name))

###############################################################################
# Chart Data Requests - used by the chart object to get the data figures
###############################################################################
def chart_data_test(request, type='bar', releaseID=-1):
    # Display the failures across the packages for the given release
    chart = open_flash_chart()
    t = title(text="FM Package Failures")
    chart.title = t

    b1 = bar()
    b1.text="Failures"

    # todo update for specified release
    results = RegressionResult.objects.filter(status='1', release__id__exact=releaseID).values('file__package').annotate(Count('file__package')).order_by('file__package')
    package_names = []
    package_failures = []
    for result_item in results:
        package_names.append(result_item['file__package'])
        package_failures.append(result_item['file__package__count'])
    b1.values = package_failures

    chart.add_element(b1)
    chart.y_axis = y_axis(min=0, max=250, steps=10)
    chart.x_axis = x_axis(labels=labels(labels=package_names))
    return HttpResponse(chart.render())

def chart_data(request, type='bar', releaseID=-1):
    '''json data request handler for ofc chart data requests'''
    t = title(text=time.strftime('%a %Y %b %d'))
    #tt = tooltip("P #val#%")
    chart = open_flash_chart()
    chart.title = t

    # Generic bar chart - for testing
    if type == 'bar1':
        b1 = bar()
        b1.values = range(9,0,-1)
        b2 = bar()
        b2.values = [random.randint(0,9) for i in range(9)]
        b2.colour = '#56acde'
        chart.add_element(b1)
        chart.add_element(b2)

    # Display the release stats for all releases - bar chart which shows three bars per release
    if type == 'bar':
        t = title(text="FM Release Figures")
        chart.title = t
        release_list = Release.objects.all().order_by('date')
        b1 = bar()
        b1.text="total"

        b2 = bar()
        b2.colour = '#00ee00'
        b2.text="pass"

        b3 = bar()
        b3.colour = '#ee0000'
        b3.text="fail"

        total_values = []
        pass_values = []
        fail_values = []
        release_names = []
        for rel in release_list:
            total_values.append(rel.total_files)
            pass_values.append(rel.total_pass)
            fail_values.append(rel.total_fail)
            release_names.append(str(rel.name))

        b1.values = total_values
        b2.values = pass_values
        b3.values = fail_values

        chart.add_element(b1)
        chart.add_element(b2)
        chart.add_element(b3)
        chart.y_axis = y_axis(min=0, max=20000, steps=1000)
        #chart.x_axis = x_axis(labels=labels(labels=release_names))

        # Custom x axis to display vertical labels
        x = x_axis()
        xlbls = x_axis_labels(steps=1, rotate='vertical', colour='#FF0000')
        xlbls.labels = release_names
        x.labels = xlbls
        chart.x_axis = x

    # Generic line chart
    elif type == 'line':
        t = title(text="FM Pass Rate")
        chart.title = t
        release_list = Release.objects.all().order_by('date')
        l1 = line()
        #l1.text="total"

        release_names = []
        percentage_pass = []
        for rel in release_list:
            release_names.append(str(rel.name))
            if rel.total_files == 0:
                pass_rate = 0
            else:
                pass_rate = round((float(rel.total_files - rel.total_fail) / rel.total_files) * 100, 2)
            percentage_pass.append(pass_rate)

        l1.values = percentage_pass
        #l1.values = [9,8,7,6,5.0,4,3.2,2,1]
        chart.add_element(l1)
        chart.y_axis = y_axis(min=0, max=100, steps=10)
        #chart.x_axis = x_axis(labels=labels(labels=release_names))

        # Custom x axis to display vertical labels
        x = x_axis()
        xlbls = x_axis_labels(steps=1, rotate='vertical', colour='#FF0000')
        xlbls.labels = release_names
        x.labels = xlbls
        chart.x_axis = x

    # Line chart showing the percentage pass rate across releases - for testing
    elif type == 'line1':
        l = line()
        l.values = [9,8,7,6,5.0,4,3.2,2,1]
        chart.add_element(l)
    # Generic pie chart - for testing
    elif type == 'pie1':
        p1 = pie();
        pa = pie_value(value=1, label='a', colour='#FF0000');
        pb = pie_value(value=2, label='b', colour='#F0DD00');
        pc = pie_value(value=3, label='c', colour='#FFDD00');
        p1.values = [pa, pb, pc]
        #p1.labels = ['a', 'b', 'c', 'd']
        chart.add_element(p1)
    # Pie chart for specific release which shows break down of file types: pass, fail, void, new etc
    elif type == 'pie':
        t = title(text="Release Figures")
        chart.title = t
        colour_mapping = {
            0 : '#00FF00', \
            1 : '#FF0000', \
            2 : '#FFDD00', \
            3 : '#0000FF', \
            4 : '#0D0D0D' \
        }
        # Obtain stats for release
        # todo need to dynamically select the release
        stats = RegressionResult.objects.filter(release__id__exact=releaseID).values('status').annotate(Count('status')).order_by('status')
        # Reformat data
        release_stats = {}
        for stat_item in stats:
            release_stats[int(stat_item['status'])] = int(stat_item['status__count'])
        # Set data for pie chart
        p1 = pie();
        data_array = []
        stats_class = StatusTotals()
        for case_type in release_stats:
            #print "BSK %d %d %s %s" %(g, release_stats[g], stat_class.getStatusStr(g), colour_mapping[g])
            #current_pie_data = pie_value(value=int(release_stats[case_type]), label=stats_class.getStatusStr(case_type), colour=colour_mapping[case_type])
            current_pie_data = pie_value(value=release_stats[case_type], label=stats_class.getStatusStr(case_type), colour=colour_mapping[case_type])
            data_array.append(current_pie_data)
        p1.values = data_array

        chart.add_element(p1)
    # Bar chart to show package failures for a given release
    elif type == 'release_packages':
        release_stats = {}
        stats = RegressionResult.objects.filter(release__id__exact=releaseID).values('file__package', 'file__layer', 'status').annotate(Count('status')).order_by('file__package', 'file__layer', 'status')
        # Gather all the details into a hash of hashes
        # The hash format is:
        # { package.layer :
        #                  {status : status_count}
        # }
        for stat in stats:
            key = "%s.%s" % (str(stat['file__package']), str(stat['file__layer']))
            status = int(stat['status'])
            status_value = int(stat['status__count'])
            TOTAL_KEY = 'total'
            statusHash = {TOTAL_KEY: 0}
            if key in release_stats.keys():
                statusHash = release_stats[key]
            else:
                # Add new hash
                release_stats[key] = statusHash
            statusHash[TOTAL_KEY] += status_value
        # Now build the chart
        t = title(text="Release Total Package stats.")
        chart.title = t

        b2 = bar()
        b2.colour = '#00ee00'
        b2.text="total"

        total_values = []
        package_names = []
        for (pkg, statuses) in release_stats.items():
            total_values.append(statuses[TOTAL_KEY])
            package_names.append(pkg)

        b2.values = total_values

        chart.add_element(b2)

        chart.y_axis = y_axis(min=0, max=5000, steps=500)
        # Custom x axis to display vertical labels
        x = x_axis()
        xlbls = x_axis_labels(steps=1, rotate='vertical', colour='#FF0000')
        xlbls.labels = package_names
        x.labels = xlbls
        chart.x_axis = x

        #chart.x_axis = x_axis(labels=labels(labels=package_names))
    elif type == 'release_packages_fail':
        release_stats = {}
        stats = RegressionResult.objects.filter(release__id__exact=releaseID).values('file__package', 'file__layer', 'status').annotate(Count('status')).order_by('file__package', 'file__layer', 'status')
        # Gather all the details into a hash of hashes
        # The hash format is:
        # { package.layer :
        #                  {status : status_count}
        # }
        for stat in stats:
            key = "%s.%s" % (str(stat['file__package']), str(stat['file__layer']))
            status = int(stat['status'])
            status_value = int(stat['status__count'])
            statusHash = {}
            if key in release_stats.keys():
                statusHash = release_stats[key]
            else:
                # Add new hash
                release_stats[key] = statusHash
            statusHash[status] = status_value
        # Now build the chart
        t = title(text="Release Package Failure stats.")
        chart.title = t

        b3 = bar()
        b3.colour = '#ee0000'
        b3.text="fail"

        total_values = []
        pass_values = []
        fail_values = []
        package_names = []
        for (pkg, statuses) in release_stats.items():
            fail_count = 0
            pass_count = 0
            if 0 in statuses.keys():
                pass_count = statuses[0]
            if 1 in statuses.keys():
                fail_count = statuses[1]

            pass_values.append(pass_count)
            fail_values.append(fail_count)
            package_names.append(pkg)

        #b2.values = pass_values
        b3.values = fail_values

        #chart.add_element(b2)
        chart.add_element(b3)
        chart.y_axis = y_axis(min=0, max=400, steps=20)
        # Custom x axis to display vertical labels
        x = x_axis()
        xlbls = x_axis_labels(steps=1, rotate='vertical', colour='#FF0000')
        xlbls.labels = package_names
        x.labels = xlbls
        chart.x_axis = x

        #chart.x_axis = x_axis(labels=labels(labels=package_names))

    return HttpResponse(chart.render())
