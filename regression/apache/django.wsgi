import os
import sys
from django.conf import settings

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
REG_DIR = os.path.dirname(CUR_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

if REG_DIR not in sys.path:
    sys.path.append(REG_DIR)

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

print >> sys.stderr, sys.path
