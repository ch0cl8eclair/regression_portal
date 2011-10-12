import os
import sys
from os.path import abspath
import posixpath
import ConfigParser

# Django settings for regression project.
DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('bklair', 'baldevklair@yahoo.co.uk'),
)


###############################################################
# Dynamic setup based on current directory and config file
#

# Get the name of the current dir
REG_DIR = os.path.dirname(os.path.abspath(__file__))
TOP_DIR_LOCAL = os.path.dirname(REG_DIR)
# Maintain unix style path for config
TOP_DIR = TOP_DIR_LOCAL.replace(os.sep, posixpath.sep)

PROJECT_PATH_LIST = []
PROJECT_PATH_LIST.append(REG_DIR)
PROJECT_PATH_LIST.append(TOP_DIR)

for mypath in PROJECT_PATH_LIST:
  if mypath not in sys.path:
    sys.path.append(mypath)

# Override any settings with settings from the optional config file
CONFIG_FILE = os.sep.join([REG_DIR, 'Config.conf'])

if os.path.isfile(CONFIG_FILE):
  Config = ConfigParser.ConfigParser()
  Config.read(CONFIG_FILE)
  # Set the Debug
  try:
    if Config.getboolean('General', 'debug'):
      DEBUG = True
  except:
    pass

  # Set the cache
  try:
    if not Config.getboolean('Cache', 'enabled'):
      CACHE_BACKEND = 'dummy://'
    else:
      CACHE_BACKEND = "file://%s/regression/cache" % TOP_DIR
  except:
    pass



###############################################################
# End Dynamic setup
#

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '%s/regression/db/regression.db' % TOP_DIR,                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '+iu^%7wl%0sqt6-inx(_4m6#ze!f)t(yb^ffs6#s!2450zw7@9'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

CACHE_MIDDLEWARE_SECONDS= 60 * 60 * 24
CACHE_MIDDLEWARE_KEY_PREFIX=""

ROOT_URLCONF = 'regression.urls'

TEMPLATE_DIRS = (
    "%s/mytemplates/regression" % TOP_DIR
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

STATIC_DOC_ROOT = '%s/mytemplates/regression/static' % TOP_DIR

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    # my models
    'regr',
    'validate',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)
