#!/data/softs/bin/python

syncFileName = "package_synchro.txt"
sqlFileName = "synchro.sql"
release_id = 12
syncTableName = "regr_packagesynchro"

def generateSQL(tablename, records):
    '''Generates an sql file from the given data'''
    sqlFile = open(sqlFileName, 'w')
    sqlFile.write("BEGIN TRANSACTION;\n")
    for record in records:
        recStr = "INSERT INTO %s VALUES( %s );\n" % (tablename, record)
        sqlFile.write(recStr)
    sqlFile.write("END;\n")
    sqlFile.close()
    
def setDateTimeValue(dataStr):
    '''Converts the string value into a Db compatible form'''
    if dataStr is None or dataStr == "?":
        return "null"
    dataStr = dataStr.replace('-','')
    dataStr = dataStr.replace(':','')
    return "'%s'" % dataStr


# the line formats can be of the following forms
# ngfuergr.edi    run on host: lonlnx30   from 2011-09-20 21:41:02 to 2011-09-20 22:20:02
# ngcmsrgr.edi    run on host: lonlnx27   from 2011-09-20 23:05:03 to ?          ?
cf = open(syncFileName)
newRecordLines = []
for cfLine in cf:
    line_values_list = cfLine.split()
    (package,layer) = line_values_list[0].split(".")[:2]
    host = line_values_list[4]
    start_date = setDateTimeValue(line_values_list[6])
    start_time = setDateTimeValue(line_values_list[7])
    end_date = setDateTimeValue(line_values_list[9])
    end_time = setDateTimeValue(line_values_list[10])

    outputDataLine = "null, %d, '%s', '%s', '%s', %s, %s, %s, %s" % (release_id, package, layer, host, start_date, start_time, end_date, end_time)
    newRecordLines.append(outputDataLine)

generateSQL(syncTableName, newRecordLines)
