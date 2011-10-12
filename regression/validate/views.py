from regr.models import *
import sys
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404

import re

DISPLAY_DEVELOPERS_HTML = 'vlistdevelopers.html'
DISPLAY_RESPONSIBILITY_HTML = 'vlistresponsibility.html'
SEARCH_MESSAGE_HTML = 'vmessagesearch.html'
SEARCH_USERMESSAGE_HTML = 'vusersearch.html'

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
    querySet = Responsibility.objects.filter(message__startswith=message)
    return render_to_response(DISPLAY_RESPONSIBILITY_HTML, {'object_list': querySet})

MSG_PATTERN = re.compile("\w{6}(_\d+)*")

def search_message(request):
    '''Searches for the supplied msg'''
    selectedObjList = None
    message = None
    errorMsg = None
    flagError = False

    try:
        message = request.GET['message']
        match = MSG_PATTERN.match(message)
        if match is not None:
          selectedObjList = Responsibility.objects.filter(function__startswith=message.upper())
        else:
          flagError = True
          errorMsg = "Invalid message format passed in: '%s'" % message
    except (KeyError, Responsibility.DoesNotExist):
        if message is not None:
          flagError = True
          errorMsg = "Invalid message format passed in: '%s'" % message

    if not flagError and message is not None and selectedObjList is not None and len(selectedObjList) < 1:
        errorMsg = "Failed to find results for entered message: '%s'" % message

    return render_to_response(SEARCH_MESSAGE_HTML, {'error_message' : errorMsg, 'message' : message, 'object_list': selectedObjList})

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
