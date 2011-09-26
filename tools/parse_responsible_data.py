#!/data/softs/bin/python
# @name parse_responsible_data.py
# @usage parse_responsible_data.py [-r -t]
# @description Prints out the responsible data from the latest DEV release
# @author bklair
# @date 30/06/11

import os.path
from os import sep
import sys
import glob
import re
import subprocess
import getopt

USAGE="parse_responsible_data.py"
PRINT_TEAMS=0
PRINT_RESPONSIBLE=0
DEBUG=0
BRANCH="DEV"

def runCommand():
    """Run the following shell command to determine the latest release
    `ls -tr /projects/ngdfmbld/htdocs/$BRANCH | grep -E '^[-0-9]*$' | tail -1`
    """
    myprocess1 = subprocess.Popen(['ls','-tr', '/projects/ngdfmbld/htdocs/' + BRANCH ], stdout=subprocess.PIPE)
    myprocess2 = subprocess.Popen(['grep', '-E', '^[-0-9]*$'], stdin=myprocess1.stdout, stdout=subprocess.PIPE)
    myprocess3 = subprocess.Popen(['tail', '-1'], stdin=myprocess2.stdout, stdout=subprocess.PIPE)
    myprocess1.stdout.close()
    myprocess2.stdout.close()
    (sout,serr) = myprocess3.communicate()
    outputStr = ""
    for line in sout.split('\n'):
        outputStr = outputStr + line
    myprocess3.wait()
    if myprocess3.returncode == 0:
        return outputStr.strip()
    return ""

def main():
    """This class gets and parses the responsible data from the latest release"""
    
    fileDir=os.sep.join(["", "vtmp", "ngdfmbld", BRANCH, runCommand(), "internal"])
    if not os.path.isdir(fileDir):
        print "Error: The given dir: %s does not exist." % fileDir
        sys.exit()

    # get the files
    os.chdir(fileDir)
    dataFiles = glob.glob("*/Messages.csv")

    # Iterate over the files

    dataLinePattern = re.compile("^\s*(?P<message>\w+)\s*,\s*(?P<primary>\w+)\s*,\s*(?P<secondary>\w+)\s*,\s*(?P<team>\w+)\s*,?\s*(?P<area>[A-Za-z0-9_ ]*)")

    teamsHash = {}
    for currentFile in dataFiles:
        try:
            f = open(currentFile, 'r')
            packageStr = os.path.dirname(f.name)
            if DEBUG:
                print "processing package: %s" % (packageStr)
            #if PRINT_RESPONSIBLE:
            #    print "--+ %s" % packageStr
            for line in f:
                match = dataLinePattern.match(line)
                if match is None:
                    continue
                teamStr = match.group('team')

                # Store team and user details in hash of sets
                membersSet = None
                if teamStr in teamsHash.keys():
                    membersSet = teamsHash[teamStr]
                else:
                    membersSet = set()
                    teamsHash[teamStr] = membersSet

                if PRINT_RESPONSIBLE:
		    print "%s, %s, %s, %s, %s, %s" % (packageStr, match.group('message'), match.group('team'), match.group('primary'), match.group('secondary'), match.group('area').strip())
                membersSet.add(match.group('primary'))
                membersSet.add(match.group('secondary'))
            f.close()
        except IOError:
            print "Failed to open file: %s\n" % currentFile

    if PRINT_TEAMS:	
        for key in teamsHash.keys():
            print "%s, %s" % (key, ", ".join(sorted(teamsHash[key])))
    if DEBUG:
        print "Done."

def usage():
    print "parse_responsible_data.py [-t | -r]"
    
def processCmdLineOpts():
    '''Process the command line parameters'''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hrt", ["help", "responsible", "teams"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(1)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        if o == "-t":
            global PRINT_TEAMS
            PRINT_TEAMS = 1
        if o == "-r":
            global PRINT_RESPONSIBLE
            PRINT_RESPONSIBLE = 1
    
    if PRINT_TEAMS == 0 and PRINT_RESPONSIBLE == 0:
        usage()
        sys.exit(1)
        
if __name__ == "__main__":
    processCmdLineOpts()
    main()
