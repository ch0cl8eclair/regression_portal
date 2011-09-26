import sys
import os
import converttocsv

class GenericDbCache:
    def __init__(self, exportFileName, commandFile, tableName):
        self.exportFileName = exportFileName
        self.commandFile = commandFile
        self.tablename = tablename
        self.cachedRecords = {}

    def exportDbData(self):
        '''Exports the given table from the Db to an csv file'''
        pass

    def __generateCommandFile__(self, filename):
        commandFile = open(filename, 'w')
        commandFile.write(self.__generateExportStatements__())
        commandFile.close()

    def __generateExportStatements__(self):
        '''Generates the commands needed to export the given table data from the db'''
        commandStr = '''.mode list
.separator |
.output %s
%s
.exit
''' % (self.commandFile, self.getSQLExportStatement())
        return commandStr

    def getSQLExportStatement(self):
        '''Defines the sql select statement which selects the data for the export'''
        return "select * from %s;" % self.tableName;

    def exportRegressionFileData(self, regenerateCmdFile=True):
        '''Exports the regression file data for a given package to a file'''

        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            sqllitefilename=settings.DATABASES["default"]["NAME"]

        # Generate the SQL export command file if required
        if regenerateCmdFile:
            self.createSqlCommandRegressionFile()

        # Now perform the export via an external process
        p1 = Popen(["cat", self.filename], stdout=PIPE)
        p2 = Popen(["sqlite3", sqllitefilename], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()
        output = p2.communicate()[1]
        if output is None:
            return True
        print >> sys.stderr, "error status of export was: %s" % output
        return False

    def parseExportFile(self):
        '''Parses the exported csv file into an internal list of record objects'''
        self.cachedRecords = {}
        dbFile = open(self.exportFileName)
        for recordLine in dbFile:
            self.parseRecordLine(recordLine.rstrip())
        dbFile.close()

    def parseRecordLine(self, recordLine):
        '''Parses a line of data from the exported db file'''
        pass

    def getRecord(self, *args, **kwargs):
        '''Gets the data that matches the given details'''
        pass

class DeveloperTableCache(GenericDbCache):
    def __init__(self):
        GenericDbCache(self, "pkgsync.csv", "pkgsync.sql", "regr_packagesynchro")

    def parseRecordLine(self, recordLine):
        (uname, uname2, firstname, surname, team, email) = recordLine.split('|')[:6]

class RegressionFileTableCache(GenericDbCache):
    def __init__(self, filename, commandFile, tablename):
        GenericDbCache(self, filename, commandFile, tablename)

    def parseRecordLine(self, recordLine):
        (recLayer, recDir, recFile, recId) = recordLine.split('|')[:4]
        recId = recId.replace("\n", "")
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
            print >> sys.stderr, "DatabaseTableCache failed to add entry %s " % recFile
        if self.cachedRecords[recLayer][recDir][recFile] != recId:
            print >> sys.stderr, "Failed to add entry: %s %s %s\n" % ",".join(recLayer, recDir, recFile)

    def getRecordId(self, layer, dir, file):
        '''Return the record id of the given file if it exits in the cache, -1 otherwise'''
        if self.cachedRecords is not None:
            try:
                return self.cachedRecords[layer][dir][file]
            except KeyError:
                return -1
        return -1

###
# Main
#
def main():
    # 1) Read in existing db developer data and use as cache
    # 2) Read in responsible data and create sql file
    # 3) Load any new developers, and update their details with json feed
    # 4) Load in new responsible data deleting the old data.
    fileDir = sys.argv[1];
    if not os.path.isdir(fileDir):
        print "Error: The given dir: %s does not exist." % fileDir
        sys.exit()
    dbutil = converttocsv.DatabaseUtil(fileDir, None, None)
    dbutil.loadResponsibleData()

    # call update dev details




if __name__ == "__main__":
    main()
