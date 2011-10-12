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
import getopt

#print "Django version is: %s" % django.get_version()

USAGE="""Usage: converttocsv.py [-h -v -p <rel#> -c <rel#> -r] <regression file dir>
-h help
-v verbose
-p <rel#> load package data only from the dir against the given release number
-c <rel#> load compliance data only from the dir against the given release number
-r load responsible data only from the dir
If no options provided then all data is loaded by default.
"""
NO_SAVE = False

def usage():
  print USAGE

###############################################################################
# Class definitions
###############################################################################
class SourceDataFile:
    '''Encapsulates a regression data file, its name is composed of various parts.'''
    def __init__(self, filename):
        (self.project, self.package, self.layer, self.branch) = filename.split('.')[:4]
        self.filename = filename
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
    def __init__(self, fileDir, sourceDataFile, sourceBaseId):
        self.fileDir = fileDir
        self.sourceDataFile = sourceDataFile
        self.sourceBaseId = sourceBaseId

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

    def __writeRecordsToFileAsSql__(self, filename, tablename, records, deleteExistingRecords=False):
        '''Writes the given records for the given table to the given file'''
        importFile = open(filename, 'w')
        importFile.write("BEGIN TRANSACTION;\n")
        if deleteExistingRecords:
            importFile.write("DELETE FROM %s;\n" % tablename)
        for record in records:
            recStr = "INSERT INTO %s VALUES( %s );\n" % (tablename, record)
            importFile.write(recStr)
        importFile.write("END;\n")
        importFile.close()

    def __saveRecordsSql__(self, importFile, databaseTable, databaseRecords, deleteExistingRecords=False):
        '''Imports the given records into the database by way of an intermediate sql script file'''
        # Generate the import sql file

        self.__writeRecordsToFileAsSql__(importFile, databaseTable, databaseRecords, deleteExistingRecords)
        return self.__executeSqlOnDb__(importFile)

    def __executeSqlOnDb__(self, sqlFileToRun):
        '''Runs the given sql file against the Db, whether import or update script, it return a results status'''

        if NO_SAVE:
            return True
        # Now import the file into the Db
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            sqllitefilename=settings.DATABASES["default"]["NAME"]

        p1 = Popen(["cat", sqlFileToRun], stdout=PIPE)
        p2 = Popen(["sqlite3", sqllitefilename], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()
        output = p2.communicate()[1]
        if output is None:
            return True
        return False

    def __removeRelease__(self, releaseId):
        '''Removes the given release from the Db'''
        dbObjectsToRemove = ['ComplianceFile', 'PackageSynchro', 'RegressionResult']
        templateDeleteStr = "DELETE FROM regr_%s where release_id = %s;\n"

        outfilename = "delete_release.sql"
        outputFile = open(outfilename, 'w')
        outputFile.write("BEGIN;\n")
        for objName in dbObjectsToRemove:
          outputFile.write(templateDeleteStr % (objName, releaseId))
        outputFile.write("END;\n")
        outputFile.close()

        return self.__executeSqlOnDb__(outfilename)

    def __loadGenericData__(self, dbFileLoaderObj, runProcess=True):
        if runProcess:
            try:
                dbFileLoaderObj.processData()
            except IOError:
                print >> sys.stderr, "Failed to update table %s with data, table not updated." % dbFileLoaderObj.tableName
                return False
        if len(dbFileLoaderObj.getDbRecords()) == 0:
            return False
        # Generate the import sql file
        result = self.__saveRecordsSql__(dbFileLoaderObj.sqlFileName, dbFileLoaderObj.tableName, dbFileLoaderObj.getDbRecords(), dbFileLoaderObj.deleteExistingRecords)
        if not result:
            print >> sys.stderr, "Error saving %s file records." % (dbFileLoaderObj.getMsgStr())
            return False
        return True

    ###
    # Package Synchro records
    #
    def loadPackageSyncData(self, fileDir, release_id):
        pkgsync = PackageSyncParser(fileDir, release_id)
        return self.__loadGenericData__(pkgsync)

    ###
    # Compliance records
    #
    def loadComplianceData(self, fileDir, release_id):
        print "running compliance parser"
        compliance = ComplianceParser(fileDir, release_id)
        print "compliance parser run, now loading data..."
        return self.__loadGenericData__(compliance)

    ###
    # Responsible and developer records
    #
    def loadResponsibleData(self):
        reponsibleMgr = ResponsibleParser(self.fileDir)
        return self.__loadGenericData__(reponsibleMgr)

    ###
    # Regression result records
    #
    def loadRegressionResultData(self, regressionResultMgr, runProcess=True):
        return self.__loadGenericData__(regressionResultMgr, runProcess)

    ###
    # Regression file records
    #
    def loadRegressionFileData(self, regressionFileMgr, runProcess=True):
        return self.__loadGenericData__(regressionFileMgr, runProcess)

    ###
    # Remove a release
    #
    def removeReleaseRecords(self, release_id):
        return self.__removeRelease__(release_id)

###############################################################################

class DbFileLoader:
    def __init__(self, parentDir, dataFileName, sqlFileName, tableName):
        if parentDir is not None:
            self.dataFileName = os.sep.join([parentDir, dataFileName])
        else:
            self.dataFileName = dataFileName
        self.sqlFileName = sqlFileName
        self.tableName = tableName
        self.db_records = None
        self.deleteExistingRecords = False
        self.db_records = []

    def processData(self, recordLines=None):
        if recordLines is not None:
            return self.__processData2__(recordLines)

        if not os.path.isfile(self.dataFileName):
            print >> sys.stderr, "Unable to open the following data file: %s " % self.dataFileName

        #curpath = os.path.abspath(os.curdir)
        #print "Current path is: %s" % (curpath)
        #print "Trying to open: %s" % (os.path.join(curpath, self.dataFileName))

        cf = open(self.dataFileName)
        for cfLine in cf:
            outputDataLine = self.generateDataRecord(cfLine.rstrip())
            if outputDataLine is not None:
                self.db_records.append(outputDataLine)
        cf.close()

    def __processData2__(self, recordLines):
        '''Appends data from the given list to the main list'''
        for recLine in recordLines:
            if isinstance(recLine, str):
                outputDataLine = self.generateDataRecord(recLine.rstrip())
            else:
                outputDataLine = self.generateDataRecord(recLine)
            if outputDataLine is not None:
                self.db_records.append(outputDataLine)

    def generateDataRecord(self, dataLine):
        return None

    def getDbRecords(self):
        return self.db_records;

    def getMsgStr(self):
        return "data records"

class PackageSyncParser(DbFileLoader):
    '''Holds functionality for parsing the package-synchro data and updating the Db'''

    def __init__(self, fileDir, release_id):
        DbFileLoader.__init__(self, fileDir, "package_synchro.txt", "synchro.sql", "regr_packagesynchro")
        self.release_id = release_id

    def setDateTimeValue(self, dataStr):
        '''Converts the string value into a Db compatible form'''
        if dataStr is None or dataStr == "?":
          return "null"
        dataStr = dataStr.replace('-','')
        dataStr = dataStr.replace(':','')
        return "'%s'" % dataStr

    def generateDataRecord(self, dataLine):
        '''Parses the given line string into a db compatible data record'''
        # the line formats can be of the following forms
        # ngfuergr.edi    run on host: lonlnx30   from 2011-09-20 21:41:02 to 2011-09-20 22:20:02
        # ngcmsrgr.edi    run on host: lonlnx27   from 2011-09-20 23:05:03 to ?          ?

        line_values_list = dataLine.split()
        (package,layer) = line_values_list[0].split(".")[:2]
        host = line_values_list[4]
        start_date = self.setDateTimeValue(line_values_list[6])
        start_time = self.setDateTimeValue(line_values_list[7])
        end_date = self.setDateTimeValue(line_values_list[9])
        end_time = self.setDateTimeValue(line_values_list[10])

        outputDataLine = "null, %d, '%s', '%s', '%s', %s, %s, %s, %s" % (self.release_id, package, layer, host, start_date, start_time, end_date, end_time)
        return outputDataLine

    def getMsgStr(self):
        return "package synchro"

class ComplianceParser(DbFileLoader):
    '''Holds functionality for parsing the compliance data and updating the Db'''

    def __init__(self, fileDir, release_id):
        DbFileLoader.__init__(self, fileDir, "compliance.csv", "compliance.sql", "regr_compliancefile")
        self.release_id = release_id

    def setDateTimeValue(self, dataStr):
        '''Converts the string value into a Db compatible form'''
        if dataStr is None or dataStr == "?":
          return "null"
        dataStr = dataStr.replace('-','')
        dataStr = dataStr.replace(':','')
        return "'%s'" % dataStr

    def generateDataRecord(self, dataLine):
        '''Parses the given line string into a db compatible data record'''
        # the line formats can be of the following forms
        # FuelWeightAndIndexLogger.cpp,1.1.2.2,1.1.2.2
        # LinearLoadLimitsManager.cpp,1.1.2.1,1.1.2.2,gchazot,2011-08-08


        outputDataLine = None
        line_values_list = dataLine.split(",")
        filename  = 'null'
        loggedVer = 'null'
        rcsVer    = 'null'
        user      = None
        modDate   = 'null'

        if len(line_values_list) >= 3:
          filename  = line_values_list[0]
          loggedVer = line_values_list[1]
          rcsVer    = line_values_list[2]
          if len(line_values_list) == 5:
            user = line_values_list[3]
            modDate = self.setDateTimeValue(line_values_list[4])
          if user is not None:
            user = "'%s'" % user
          else:
            user = 'null'
          outputDataLine = "null, %s, '%s', '%s', '%s', %s, %s" % (self.release_id, filename, loggedVer, rcsVer, user, modDate)
        print "Output line: %s" % outputDataLine
        return outputDataLine

    def getMsgStr(self):
        return "compliance"

class ResponsibleParser(DbFileLoader):
    '''Holds functionality for parsing the responsible data and updating the Db'''

    def __init__(self, fileDir):
        DbFileLoader.__init__(self, fileDir, "regr_responsibility.csv", "regr_responsibility.sql", "regr_responsibility")
        self.deleteExistingRecords = True
        self.developersQuerySet = Developer.objects.all()

    def checkDeveloper(self, devName, devTeam):
        try:
            dev = self.developersQuerySet.get(username=devName)
            # OK developer returned ok
            return True
        except Developer.DoesNotExist:
            # Add a new developer
            newDeveloper = Developer()
            newDeveloper.populateBasicDetails(devName, devTeam)
            print "Adding new developer: %s for team: %s" % (devName, devTeam)
            newDeveloper.save()

    def generateDataRecord(self, dataLine):
        (package, function, team, primary, secondary, area) = [x.strip() for x in dataLine.split(',')][:6]
        # We must ensure that the developer with the given username exists in the Db prior to adding the responsible record
        self.checkDeveloper(primary, team)
        self.checkDeveloper(secondary, team)
        outputDataLine = "null, '%s', '%s', '%s', '%s', '%s', '%s'" % (package, function, team, primary, secondary, area)
        return outputDataLine

    def getMsgStr(self):
        return "responsible records"

class RegressionResultsParser(DbFileLoader):
    '''Holds functionality for parsing the regression result data and updating the Db'''

    def __init__(self, fileDir, release_id, statusTotals, sourceDataFile, laterProcessingLines, newFileObjectsToCreate, dbTableCache):
        DbFileLoader.__init__(self, fileDir, sourceDataFile.filename, "imp_%s_reg_result.sql" % sourceDataFile.getPackage(), "regr_regressionresult")
        self.developersQuerySet = Developer.objects.all()
        self.release_id = release_id
        self.statusTotals  = statusTotals
        self.sourceDataFile = sourceDataFile
        self.laterProcessingLines = laterProcessingLines
        self.dbTableCache = dbTableCache
        self.newFileObjectsToCreate = newFileObjectsToCreate
        self.instanceCountHash = {}
        self.disableStatsForReprocess = False

    def resetForSecondParse(self, dbTableCache):
        self.laterProcessingLines = []
        self.newFileObjectsToCreate = []
        self.dbTableCache = dbTableCache
        self.disableStatsForReprocess = True

    def convertDurationStr(self, durationStr):
      seconds = float(durationStr)
      m, s = divmod(seconds, 60)
      h, m = divmod(m, 60)
      return "'%d,%d,%.1f'" % (h, m, s)

    def convertTimeStr(self, timeStr):
        '''Converts a time str of the format: hh:mm:ss to hhmmss'''
        return "'%s'" % (timeStr.replace(':',''))

    def generateDataRecord(self, dataLine):
         # RetrieveDistributionForRamp/DistributionRequestForRamp.Case_001.scn,OK,7.1,01:23:55\n
        (cfFileName, cfStatus, cfDurationStr, cfStartTimeStr) = dataLine.split(',')[:4]
        justDirName = os.path.dirname(cfFileName)
        justFileName = os.path.basename(cfFileName)
        # Check for an existing file results
        try:
            val = self.instanceCountHash[cfFileName]
            print "-- reg res: %s of time %s already entered in hash, orig time: %s" % (cfFile, val, cfStartTimeStr)
        except:
            self.instanceCountHash[cfFileName] = cfStartTimeStr
        # Update totals
        if not self.disableStatsForReprocess:
          self.statusTotals.updateTotals(cfStatus)
        # check if this file already exist in the db
        recordId = self.dbTableCache.getRecordId(self.sourceDataFile.getLayer(), justDirName, justFileName)
        if recordId != -1:
            # generate regression result
            outputDataLine = "null, %s, %s, %s, 0, null, null, null, null, %s, %s" % (self.release_id, recordId, str(self.statusTotals.getNumericValue(cfStatus)), self.convertDurationStr(cfDurationStr), self.convertTimeStr(cfStartTimeStr))
            return outputDataLine
        else:
            # need to store this record for later processing, add it as a tuple
            self.newFileObjectsToCreate.append((justDirName, justFileName))
            self.laterProcessingLines.append(dataLine)
        return None

    def getMsgStr(self):
        return "regression result records"

class RegressionFileParser(DbFileLoader):
    '''Holds functionality for parsing the regression file data and updating the Db'''

    def __init__(self, fileDir, sourceBaseId, sourceDataFile, dbTableCache):
        DbFileLoader.__init__(self, fileDir, sourceDataFile.filename, "imp_%s_reg_file.sql" % sourceDataFile.getPackage(), "regr_regressionfile")
        self.developersQuerySet = Developer.objects.all()
        self.sourceBaseId = sourceBaseId
        self.sourceDataFile = sourceDataFile
        self.dbTableCache = dbTableCache
        self.instanceCountHash = {}

    def generateDataRecord(self, dataLine):
        assert isinstance(dataLine, tuple) == True

        (directory, filename) = dataLine
        key = os.sep.join([directory, filename])
        # check for existing file entry
        try:
            val = self.instanceCountHash[key]
            print "-- file: %s already exists" % (key)
        except:
            self.instanceCountHash[key] = 0

        outputDataLine = "null, %s, '%s', '%s', '%s', '%s'" % (self.sourceBaseId, self.sourceDataFile.getPackage(), self.sourceDataFile.getLayer(), directory, filename)

        return outputDataLine

    def getMsgStr(self):
        return "regression file records"

###############################################################################
def updateReleaseRecordWithStats(oRelease, statusTotals):
    oRelease.total_files = statusTotals.total_count
    oRelease.total_pass  = statusTotals.total_pass
    oRelease.total_fail  = statusTotals.total_fail
    oRelease.total_void  = statusTotals.total_void
    oRelease.total_new   = statusTotals.total_new
    oRelease.total_other = statusTotals.total_other
    oRelease.save()


###
# Main method
#
def main(fileDir):
    (fProjectStr, fBranchStr, fReleaseStr) = fileDir.split(".")

    ###
    # read the version.txt file
    #
    versionFile=os.sep.join([fileDir, 'version.txt'])
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
    # Obtain any still running details
    # and update the release object
    #

    running_str = ""
    running_list = []
    still_running_file_name = "still_running.txt"
    if os.path.isfile(still_running_file_name):
      still_running_file = open(still_running_file_name)
      for srLine in still_running_file:
        running_list.append(srLine.rstrip())
      still_running_file.close()
      if len(running_list) > 0:
        running_str = ", ".join(running_list)

    ###
    # Obtain the code base record
    #
    code_base_id = -1
    try:
        oCodeBase = CodeBase.objects.get(project=fProjectStr, branch=fBranchStr)
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
        print >> sys.stderr, "Warning this release is already loaded, exiting..."
        sys.exit(0)
    except Release.DoesNotExist:
        timestring = releaseDate.replace(" UTC", "")
        time_format = "%Y-%m-%d %H:%M:%S"
        rel_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timestring, time_format)))
        oRelease = Release(code_base=oCodeBase, name=releaseVersion, date=rel_date)
        oRelease.initialise_counters()
        if not NO_SAVE:
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
        dbutil = DatabaseUtil(fileDir, sourceDataFile, code_base_id)
        dbTableCache = dbutil.readInDatabaseTableCache() # This is the regressionfile cache for the current package

        # Now read the data file, it should contain the name and status
        # The file can potentially be empty
        #f = open("fm.DEV.25-0-219/fm.nglddrgr.xml.DEV.data")
        laterProcessingLines = []
        newFileObjectsToCreate = []
        regressionResultsParser = RegressionResultsParser(None, release_id, statusTotals, sourceDataFile, laterProcessingLines, newFileObjectsToCreate, dbTableCache)
        # Processed all the lines from the current datafile.
        regressionResultsParser.processData()

        # Now save the new regression files
        regFileParser = RegressionFileParser(None, code_base_id, sourceDataFile, dbTableCache)
        regFileParser.processData(newFileObjectsToCreate)
        dbutil.loadRegressionFileData(regFileParser, False)

        #print "File data saved, now updating regression results"
        # Update the cache now that the Db has been updated
        dbTableCache = dbutil.readInDatabaseTableCache(False)

        # reprocess the regression results which we could not before
        # now process the saved lines
        regressionResultsParser.resetForSecondParse(dbTableCache)
        regressionResultsParser.processData(laterProcessingLines)

        # Now save the new regression result records
        dbutil.loadRegressionResultData(regressionResultsParser, False)



    # #
    # Update the release object with the still running details if any present
    if os.path.isfile(still_running_file_name) and len(running_list) > 0:
      oRelease.comment = "Pkgs: " + running_str  + " are still running."

    # Right all files processed
    print "Processed files, Totals: %s" % (statusTotals)

    # Update the release record
    updateReleaseRecordWithStats(oRelease, statusTotals)

    # Process and Load the package sync data for the server logs functionality
    dbutil.loadPackageSyncData(None, release_id)

    # Process and Load the complinace data if present
    # Check for the presence of the compliance file to determine if we should process it or not
    compliance_file = "compliance.csv"
    if os.path.isfile(compliance_file):
      dbutil.loadComplianceData(None, release_id)

    print "done"

