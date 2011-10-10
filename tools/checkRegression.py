#!/data/softs/bin/python
# @name checkRegression.py
# @usage checkRegression.py -r 27-0-869
# @description Check the regression run across all of the machine. It allows you to see which packages have not run
# @author bklair
# @date 14/09/11

import datetime
import os
import re
import getopt, sys
import glob

def parseDataline(pDate, pBranch, pRelease, useArchieve=False):
    '''Parsing the following line format:
    ngdfmbld@lonlnx27 Wed 2011-09-14 10:04:03 UTC INFO [tst:DEV:27-0-869:regression:ngwwwrgr:edi] ...
    from file: /projects/ngdfmbld/queues/xtest/SUMMARY.LOG
    Note that the date filtering has been removed since some tests can span days
    '''
    
    #print "Process file with  options: %s %s %s" % (pDate, pBranch, pRelease)
    dataHash = {}
    #linePattern = re.compile("\w+@(?P<host>lonlnx\d+)\s+\w+\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+\:\d+\:\d+)\s+\w+\s+\w+\s*")
    linePattern = re.compile("\w+@(?P<host>lonlnx\d+)\s+\w+\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+\:\d+\:\d+)\s+\w+\s+\w+\s*\[\w+\:(?P<branch>[\w\-_\d]+)\:(?P<release>[\w\-+]+)\:regression\:(?P<package>\w+)\:(?P<layer>\w+)\]\s+(?P<text>.*)")
    linePattern2 = re.compile("\w+@(?P<host>lonlnx\d+)\s+\w+\s+(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+\:\d+\:\d+)\s+\w+\s+\w+\s*\[\w+\:(?P<branch>[\w\-_\d]+)\:(?P<release>[\w\-+]+)\:regression\:(?P<package>\w*)\:(?P<layer>\w*)\:?\]\s+(?P<text>.*)")

    startPattern = re.compile("\s*running\s+\"regression\"\s+tests\s+for\s+")
    "-> requesting regression tests on xtest queue for nglddrgr (edi) module"
    startPattern2 = re.compile("\s*->\s+requesting\s+regression\s+tests\s+on\s+xtest\s+queue\s+for\s+(?P<text_pkg>\w+)\s+\((?P<text_layer>\w+)\)\s+module")
    endPattern = re.compile("\s*->\s+task\s+successful")

    if not useArchieve:
        dataFile = open("/projects/ngdfmbld/queues/xtest/SUMMARY.LOG")
    else:
        # Archieve file format: SUMMARY.2011-09-29-04:29:02-UTC.LOG
        summary_files = glob.glob("/projects/ngdfmbld/queues/xtest/HISTORY/SUMMARY.%s*.LOG" % pDate)
        if len(summary_files) == 0:
            return {}
        dataFile = open(summary_files[0])
        
    for fileLine in dataFile:
        match = linePattern.match(fileLine)
        if match is not None:
            if match.group('branch') == pBranch and match.group('release') == pRelease:
                logText = match.group('text')
                
                key = "%s.%s" % (match.group('package'), match.group('layer'))
                if key in dataHash.keys():
                    detailsHash = dataHash[key]
                else:
                    detailsHash = {}
                    dataHash[key] = detailsHash
                    
                startMatch = startPattern.match(logText)
                if startMatch is not None:
                    detailsHash['start_time'] = match.group('time')
                    detailsHash['start_date'] = match.group('date')
                    detailsHash['host']       = match.group('host')
                    
                endMatch = endPattern.match(logText)
                if endMatch is not None:
                    detailsHash['end_time'] = match.group('time')
                    detailsHash['end_date'] = match.group('date')
                    detailsHash['host']       = match.group('host')
        else:
            match = linePattern2.match(fileLine)
            if match is not None:

                # Match the branch release
                if match.group('branch') == pBranch and match.group('release') == pRelease:

                    logText = match.group('text')
                    detailsHash = {}

                    startMatch = startPattern2.match(logText)
                    if startMatch is not None:
                        detailsHash['start_time'] = match.group('time')
                        detailsHash['start_date'] = match.group('date')
                        # This value is not accurate, it is the actioning server and not the running server, we should replace this
                        detailsHash['host']       = match.group('host')
                        key = "%s.%s" %(startMatch.group('text_pkg'), startMatch.group('text_layer'))
                        
                        if key in dataHash.keys():
                            newDetailsHash = dataHash(key).items() + detailsHash.items()
                            dataHash[key] = newDetailsHash
                        else:
                            dataHash[key] = detailsHash
                        
    dataFile.close()
    # If we did not parse any data then perhaps the file was archieved, so rerun with the archieve file
    if not useArchieve and len(dataHash.keys()) == 0:
        return parseDataline(cpDate, cpBranch, cpRelease, True)
    return dataHash

