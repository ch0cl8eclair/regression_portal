import django
from regr.models import Developer
import urllib2
import urllib
import anyjson

'''
Updates the regr_developer table with the user details from the OCR system.
The username from the Db is used to id the user from the OCR data and the user's name, surname and email are updated.
Any users in the Db which are not listed in the OCR data are output as errors.
'''

USE_FILE = 1
RETRIEVE_TEAM_DETAILS_URL = 'http://gcnet.nce.amadeus.net/application/poc/api/json/team/%s/users/'

TEAM_GROUP_MAP = {
  'FMW' : 'DEV-ASL-GCD-FMG-FMW',
  'FMF' : 'DEV-ASL-GCD-FMG-FMF',
  'FMD' : 'DEV-ASL-GCD-FLI-FMD',
}

def getOCRTeamData(team):
    '''Reads the team data json values either from a file or url
    @param team - the 3 letter team code'''

    data_hash = None
    if USE_FILE :
        with open('%s.json' % team, 'r') as f:
            json_text = f.read()
    else:
        full_team_name = TEAM_GROUP_MAP[team]
        json_url = RETRIEVE_TEAM_DETAILS_URL % full_team_name
        try:
            with urllib2.urlopen(json_url) as u:
                json_text = u.read()
        except URLError, e:
            print e.reason
            return None
    data_hash = anyjson.deserialize(json_text)
    return data_hash

# A cache of the team json data
json_data_cache = {}

def getTeamData(team):
    '''Returns the data for the given team from a cache, if the data is not found in the cache then the cache is updated
    @param team - the 3 letter team code'''

    team_uc = team.upper()
    if team_uc in json_data_cache.keys():
        return json_data_cache[team_uc]
    else:
        try:
            data = getOCRTeamData(team_uc)
        except IOError:
            print "Failed to get data for team: %s" % team
            data = None
        if data is not None:
            json_data_cache[team_uc] = data
        return data
    return None

def updateDeveloperDetails(developer, data_firstname, data_surname, data_email):
    '''Updates the developer object with the given parameters and saves the object if needed
    @param developer - developer model object
    @param data_firsname - json firstname value
    @param data_surname - json surname value
    @param data_email - json email value'''

    if (developer.firstname != data_firstname or developer.surname != data_surname or developer.email != data_email):
        developer.firstname = data_firstname
        developer.surname = data_surname
        developer.email = data_email
        print "Updating developer: %s" % developer.firstname
        developer.save()

####################################
# Main
#
print "beginning"
developers = None
try:
    developers = Developer.objects.all()
except Developer.DoesNotExist:
    print "failed to find any developers to update"
    sys.exit()

for developer in developers:
  username = developer.username
  firstInitial = username[0].lower()
  surname = username[1:].lower()
  team = developer.team
  print "processing db user: %s from team: %s" % (username, team)

  developer_data = getTeamData(team)
  # Check that the team exists
  if developer_data is None:
    print "Failed to get developer details for team: %s" % team
    # TODO should we add in dummy data to ensure data integrity
    continue

  processed_developer = False
  for people in developer_data['people']:
    dd_lastname = str(people['last_name']).lower()
    dd_firstname = str(people['first_name']).lower()

    if dd_lastname.startswith(surname) and dd_firstname.startswith(firstInitial):
        processed_developer = True
        data_firstname = dd_firstname.capitalize()
        data_surname   = dd_lastname.capitalize()
        data_email     = str(people['internet_address'])
        updateDeveloperDetails(developer, data_firstname, data_surname, data_email)

  if not processed_developer:
    print "Failed to process user: %s" % username
print "done"
