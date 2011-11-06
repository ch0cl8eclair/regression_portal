from regr.models import *
import sys
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from forms import *
from django.db.models import Q
from sets import Set
from regr.utils import RegressionRequestWrapper
from regr.utils import *
from regr.utils import getReleaseTotalStats
import re

DISPLAY_DEVELOPERS_HTML = 'vlistdevelopers.html'
DISPLAY_RESPONSIBILITY_HTML = 'vlistresponsibility.html'
SEARCH_MESSAGE_HTML = 'vmessagesearch.html'
SEARCH_USERMESSAGE_HTML = 'vusersearch.html'
RELEASE_USER_SUMMARY_HTML = 'vreleasesummary.html'

def display_team(request, team):
    '''Displays the developers belonging to the given team'''
    querySet = Developer.objects.filter(team__startswith=team)
    return render_to_response(DISPLAY_DEVELOPERS_HTML, {'object_list': querySet})

def display_developer(request, developer):
    '''Displays the Developer details matching the given username'''
    querySet = Developer.objects.filter(username__startswith=developer)
    return render_to_response(DISPLAY_DEVELOPERS_HTML, {'object_list': querySet})

def display_message(request, message):
    '''Displays the message responsibility data that matches the given msg'''
    querySet = Responsibility.objects.filter(function__startswith=message.upper())
    return render_to_response(DISPLAY_RESPONSIBILITY_HTML, {'object_list': querySet})

MSG_PATTERN = re.compile("\w{6}(_\d+)*")

def search_message(request):
    '''Searches for the supplied msg'''
    
    #message = request.GET.get('message', '')
    #selectedObjList = None
    errorMsg = None
    flagError = False
    selectedObjList = None
    message = ''
    
    if request.method == 'GET' and len(request.GET) > 0:
        form = MessageForm(request.GET)
        if form.is_valid():
            message = form.cleaned_data['message']
            qset = (
                Q(function__istartswith=message)
            )
            selectedObjList = Responsibility.objects.filter(qset)
    else:
        form = MessageForm(
                initial={'message': 'FDDLRQ'}
            )
    #         Message: <input type="text" name="message" value="{{ message|escape|default_if_none:"" }}"/><br />
    #return render_to_response(SEARCH_MESSAGE_HTML, {'message' : message, 'object_list': selectedObjList, 'form' : form})
    return render_to_response(SEARCH_MESSAGE_HTML, {'object_list': selectedObjList, 'form' : form})

USER_PATTERN = re.compile("[\w\d]{4,10}")

def search_user_message(request):
    '''Searches for the msgs for the given user'''
    selectedObjList = None
    user = None
    errorMsg = None
    flagError = False
    dev = None
    isPrimary = True

    try:
        user = request.GET['user']
        try:
          primaryStr = str(request.GET['isprimary'])
          isPrimary = (primaryStr.upper() == "TRUE")
        except (KeyError):
          isPrimary = True

        match = USER_PATTERN.match(user)
        if match is not None:
          try:
              dev = Developer.objects.get(username__exact=user)
          except (Developer.DoesNotExist):
              errorMsg = "User: '%s' does not exist" % user
              flagError = True
        else:
          errorMsg = "Invalid user name format: '%s'" % user
          flagError = True

        if isPrimary:
            selectedObjList = Responsibility.objects.filter(primary__exact=user)
        else:
            selectedObjList = Responsibility.objects.filter(secondary__exact=user)

    except (KeyError, Responsibility.DoesNotExist):
        if user is not None:
          flagError = True
          errorMsg = "Failed to find an messages for user: '%s'" % user

    if not flagError and user is not None and selectedObjList is not None and len(selectedObjList) < 1:
        errorMsg = "Failed to find any messages for user: '%s'" % user

    return render_to_response(SEARCH_USERMESSAGE_HTML, {'error_message' : errorMsg, 'user': user, 'isprimary': isPrimary, 'object_list': selectedObjList})


HOST_PATTERN = re.compile("LON.(\w+)\d*")
EMAIL_PATTERN = re.compile("(\w+)\d*@\w+")

def getUserNameFromRequest(request):
  userName = None
  computerName = None

  try:
    userName= request.META['USERNAME']
  except:
    pass

  try:
    computerName = request.META['COMPUTERNAME']
  except:
    pass

  try:
    adminName = request.META['SERVER_ADMIN']
  except:
    pass

  if userName is not None and len(userName) >= 4:
    return userName

  if computerName is not None and len(computerName) >=4:
    match = HOST_PATTERN.match(computerName)
    if match is not None:
      return match.group(1)

  if adminName is not None and len(adminName) >= 4:
    match = EMAIL_PATTERN.match(adminName)
    if match is not None:
      return match.group(1)
  return None


def help(request):

    userName = getUserNameFromRequest(request)

    try:
        dev = Developer.objects.get(username__exact=userName)
        return HttpResponse("Hello %s %s (username: %s) this is the help pages specially made for you!" % (dev.firstname, dev.surname, userName))
    except (Developer.DoesNotExist):
        pass
    return HttpResponse("Hello %s this is the help pages specially made for you! ['%s', '%s']" % (userName, request.META['SERVER_ADMIN'], request.META['SERVER_NAME']))

def display_user_release_summary(request, project, branch, release):
    '''Display the results for the selected release'''
    paramWrapper = RegressionRequestWrapper(project, branch, release)
    paramWrapper.setBaseURL('validate')
    selected_release = paramWrapper.getRelease()

    # Process request to display the packages chart for the release
    selectedUser = None
    if 'user' in request.REQUEST.keys() and request.REQUEST['user'] is not None:
        selectedUser = request.REQUEST['user']
    else:
        raise Http404

    # Get the responsible data for the user
    selectedObjList = Responsibility.objects.filter(primary__exact=selectedUser).values('package', 'function').distinct()
    packages = Set()
    functions = Set()
    for x in selectedObjList:
        packages.add(x['package'])
        functions.add(x['function'])

    # Now filter the release data
    regQuerySet = RegressionResult.objects.filter(release__id__exact=selected_release.id, \
                                                  file__package__in=packages, \
                                                  file__directory_path__in=functions)

    pkgs_list = paramWrapper.getPackagesList(regQuerySet)

    # Get the status figures per package
    pkg_hash_list = process_package_stats_list(regQuerySet, pkgs_list, None, None)

    # Get top level stats for the release.
    paramWrapper.getReleaseStats()

    return render_to_response(RELEASE_USER_SUMMARY_HTML, {'reg_params': paramWrapper, \
                                                          'pkg_hash_list' : pkg_hash_list})
                                                     