def printDataFigures(pDate, pBranch, pRelease, dataHash):
    '''Format out the details that we have collected'''
    if not cpSilent:
        print "Regression details for branch: %s, release: %s on date: %s" % (pBranch, pRelease, pDate)
    if dataHash:
        for key, detailsHash in dataHash.items():
            sTime = "?"
            eTime = "?"
            sDate = "?"
            eDate = "?"
            host = "?"
            if 'host' in detailsHash.keys():
                host = detailsHash['host']
            if 'start_time' in detailsHash.keys():
                sTime = detailsHash['start_time']
            if 'start_date' in detailsHash.keys():
                sDate = detailsHash['start_date']
            if 'end_date' in detailsHash.keys():
                eDate = detailsHash['end_date']
            if 'end_time' in detailsHash.keys():
                eTime = detailsHash['end_time']
            
            print "%-15s run on host: %-10s from %-10s %-8s to %-10s %-8s" % (key, host, sDate, sTime, eDate, eTime)
    
def isTimeToBeIgnored(timeObj, filterTimeObj):
    '''Returns a boolean to indicate if the timeObj is less than the filter time'''
    if filterTimeObj is not None:
        return timeObj < filterTimeObj
    return False

def getTimeObjFromStr(timeStr):
    '''Returns a time object given the time str of the format: hh:mm'''
    timeComps = timeStr.split(":")
    return datetime.time(int(timeComps[0]), int(timeComps[1]))

def usage():
    '''Display usage text'''
    print "checkRegression.py [-v -h] -d <date> -t <time> -f <file> -p <package> -m <machine>"

def processCmdLineOpts():
    '''Process the command line parameters'''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvsb:p:d:t:u:r:m:", ["help", "branch=", "package=", "date=", "time=", "user=", "release=", "machine="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(1)
    for o, a in opts:
        if o == "-v":
            global cpVerbose
            cpVerbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o == "-s":
            global cpSilent
            cpSilent = True
        elif o in ("-p", "--package"):
            global cpPackage
            cpPackage = a
        elif o in ("-b", "--branch"):
            global cpBranch
            cpBranch = a
        elif o in ("-d", "--date"):
            global cpDate
            cpDate = a
        elif o in ("-t", "--time"):
            global cpTime
            cpTime = a
        elif o in ("-u", "--user"):
            global cpUser
            cpUser = a
        elif o in ("-r", "--release"):
            global cpRelease
            cpRelease = a           
        elif o in ("-m", "--machine"):
            global cpMachine
            cpMachine = a
        else:
            assert False, "unhandled option"

def getRecommendedRelease():
    f = open("/projects/ngdfmbld/status/%s/recommended"%cpBranch)
    line = f.read()
    if line is not None and len(line) > 0:
        global cpRelease
        cpRelease = line.strip()
    f.close()
    
if __name__ == "__main__":
    global cpDate
    global cpRelease
    global cpSilent
    cpSilent = None
    cpRelease = None
    cpDate = None
    global cpBranch
    cpBranch = "DEV"
    processCmdLineOpts()

    if cpDate is None:
        now = datetime.datetime.now()
        cpDate = now.strftime("%Y-%m-%d")

    if cpRelease is None:
        getRecommendedRelease()
        if not cpSilent:
            print "Release not supplied, defaulting to recommended: %s" % cpRelease

    dataHash = parseDataline(cpDate, cpBranch, cpRelease)
    printDataFigures(cpDate, cpBranch, cpRelease, dataHash)
    
