import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

sys.path.append('c:\dev\webproj')
sys.path.append('c:\dev\webproj\regression')
sys.path.append('c:\dev\data')

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

#print >> sys.stderr, sys.path
