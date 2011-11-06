# Django imports
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.http import last_modified
from django.views.decorators.cache import cache_control
from django.db.models import Count
from django.core.urlresolvers import reverse

# Models imports
from regr.models import *

# Python imports
import random
import time
import urllib
from datetime import datetime, timedelta


###############################################################################
# Request wrapper class provides a number of convenient helper functions
###############################################################################

class RegressionRequestWrapper:
    '''This class wraps the http url parameters and aids with the retrieval of the appropriate model objects'''
    
    def __init__(self, projectStr=None, branchStr=None, releaseStr=None, packageStr=None, layerStr=None, directoryStr=None, filenameStr=None):
        self.baseSiteURL   = 'regression'
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

    ###########################################################################
    # Def URL helper methods
    #
    def setBaseURL(self, newURL):
        self.baseSiteURL = newURL
        
    def setValidate(self, isValidate):
        if isValidate:
            self.setBaseURL('validate')
        else:
            self.setBaseURL('regression')
    
    def getBaseURL(self):
        if self.baseSiteURL == 'regression':
            return reverse('regr.views.list_projects')
        else:
            return reverse('validate_home')
    
    def getHelpURL(self):
        namespace = 'reg' if self.baseSiteURL == 'regression' else 'val'
        return reverse('%s:regr.views.help'%namespace);
        
     
    def getProjectURL(self):
        return reverse('regression:regr.views.list_branches', args=[self.projectStr])

    def getBranchURL(self):
        return reverse('regression:regr.views.list_releases', args=[self.projectStr, self.branchStr])

    def getReleaseURL(self):
        namespace = 'reg' if self.baseSiteURL == 'regression' else 'val'
        return reverse('%s:regr.views.display_release_summary'%namespace, args=[self.projectStr, self.branchStr, self.release.name])
        
    def getReleaseTotalsURL(self):
        return reverse('reg:regr.views.display_totals_chart', args=[self.projectStr, self.branchStr])
    
    def getReleasePassRateURL(self):
        return reverse('reg:regr.views.display_pass_rate_chart', args=[self.projectStr, self.branchStr])

    def getPackageSynchroURL(self):
        return reverse('regr.views.display_hosts_synchro', args=[self.projectStr, self.branchStr, self.release.name])
        
    def getReleaseDiffURL(self):
        return reverse('regr.views.display_release_diffs', args=[self.projectStr, self.branchStr, self.release.name])

    def getReleaseDiffCVSURL(self):
        return reverse('regr.views.display_release_diffs', args=[self.projectStr, self.branchStr, self.release.name])
        
    def getPackageURL(self):
        namespace = 'reg' if self.baseSiteURL == 'regression' else 'val'
        return reverse('%s:regr.views.display_layers'%namespace, args=[self.projectStr, self.branchStr, self.release.name, self.packageStr])
        
    def getLayerURL(self):
        namespace = 'reg' if self.baseSiteURL == 'regression' else 'val'
        return reverse('%s:regr.views.display_dirs'%namespace, args=[self.projectStr, self.branchStr, self.release.name, self.packageStr, self.layerStr])

    def getDirectoryURL(self):
        namespace = 'reg' if self.baseSiteURL == 'regression' else 'val'
        return reverse('%s:regr.views.display_results'%namespace, args=[self.projectStr, self.branchStr, self.release.name, self.packageStr, self.layerStr, self.directoryStr])

    def getFileURL(self):
        namespace = 'reg' if self.baseSiteURL == 'regression' else 'val'
        return reverse('reg:regr.views.display_file_details'%namespace, args=[self.projectStr, self.branchStr, self.release.name, self.packageStr, self.layerStr, self.directoryStr, self.filenameStr])
            
    def getFileHistoryURL(self):
        namespace = 'reg' if self.baseSiteURL == 'regression' else 'val'
        return reverse('%s:regr.views.display_file_history'%namespace, args=[self.projectStr, self.branchStr, self.release.name, self.packageStr, self.layerStr, self.directoryStr, self.filenameStr])

    def getFileDiffURL(self):
        return 'http://lonlnx27/ngd_test/web/cgi-bin/ngd_test_diff.cgi?layout=3&appli=FM&user=&branch={{ %s }}&release={{ %s }}&diff={{ %s }}/{{ %s }}/{{ %s }}/log/{{ %s }}' % ( self.branchStr, self.release.name, self.packageStr, self.layerStr, self.directoryStr, self.diffnameStr)
            
    def getFileShortDiffURL(self):
        return 'http://lonlnx27/ngd_test/web/cgi-bin/ngd_test_diff.cgi?layout=3&appli=FM&user=&branch={{ %s }}&release={{ %s }}&diff={{ %s }}/{{ %s }}/{{ %s }}/log/{{ %s }}&shortdiff=on' % ( self.branchStr, self.release.name, self.packageStr, self.layerStr, self.directoryStr, self.diffnameStr)
    
    def getInputFileURL(self):
        return 'http://lonlnx27/ngd_test/web/cgi-bin/ngd_test_report.cgi?layout=3&appli=FM&user=&input={{ %s }}/{{ %s }}/{{ %s }}/log/{{ %s }}' % ( self.packageStr, self.layerStr, self.directoryStr, self.lognameStr)

    def getLogFileURL(self):
        return 'http://lonlnx27/ngdfm-tst/htdocs/{{ %s }}/{{ %s }}/{{ %s }}/{{ %s }}/{{ %s }}/log/{{ %s }}' % ( self.branchStr, self.release.name, self.packageStr, self.layerStr, self.directoryStr, self.lognameStr)
    
    ###########################################################################
    
    def getProjectsList(self):
        '''Returns a list of all projects in the system'''
        self.project_list = get_list_or_404(CodeBase)
        return self.project_list

    def getBranchList(self):
        '''Returns a list of branches for the given project'''
        if (self.projectStr):
            self.project_list = get_list_or_404(CodeBase, project__exact=self.projectStr)
            return self.project_list
        raise Http404

    def getCodeBase(self):
        '''Gets the specific codebase object ie project-branch eg FM-DEV'''
        self.project = get_object_or_404(CodeBase, project__exact=self.projectStr, branch__exact=self.branchStr)
        return self.project

    def getReleaseList(self):
        '''Gets the list of release for the select project'''
        self.getCodeBase()
        if self.project.release_set is None or not self.project.release_set.exists():
            raise Http404
        self.release_list = self.project.release_set.values()[:5]
        return self.release_list

    def getLatestRelease(self):
        '''Gets the latest release for the select project'''
        self.getCodeBase()
        latest_release = Release.objects.filter(code_base__exact=self.project.id)[0]
        return latest_release

    def getRelease(self):
        '''Gets the specific release object'''
        self.getCodeBase()
        self.release = get_object_or_404(self.project.release_set, name__exact=self.releaseStr)
        #self.release = self.project.release_set.get(name__exact=self.releaseStr)
        return self.release
        
    def getReleaseQuerySet(self):
        '''Gets a query set containing all of the releases for the given project'''
        self.getCodeBase()
        querySet = Release.objects.filter(code_base=self.project.id)
        return querySet

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
        if file_list is not None and file_list.exists():
          file_start_time = file_list[0].start_time
          file_duration = file_list[0].duration
        else:
          return BAD_URL

        # Now retrieve the pacakge synchro info ie the host on which the package was run
        packageList = PackageSynchro.objects.filter(release__exact=self.release.id, package__exact=self.packageStr, layer__exact=self.layerStr);
        if packageList is None or not packageList.exists() or packageList[0] is None:
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

    def getPackagesList(self, querySet=None):
        '''Gets a list of the packages for the current release'''
        if not querySet:
            selected_release = self.getRelease()
            packages_hash = selected_release.files.values('package').order_by('package').distinct()
            self.packages_list = [str(x.get('package')) for x in packages_hash]
        else:
            packages_hash = querySet.values('file__package').order_by('file__package').distinct()
            self.packages_list = [str(x.get('file__package')) for x in packages_hash]
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
# Package heirarchy helpers
###############################################################################

