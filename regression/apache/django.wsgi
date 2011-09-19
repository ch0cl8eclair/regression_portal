import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

sys.path.append('d:\dev\webproj')
sys.path.append('d:\dev\webproj\regression')
sys.path.append('d:\dev\data')

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

print >> sys.stderr, sys.path
