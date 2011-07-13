from converttocsv import *
import unittest

class SourceDataFileTest(unittest.TestCase):
    def testBasic(self):
        """test basic case with a typical input"""
        sdf = SourceDataFile("fm.ngcp4rgr.edi.DEV.data")
        self.assertEqual("fm", sdf.getProject())
        self.assertEqual("ngcp4rgr", sdf.getPackage())
        self.assertEqual("edi", sdf.getLayer())
        self.assertEqual("DEV", sdf.getBranch())

class StatusTotalsTest(unittest.TestCase):
    def testInitialisation(self):
        """test initialisation values"""
        statsClass = StatusTotals()
        self.assertEqual(0, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
        self.assertEqual(0, statsClass.getTotalVoid())
        self.assertEqual(0, statsClass.getTotalNew())
        self.assertEqual(0, statsClass.getTotalOther())
    def testUpdateOK(self):
        """test update functionality with OK status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("OK")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(1, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
    def testUpdateFailed(self):
        """test update functionality with failed status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("Failed")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(1, statsClass.getTotalFail())
    def testUpdateVoid(self):
        """test update functionality with void status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("Void")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
        self.assertEqual(1, statsClass.getTotalVoid())
    def testUpdateNew(self):
        """test update functionality with new status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("New")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
        self.assertEqual(0, statsClass.getTotalVoid())
        self.assertEqual(1, statsClass.getTotalNew())
    def testUpdateBadInput(self):
        """test update functionality with bad or other status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("dumped")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
        self.assertEqual(0, statsClass.getTotalVoid())
        self.assertEqual(0, statsClass.getTotalNew())
        self.assertEqual(1, statsClass.getTotalOther())
    def testUpdateOKLowerCase(self):
        """test update functionality with lowercase OK status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("ok")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
        self.assertEqual(1, statsClass.getTotalOther())
    def testUpdateFailedLowerCase(self):
        """test update functionality with lowercase failed status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("failed")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
        self.assertEqual(1, statsClass.getTotalOther())
    def testUpdateFailedUpperCase(self):
        """test update functionality with upppercase failed status"""
        statsClass = StatusTotals()
        statsClass.updateTotals("FAILED")
        self.assertEqual(1, statsClass.getTotalCount())
        self.assertEqual(0, statsClass.getTotalPass())
        self.assertEqual(0, statsClass.getTotalFail())
        self.assertEqual(1, statsClass.getTotalOther())
    def testUpdateAccumulative(self):
        """test update functionality multiple updates"""
        statsClass = StatusTotals()
        statsClass.updateTotals("OK")
        statsClass.updateTotals("OK")
        statsClass.updateTotals("OK")
        statsClass.updateTotals("Failed")
        statsClass.updateTotals("Failed")
        statsClass.updateTotals("Void")
        statsClass.updateTotals("Void")
        statsClass.updateTotals("Void")
        statsClass.updateTotals("New")
        statsClass.updateTotals("Dumped")
        statsClass.updateTotals("OK")
        statsClass.updateTotals("Failed")
        self.assertEqual(12, statsClass.getTotalCount())
        self.assertEqual(4, statsClass.getTotalPass())
        self.assertEqual(3, statsClass.getTotalFail())
        self.assertEqual(3, statsClass.getTotalVoid())
        self.assertEqual(1, statsClass.getTotalNew())
        self.assertEqual(1, statsClass.getTotalOther())
    def testGetNumericValue(self):
        """test method to convert a string to a number"""
        statsClass = StatusTotals()
        self.assertEqual(0, statsClass.getNumericValue("OK"))
        self.assertEqual(1, statsClass.getNumericValue("Failed"))
        self.assertEqual(2, statsClass.getNumericValue("Void"))
        self.assertEqual(3, statsClass.getNumericValue("New"))
        self.assertEqual(4, statsClass.getNumericValue("Dumped"))
        self.assertEqual(4, statsClass.getNumericValue("aaa"))
        self.assertEqual(4, statsClass.getNumericValue("ok"))
        self.assertEqual(4, statsClass.getNumericValue("failed"))
    def testGetStatusStr(self):
        """test method to convert number to a string"""
        statsClass = StatusTotals()
        self.assertEquals("OK", statsClass.getStatusStr(0))
        self.assertEquals("Failed", statsClass.getStatusStr(1))
        self.assertEquals("Void", statsClass.getStatusStr(2))
        self.assertEquals("New", statsClass.getStatusStr(3))
        self.assertEquals("Unknown", statsClass.getStatusStr(4))
        self.assertEquals("Unknown", statsClass.getStatusStr(5))
        
class DatabaseTableCacheTest(unittest.TestCase):
    file_name = "dbcachetest.data"
    file_data = """edi|ACTIVITIES|Activity_ADP.Case_002.scn|14339
edi|ACTIVITIES|Activity_ATO.Case_002.scn|14340
edi|ACTIVITIES|Activity_BGD.Case_002.scn|14341
edi|ACTIVITIES|Activity_CCA.Case_002.scn|14342
edi|ACTIVITIES|Activity_CCD.Case_002.scn|14343
edi|ACTIVITIES|Activity_CCP.Case_002.scn|14344
edi|ACTIVITIES|Activity_CDI.Case_002.scn|14345
edi|ACTIVITIES|Activity_CEC.Case_002.scn|14346
edi|ACTIVITIES|Activity_CFF.Case_002.scn|14347
edi|ACTIVITIES|Activity_CGO.Case_002.scn|14348
edi|ACTIVITIES|Activity_CLD.Case_002.scn|14349
edi|ACTIVITIES|Activity_CLP.Case_002.scn|14350
edi|ACTIVITIES|Activity_CPM.Case_002.scn|14351
edi|ACTIVITIES|Activity_DGA.Case_002.scn|14352
"""
    def createDataFile(self):
        """create the test data file to be loaded"""
        f = file(DatabaseTableCacheTest.file_name, "w")
        f.write(DatabaseTableCacheTest.file_data)
        f.close()
        
    def testInitialisation(self):
        """test basic initialisation and retrieval for cache class"""
        self.createDataFile()
        dbTableCase = DatabaseTableCache(DatabaseTableCacheTest.file_name)
        self.assertEqual("14339", dbTableCase.getRecordId("edi", "ACTIVITIES", "Activity_ADP.Case_002.scn"))
        self.assertEqual("14340", dbTableCase.getRecordId("edi", "ACTIVITIES", "Activity_ATO.Case_002.scn"))
        self.assertEqual("14341", dbTableCase.getRecordId("edi", "ACTIVITIES", "Activity_BGD.Case_002.scn"))
        self.assertEqual("14342", dbTableCase.getRecordId("edi", "ACTIVITIES", "Activity_CCA.Case_002.scn"))
        self.assertEqual(-1, dbTableCase.getRecordId("edi", "ACTIVITIES", "Activity_CCA.Case_009.scn"))

class DatabaseUtilTest(unittest.TestCase):
    def testInitialisation(self):
        """test initialisation"""
        sdf = SourceDataFile("fm.ngcp4rgr.edi.DEV.data")
        dbutil = DatabaseUtil(sdf, 1)
        self.assertEqual(1, dbutil.sourceBaseId)
        self.assertEqual(0, len(dbutil.newRegressionFileRecords))
        self.assertEqual(0, len(dbutil.newRegressionResultRecords))
        # we could also test __generateCommandFile__ to ensure that the string is correctly output to the file
        expectedStr = '''.mode list
.separator |
.output exp_ngcp4rgr_reg_file.csv
select layer, directory_path, file_name, id from regr_regressionfile where code_base_id = 1 and package = "ngcp4rgr";
.exit
'''
        self.assertEqual(expectedStr, dbutil.__getRegressionFileExportCommands__())

    def testGetFileNameMethods(self):
        """ensure that the generated file names are correct"""
        sdf = SourceDataFile("fm.ngcp4rgr.edi.DEV.data")
        dbutil = DatabaseUtil(sdf, 1)
        self.assertEqual("get_ngcp4rgr_data.sql", dbutil.__getSqlCommandFile__())
        self.assertEqual("exp_ngcp4rgr_reg_file.csv", dbutil.__getExportFile__())
        self.assertEqual("imp_ngcp4rgr_reg_file.csv", dbutil.__getCsvRegressionFileImportFile__())
        self.assertEqual("imp_ngcp4rgr_reg_file.sql", dbutil.__getSqlRegressionFileImportFile__())        
        self.assertEqual("imp_ngcp4rgr_reg_result.csv", dbutil.__getCsvRegressionResultImportFile__())
        self.assertEqual("imp_ngcp4rgr_reg_result.sql", dbutil.__getSqlRegressionResultImportFile__())
    
    def testConvertBoolForDb(self):
        """test convert bool to string function"""
        sdf = SourceDataFile("fm.ngcp4rgr.edi.DEV.data")
        dbutil = DatabaseUtil(sdf, 1)
        self.assertEqual("1", dbutil.convertBoolForDb(True))
        self.assertEqual("0", dbutil.convertBoolForDb(False))
        
    def testAddNewRegressionFileRecord(self):
        """test the add new regression file method"""
        sdf = SourceDataFile("fm.ngcp4rgr.edi.DEV.data")
        dbutil = DatabaseUtil(sdf, 1)
        self.assertEqual(0, len(dbutil.newRegressionFileRecords))
        dbutil.addNewRegressionFileRecord("ACTIVITIES", "Activity_CCA.Case_011.scn")
        self.assertEqual(1, len(dbutil.newRegressionFileRecords))
        self.assertEqual("null, 1, 'ngcp4rgr', 'edi', 'ACTIVITIES', 'Activity_CCA.Case_011.scn'", dbutil.newRegressionFileRecords[0])
        # now add another record to test the file write
        dbutil.addNewRegressionFileRecord("ACTIVITIES", "Activity_CCA.Case_012.scn")
        self.assertEqual(2, len(dbutil.newRegressionFileRecords))
        test_file_name = "test_file_recs.sql"
        dbutil.__writeRecordsToFileAsSql__(test_file_name, "regr_regressionfile", dbutil.newRegressionFileRecords)
        f = file(test_file_name)
        file_line1 = f.readline()
        self.assertEqual("INSERT INTO regr_regressionfile VALUES( null, 1, 'ngcp4rgr', 'edi', 'ACTIVITIES', 'Activity_CCA.Case_011.scn' );\n", file_line1)
        file_line2 = f.readline()
        self.assertEqual("INSERT INTO regr_regressionfile VALUES( null, 1, 'ngcp4rgr', 'edi', 'ACTIVITIES', 'Activity_CCA.Case_012.scn' );\n", file_line2)
        f.close()

        
    def testAddNewRegressionResultRecord(self):
        """test the add new regression result method"""
        sdf = SourceDataFile("fm.ngcp4rgr.edi.DEV.data")
        dbutil = DatabaseUtil(sdf, 1)
        self.assertEqual(0, len(dbutil.newRegressionResultRecords))
        dbutil.addNewRegressionResultRecord(1, 2, 0)
        self.assertEqual(1, len(dbutil.newRegressionResultRecords))
        self.assertEqual("null, 1, 2, 0, 0, null, null, null", dbutil.newRegressionResultRecords[0])
        
if __name__ == "__main__":
    unittest.main()