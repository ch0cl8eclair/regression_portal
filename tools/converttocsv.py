#!/usr/bin/env python

import django
from regr.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from subprocess import *
import time
import datetime
import sys
import os
import glob

#print "Django version is: %s" % django.get_version()

USAGE="""Usage: converttocsv.py <regression file dir>"""

###############################################################################
# Class definitions
###############################################################################
class SourceDataFile:
    '''Encapsulates a regression data file, its name is composed of various parts.'''
    def __init__(self, filename):
        (self.project, self.package, self.layer, self.branch) = filename.split('.')[:4]
    def getProject(self):
        return self.project
    def getPackage(self):
        return self.package
    def getLayer(self):
        return self.layer
    def getBranch(self):
        return self.branch

###############################################################################
class DatabaseTableCache:
    '''Internal representation of a database table(RegressionFile) read in from an exported csv'''
    def __init__(self, filename):
        '''Read in the exported table data file'''
        self.cachedRecords = {}
        print "Opening cache file: %s\n" % filename
        dbFile = open(filename)
        for recordLine in dbFile:
            (recLayer, recDir, recFile, recId) = recordLine.split('|')[:4]
            # TODO need to refactor for sep layer
            recId = recId.replace("\n", "")
            #justLayer = os.path.dirname(recDirStr)
            #justDir = os.path.basename(recDirStr)
            # Check layer
            if recLayer in self.cachedRecords.keys():
                layerHash = self.cachedRecords[recLayer]
            else:
                layerHash = {}
                self.cachedRecords[recLayer] = layerHash
            # check dir
            if recDir in layerHash.keys():
                dirHash = layerHash[recDir]
            else:
                dirHash = {}
                layerHash[recDir] = dirHash

            # add file
            dirHash[recFile] = recId
            # now do the check
            if dirHash[recFile] != recId:
                print "damn bugger did not go in"
            if self.cachedRecords[recLayer][recDir][recFile] != recId:
                print "Failed to add entry: %s %s %s\n" % ",".join(recLayer, recDir, recFile)
        dbFile.close()
    def getRecordId(self, layer, dir, file):
        '''Return the record id of the given file if it exits in the cache, -1 otherwise'''
        #print "getting cache key: %s\n" % ",".join([layer, dir, file])
        if self.cachedRecords is not None:
            try:
                return self.cachedRecords[layer][dir][file]
            except KeyError:
                #print >> sys.stderr, "keyerror: %s-%s-%s.\n" % (layer, dir, file)
                return -1
        return -1

