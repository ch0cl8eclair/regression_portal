from regr.models import *
from django.db.models import Count

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
        print "handleAdditionalData processing %s"%name
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
