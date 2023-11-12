"""Tests of the show team view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User

class ShowTeamViewTestCase(TestCase):
    """Tests of the show team view."""

    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        #need to have logged in and created team first, do this in setup
        self.url = reverse('dashboard/show_team')
        self.user = User.objects.get(username='@johndoe')

    def test_show_team_url(self):
        self.assertEqual(self.url,'/')

    def test_get_show_team(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_team.html')

    def test_team_members_passed_in(self):
        #check if a list of users and the team is provided and that they are all valid teams and users
        pass