###############################################################################
class DatabaseUtil:
    '''Utility functions to interact with the database.'''
    def __init__(self, sourceDataFile, sourceBaseId):
        self.sourceDataFile = sourceDataFile
        self.sourceBaseId = sourceBaseId
        self.newRegressionFileRecords = []
        self.newRegressionResultRecords = []

    def __getSqlCommandFile__(self):
        '''Gets the name of the sql command file which is used to hold the export data commands'''
        return "get_%s_data.sql" % self.sourceDataFile.getPackage()

    def __getExportFile__(self):
        '''Gets the name of the csv export file which is used to hold the export data'''
        return "exp_%s_reg_file.csv" % self.sourceDataFile.getPackage()

    def createSqlCommandRegressionFile(self):
        self.__generateCommandFile__(self.__getSqlCommandFile__())

    def __generateCommandFile__(self, filename):
        commandFile = open(filename, 'w')
        commandFile.write(self.__getRegressionFileExportCommands__())
        commandFile.close()

    def __getRegressionFileExportCommands__(self):
        '''Generates the commands needed to export the regression file data from the db'''
        commandStr = '''.mode list
.separator |
.output %s
select layer, directory_path, file_name, id from regr_regressionfile where code_base_id = %s and package = "%s";
.exit
''' % (self.__getExportFile__(), self.sourceBaseId, self.sourceDataFile.getPackage())
        return commandStr

    def exportRegressionFileData(self, regenerateCmdFile=True):
        '''Exports the regression file data for a given package to a file'''
        if regenerateCmdFile:
            self.createSqlCommandRegressionFile()
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            sqllitefilename=settings.DATABASES["default"]["NAME"]
        # TODO handle case where we are using a different Db
        p1 = Popen(["cat", self.__getSqlCommandFile__()], stdout=PIPE)
        p2 = Popen(["sqlite3", sqllitefilename], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()
        output = p2.communicate()[1]
        if output is None:
            return True
        print >> sys.stderr, "error status of export was: %s" % output
        return False

    def readInDatabaseTableCache(self, regenerateCmdFile=True):
        self.exportRegressionFileData(regenerateCmdFile)
        dbcache = DatabaseTableCache(self.__getExportFile__())
        return dbcache

    def convertBoolForDb(self, mybool):
        '''Util function to convert a bool to a str'''
        if mybool:
            return "1"
        return "0"

    def __writeRecordsToFile__(self, filename, records):
        '''Writes the given records to the given file'''
        importFile = open(filename, 'w')
        importFile.write("\n".join(records))
        importFile.close()

    def __writeRecordsToFileAsSql__(self, filename, tablename, records):
        '''Writes the given records for the given table to the given file'''
        importFile = open(filename, 'w')
        importFile.write("BEGIN TRANSACTION;\n")
        for record in records:
            recStr = "INSERT INTO %s VALUES( %s );\n" % (tablename, record)
            importFile.write(recStr)
        importFile.write("END;\n")
        importFile.close()

    def __saveRecordsCsv__(self, importFileName, fileRecords, databaseTable):
        '''Imports the given records into the database by way of an intermediate csv file'''
        # Generate the import csv file
        self.__writeRecordsToFile__(importFileName, fileRecords)
        # Now import the file into the Db
        importCommand = '\".import %s %s\"' % (importFileName, databaseTable)
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            sqllitefilename=settings.DATABASES["default"]["NAME"]
        p1 = Popen(["sqlite3", sqllitefilename, importCommand], stdout=PIPE)
        output = p1.communicate()[1]
        if output is not None:
            return False
        return True

    def __saveRecordsSql__(self, importFile, databaseTable, databaseRecords):
        '''Imports the given records into the database by way of an intermediate sql script file'''
        # Generate the import sql file
        self.__writeRecordsToFileAsSql__(importFile, databaseTable, databaseRecords)
        # Now import the file into the Db
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            sqllitefilename=settings.DATABASES["default"]["NAME"]
        p1 = Popen(["cat", importFile], stdout=PIPE)
        p2 = Popen(["sqlite3", sqllitefilename], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()
        output = p2.communicate()[1]
        if output is None:
            return True
        return False

    ###
    # Regression File methods
    #
    def __getCsvRegressionFileImportFile__(self):
        return "imp_%s_reg_file.csv" % self.sourceDataFile.getPackage()

    def __getSqlRegressionFileImportFile__(self):
        return "imp_%s_reg_file.sql" % self.sourceDataFile.getPackage()

    def addNewRegressionFileRecord(self, directory, filename):
        recordLine = "null, %s, '%s', '%s', '%s', '%s'" % (self.sourceBaseId, self.sourceDataFile.getPackage(), self.sourceDataFile.getLayer(), directory, filename)
        self.newRegressionFileRecords.append(recordLine)

    def saveRegressionFileRecords(self):
        return self.__saveRegressionFileRecordsSql__()

    def __saveRegressionFileRecordsCsv__(self):
        result = self.__saveRecordsCsv__(self.__getCsvRegressionFileImportFile__(), self.newRegressionFileRecords, "regr_regressionfile")
        if not result:
            print >> sys.stderr, "Error saving regression file records."
            return False
        return True

    def __saveRegressionFileRecordsSql__(self):
        # Generate the import sql file
        result = self.__saveRecordsSql__(self.__getSqlRegressionFileImportFile__(), "regr_regressionfile", self.newRegressionFileRecords)
        if not result:
            print >> sys.stderr, "Error saving regression file records."
            return False
        return True

    ###
    # Regression Result methods
    #
    def __getCsvRegressionResultImportFile__(self):
        return "imp_%s_reg_result.csv" % self.sourceDataFile.getPackage()

    def __getSqlRegressionResultImportFile__(self):
        return "imp_%s_reg_result.sql" % self.sourceDataFile.getPackage()

    def addNewRegressionResultRecord(self, releaseId, fileId, status, duration):
        recordLine = "null, %s, %s, %s, 0, null, null, null, null, %s, null" % (releaseId, fileId, str(status), duration)
        self.newRegressionResultRecords.append(recordLine)

    def saveRegressionResultRecords(self):
        return self.__saveRegressionResultRecordsSql__()

    def __saveRegressionResultRecordsCsv__(self):
        result = self.__saveRecordsCsv__(self.__getCsvRegressionResultImportFile__(), self.newRegressionResultRecords, "regr_regressionresult")
        if not result:
            print >> sys.stderr, "Error saving regression result records."
            return False
        return True

    def __saveRegressionResultRecordsSql__(self):
        # Generate the import sql file
        result = self.__saveRecordsSql__(self.__getSqlRegressionResultImportFile__(), "regr_regressionresult", self.newRegressionResultRecords)
        if not result:
            print >> sys.stderr, "Error saving regression file records."
            return False
        return True

###############################################################################

def updateReleaseRecordWithStats(oRelease, statusTotals):
    oRelease.total_files = statusTotals.total_count
    oRelease.total_pass  = statusTotals.total_pass
    oRelease.total_fail  = statusTotals.total_fail
    oRelease.total_void  = statusTotals.total_void
    oRelease.total_new   = statusTotals.total_new
    oRelease.total_other = statusTotals.total_other
    oRelease.save()

def convertDurationStr(durationStr):
  seconds = float(durationStr)
  m, s = divmod(seconds, 60)
  h, m = divmod(m, 60)
  return "'%d,%d,%.1f'" % (h, m, s)

###
# Main method
#
def main():
    ###
    # Check the arguments
    #
    if len(sys.argv) != 2:
        print USAGE
        sys.exit()

    ###
    # Check the directory exists and its name format
    # The file dir should be of the format <project>.<branch>.<release> eg fm.DEV.25-0-219
    #
    fileDir = sys.argv[1];
    if not os.path.isdir(fileDir):
        print "Error: The given dir: %s does not exist." % fileDir
        sys.exit()

    ###
    # read the version.txt file
    #
    versionFile=fileDir + os.sep + 'version.txt'
    print "version file is: %s"  % versionFile
    if not os.path.isfile(versionFile):
        print "Error version file does not exist"
        sys.exit()

    f = open(versionFile)
    versionData = f.read()
    f.close()

    print "read data of version.txt is: %s" % versionData
    (releaseVersion, releaseDate) = versionData.split(',')
    releaseVersion = releaseVersion.strip()
    releaseDate = releaseDate.strip() # remove leading space
    print "Release version is: %s, release date is: %s" % (releaseVersion, releaseDate)


    ###
    # Obtain the code base record
    #
    code_base_id = -1
    try:
        oCodeBase = CodeBase.objects.get(project="fm", branch="DEV")
        code_base_id = oCodeBase.id
    except CodeBase.DoesNotExist:
        print "Code base not found"
        sys.exit()

    print "Code base id for FM: %d" % code_base_id


    ###
    # Now retrieve the release object, check if it already exists
    #
    release_id = -1
    try:
        oRelease = Release.objects.get(code_base=code_base_id, name=releaseVersion)
        release_id = oRelease.id
    except Release.DoesNotExist:
        timestring = releaseDate.replace(" UTC", "")
        time_format = "%Y-%m-%d %H:%M:%S"
        rel_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timestring, time_format)))
        oRelease = Release(code_base=oCodeBase, name=releaseVersion, date=rel_date)
        oRelease.initialise_counters()
        oRelease.save()
        release_id = oRelease.id

    print "Release id for release %s is: %d" % (releaseVersion, release_id)


    ###
    # Now process the list of data files to process
    # Their format should be:  fm.ngcp4rgr.edi.DEV.data
    os.chdir(fileDir)
    dataFiles = glob.glob("*.data")
    print "%d files found to process." % len(dataFiles)

    # Break up the data file name into into component parts
    statusTotals = StatusTotals()
    # Iterate over the data files, one per package/layer
    for currentFile in dataFiles:
        sourceDataFile = SourceDataFile(currentFile)
        print "Proj: %s, Pack: %s, Layer: %s, Branch: %s" % (sourceDataFile.getProject(), sourceDataFile.getPackage(), sourceDataFile.getLayer(), sourceDataFile.getBranch())
        dbutil = DatabaseUtil(sourceDataFile, code_base_id)
        dbTableCache = dbutil.readInDatabaseTableCache() # This is the regressionfile cache for the current package

        # Now read the data file, it should contain the name and status
        # The file can potentially be empty
        #f = open("fm.DEV.25-0-219/fm.nglddrgr.xml.DEV.data")
        cf = open(currentFile)
        newRecordLines = []
        for cfLine in cf:
            # RetrieveDistributionForRamp/DistributionRequestForRamp.Case_001.scn,OK,\n
            (cfFileName, cfStatus, cfDurationStr) = cfLine.split(',')[:3]
            justDirName = os.path.dirname(cfFileName)
            justFileName = os.path.basename(cfFileName)
            # Update totals
            statusTotals.updateTotals(cfStatus)
            # check if this file already exist in the db
            recordId = dbTableCache.getRecordId(sourceDataFile.getLayer(), justDirName, justFileName)
            if recordId != -1:
                # generate regression result
                dbutil.addNewRegressionResultRecord(release_id, recordId, str(statusTotals.getNumericValue(cfStatus)), convertDurationStr(cfDurationStr))
            else:
                # need to store this record for later processing
                dbutil.addNewRegressionFileRecord(justDirName, justFileName)
                newRecordLines.append(cfLine)

        cf.close()
        # Processed all the lines from the current datafile.
        # Now save the new regression files
        dbutil.saveRegressionFileRecords()

        # Update the cache now that the Db has been updated
        dbTableCache = dbutil.readInDatabaseTableCache(False)
        # reprocess the regression files
        for newLine in newRecordLines:
            (cfFileName, cfStatus, cfDurationStr) = newLine.split(",")[:3]
            justDirName = os.path.dirname(cfFileName)
            justFileName = os.path.basename(cfFileName)

            recordId = dbTableCache.getRecordId(sourceDataFile.getLayer(), justDirName, justFileName)
            if recordId == -1:
                print >> sys.stderr, "Damn, something wrong here, the saved file has a negative id - file: %s %s %s" % (sourceDataFile.getPackage(), sourceDataFile.getLayer(), cfFileName)
                continue
            dbutil.addNewRegressionResultRecord(release_id, recordId, str(statusTotals.getNumericValue(cfStatus)), convertDurationStr(cfDurationStr))

        # Now save all the regression results.
        dbutil.saveRegressionResultRecords()
    # Right all files processed
    print "Processed files, Totals: %s" % (statusTotals)

    # Update the release record
    updateReleaseRecordWithStats(oRelease, statusTotals)
    print "done"

if __name__ == "__main__":
    main()