class ReleaseHierarchy:
    '''Represents the top level release level of the regression hierarchy'''
    def __init__(self, querySet, selectedName=None, selectedSubName=None):
        self.regQuerySet = querySet
        self.selectedName = selectedName
        self.selectedSubName = selectedSubName

    def getFilterField(self):
        return 'file__package'

    def getDataSet(self):
        return self.regQuerySet.values(self.getFilterField(), 'status').annotate(Count('status')).order_by(self.getFilterField(), 'status')

    def setSelectedName(self, name):
        self.selectedName = name

    def createNewStatusHash(self):
        statusHash = {'pass' : 0, 'fail' : 0, 'total' : 0}
        return statusHash

    def __updateStatusHash__(self, pass_cases, fail_cases, total_cases, statusHash):
        if statusHash is not None:
            #print "Updating values: p %d, f: %d, t: %d with p:%d, f:%d, t:%d" % (statusHash['pass'],statusHash['fail'],statusHash['total'], pass_cases, fail_cases, total_cases)
            if 'pass' in statusHash.keys():
                statusHash['pass'] += pass_cases
            if 'fail' in statusHash.keys():
                statusHash['fail'] += fail_cases
            if 'total' in statusHash.keys():
                statusHash['total'] += total_cases

    def handleAdditionalData(self, name, statusHash):
        #print "handleAdditionalData processing %s"%name
        if self.selectedName is not None and self.selectedName == name:
            layerObj = LayerHierarchy(self.regQuerySet, self.selectedName)
            layerHash = layerObj.getDirList()

            if layerHash is not None:
                layerList = []
                for l in sorted(layerHash.keys()):
                    newHash = {}
                    newHash[l] = layerHash[l]
                    layerList.append(newHash)
                statusHash['layers'] = layerList

    def getDirList(self):
        '''Create a hash with hierarchy information'''
        resultsHash = {}
        statsQuerySet = self.getDataSet()
        for item in statsQuerySet:
            pass_cases = 0
            fail_cases = 0
            total_cases = 0
            status = item['status']
            count = int(item['status__count'])
            name = item[self.getFilterField()]

            # Get or create the hash for the package
            statusHash = {}
            if name in resultsHash.keys():
                statusHash = resultsHash[name]
            else:
                # Add new hash
                statusHash = self.createNewStatusHash()
                resultsHash[name] = statusHash

            if status == 0:
                pass_cases = count
            elif status == 1:
                fail_cases = count
            total_cases = count

            # Add the status stats
            self.__updateStatusHash__(pass_cases, fail_cases, total_cases, statusHash)
            #print "Pkg status: %s, status %d, count: %d" % (name, status, count)

            self.handleAdditionalData(name, statusHash)
        return resultsHash