def processCmdLineOpts():
    '''Process the command line parameters'''
    global cpReleaseNumber
    global cpVerbose
    global cpCompliance
    global cpPackage
    global cpResponsible
    global cpDelete
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvc:prd", ["help", "compliance=", "package=", "responsible", "delete"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(1)
    for o, a in opts:
        if o == "-v":
            cpVerbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-c", "--compliance"):
            cpCompliance = True
            cpReleaseNumber = a
        elif o in ("-p", "--package"):
            cpPackage = True
            cpReleaseNumber = a
        elif o in ("-r", "--responsible"):
            cpResponsible = True
        elif o in ("-d", "--delete"):
            cpDelete = True
        else:
            assert False, "unhandled option"

    if cpCompliance or cpPackage or cpResponsible or cpDelete:
      if len(args) == 0:
        print usage()
        sys.exit(1)

    global cpFileDir
    cpFileDir = args[0]
    if not cpDelete:
      if not os.path.isdir(cpFileDir):
        print >> sys.stderr, "Error: The given dir: %s does not exist." % cpFileDir
        sys.exit(1)


# Globals:
cpVerbose = False
cpCompliance = False
cpPackage = False
cpResponsible = False
cpReleaseNumber = -1
cpDelete = False

if __name__ == "__main__":

    processCmdLineOpts()

    if cpCompliance:
      print "Loading Package compliance data for release: %s ..." % cpReleaseNumber
      dbutil = DatabaseUtil(cpFileDir, None, None)
      dbutil.loadComplianceData(cpFileDir, cpReleaseNumber)
    elif cpPackage:
      print "Loading Package synchro data for release: %s ..." % cpReleaseNumber
      dbutil = DatabaseUtil(cpFileDir, None, None)
      dbutil.loadPackageSyncData(cpFileDir, cpReleaseNumber)
    elif cpResponsible:
      print "Loading responsible data..."
      dbutil = DatabaseUtil(None, None, None)
      dbutil.loadResponsibleData()
    elif cpDelete:
      (fProjectStr, fBranchStr, fReleaseStr) = cpFileDir.split(".")
      print "Deleting release: %s/%s/%s ..." % (fProjectStr, fBranchStr, fReleaseStr)

      # retrieve the code base id
      try:
          oCodeBase = CodeBase.objects.get(project=fProjectStr, branch=fBranchStr)
          code_base_id = oCodeBase.id
      except CodeBase.DoesNotExist:
          print >> sys.stderr, "Project not found"
          sys.exit(1)
      try:
          oRelease = Release.objects.get(code_base=code_base_id, name=fReleaseStr)
          release_id = oRelease.id
      except Release.DoesNotExist:
          print >> sys.stderr, "Release not found"
          sys.exit(1)
      dbutil = DatabaseUtil(cpFileDir, None, None)
      dbutil.removeReleaseRecords(release_id)
    else:
      print "loading data for release: %s ..." % cpFileDir
      main(cpFileDir)
