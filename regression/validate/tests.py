"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from regr.models import *

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.failUnlessEqual(1 + 1, 2)

__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}

"""
Test the validate form urls
"""
class ValidateTest(TestCase):
    
    fixtures = ['developer.json', 'responsibility.json']
    
    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_teams(self):
        # Issue a GET request.
        response = self.client.get('/validate/teams/')

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        # Check that the rendered context contains x teams
        querySet = Developer.objects.values('team').order_by('team').distinct()
        self.assertEqual(len(response.context['object_list']), len(querySet))
        
    def test_developers(self):
        # Issue a GET request.
        response = self.client.get('/validate/developers/')

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        # Check that the rendered context contains all developers
        querySet = Developer.objects.all()
        self.assertEqual(len(response.context['object_list']), len(querySet))
        
    def test_get_team_developers(self):
        # Issue a GET request.
        teamStr = "FMW"
        response = self.client.get('/validate/team/%s/' % teamStr)
        

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        # Check that the rendered context contains all developers
        querySet = Developer.objects.filter(team__startswith=teamStr)
        self.assertEqual(len(response.context['object_list']), len(querySet))
        
    def test_get_developer(self):
        # Issue a GET request.
        devStr = "gbarnier"
        response = self.client.get('/validate/developer/%s/' % devStr)

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        # Check that the rendered context contains all developers
        querySet = Developer.objects.filter(username__startswith=devStr)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].firstname, "Guillaume")

    def test_display_message(self):
        # Issue a GET request.
        msgStr = "FCPCRQ"
        response = self.client.get('/validate/message/%s/' % msgStr)

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        # Check that the rendered context contains all developers
        querySet = Responsibility.objects.filter(function__startswith=msgStr)
        self.assertEqual(len(response.context['object_list']), len(querySet))
        self.assertEqual(response.context['object_list'][0].function, 'FCPCRQ')
        
    def test_search_message(self):
        # Issue a GET request.
        msgStr = "FCPCRQ"
        response = self.client.get('/validate/message/?message=%s' % msgStr)

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)
        
        # Check that the rendered context contains all developers
        querySet = Responsibility.objects.filter(function__startswith=msgStr)
        self.assertEqual(len(response.context['object_list']), len(querySet))
        self.assertEqual(response.context['object_list'][0].function, 'FCPCRQ')
        self.assertEqual(response.context['error_message'], None)
        self.assertEqual(response.context['message'], msgStr)
        
    def test_search_user(self):
        # Issue a GET request.
        userStr = "dward"
        response = self.client.get('/validate/usermessage/?user=%s' % userStr)

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)
        
        # Check that the rendered context contains all developers
        querySet = Responsibility.objects.filter(primary__exact=userStr)
        self.assertEqual(len(response.context['object_list']), len(querySet))
        self.assertEqual(response.context['object_list'][0].function, 'TTY_LDM_CPM')
        self.assertEqual(response.context['error_message'], None)
        self.assertEqual(response.context['user'], userStr)
        self.assertEqual(response.context['isprimary'], True)
        