class LayerHierarchy(ReleaseHierarchy):
    '''Represents the mid level layer level of the regression hierarchy'''
    def __init__(self, querySet, package):
        ReleaseHierarchy.__init__(self, querySet)
        self.package = package
    def getFilterField(self):
        return 'file__layer'
    def getDataSet(self):
        return self.regQuerySet.filter(file__package__exact=self.package).values(self.getFilterField(), 'status').annotate(Count('status')).order_by(self.getFilterField(), 'status')

    def handleAdditionalData(self, name, statusHash):
        dirObj = DirHierarchy(self.regQuerySet, self.package, name)
        dirHash = dirObj.getDirList()
        if dirHash is not None:
                dirList = []
                for d in sorted(dirHash.keys()):
                    newHash = {}
                    newHash[d] = dirHash[d]
                    dirList.append(newHash)
                statusHash['dirs'] = dirList

class DirHierarchy(LayerHierarchy):
    '''Represents the lower level dir/msg level of the regression hierarchy'''
    def __init__(self, querySet, package, layer):
        LayerHierarchy.__init__(self, querySet, package)
        self.layer = layer
    def getFilterField(self):
        return 'file__directory_path'
    def getDataSet(self):
        return self.regQuerySet.filter(file__package__exact=self.package, file__layer__exact=self.layer).values(self.getFilterField(), 'status').order_by(self.getFilterField(), 'status').annotate(Count('status'))
    def handleAdditionalData(self, name, statusHash):
        return None

def process_package_stats(statsQuerySet, package=None, layer=None):
    '''Generates a hash which contains all the package information for a release'''
    release = ReleaseHierarchy(statsQuerySet, package, layer)
    #release.setSelectedName(package)
    resultsHash = release.getDirList()
    return resultsHash

def process_package_stats_list(statsQuerySet, pkgs_list, package=None, layer=None):
    '''Generates a list of hashes which contains all the package information for a release'''
    pkg_hash_list = []
    pkg_hash = process_package_stats(statsQuerySet, package, layer)

    for p in pkgs_list:
        newHash = {}
        newHash[p] = pkg_hash[p]
        pkg_hash_list.append(newHash)
    return pkg_hash_list

def printPackageHash(packageHash):
    '''Test method to output the contents of a generated pkg hash'''
    if packageHash:
        for p,v in packageHash.items():
            print "Package: %s f: %d, t: %d" % (p, v['fail'], v['total'])
            if 'layers' in sorted(v.keys()):
                for l in v['layers']:
                    print "  Layer: %s f: %d, t: %d" % (l.items()[0][0], l.items()[0][1]['fail'], l.items()[0][1]['total'])
                    if 'dirs' in l.items()[0][1]:
                        for d in l.items()[0][1]['dirs']:
                            print "    Dir: %s f: %d, t: %d" % (d.items()[0][0], d.items()[0][1]['fail'], d.items()[0][1]['total'])

###############################################################################
# Release position, and related release helpers
###############################################################################
def getReleasePosition(relQuerySet, releaseId):
    '''Gets the query set position of the given release id'''
    relList = relQuerySet.values_list('id', flat=True)
    for idx,item in enumerate(relList):
        if item == releaseId:
            return idx
    return -1;
    

def getReleasePositionStr(relQuerySet, releaseName):
    '''Gets the query set position of the given release name'''
    relList = relQuerySet.values_list('name', flat=True)
    for idx,item in enumerate(relList):
        print str(item), releaseName
        if str(item) == releaseName:
            return idx
    return -1;

def getNextReleaseFromId(relQuerySet, currentReleasePos):
    '''Returns the previous release object based on the given release id'''
    if currentReleasePos > -1 and relQuerySet.count() > currentReleasePos:
        return relQuerySet[currentReleasePos + 1]
    return None

###############################################################################
# Basic stats functions
###############################################################################

TOTAL_KEY = 'total'

def getReleaseTotalStats(releaseID):
    release_stats = {}
    stats = RegressionResult.objects.filter(release__id__exact=releaseID).values('file__package', 'file__layer', 'status').order_by('file__package', 'file__layer', 'status').annotate(Count('status'))
    # Gather all the details into a hash of hashes
    # The hash format is:
    # { package.layer :
    #                  {status : status_count, total: total status count}
    # }
    
    for stat in stats:
        key = "%s.%s" % (stat['file__package'], stat['file__layer'])
        status = int(stat['status'])
        status_value = int(stat['status__count'])
        statusHash = {TOTAL_KEY: 0}
        if key in release_stats.keys():
            statusHash = release_stats[key]
        else:
            # Add new hash
            release_stats[key] = statusHash
        statusHash[TOTAL_KEY] += status_value
        statusHash[status] = status_value # store the individual status
    return release_stats
