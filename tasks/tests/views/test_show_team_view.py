"""Tests of the show team view."""
"""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team
from tasks.forms import CreateTeamForm

class ShowTeamViewTestCase(TestCase):
    """Tests of the show team view."""

    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        #need to have logged in and created team first, do this in setup
        self.client.login(username='@johndoe', password='Password123')
        #create a team for this guy
        self.client.post(reverse("create_team"), {'team_name':'NewTeam'}, follow = True)
        self.url = reverse('show_team')
        self.user = User.objects.get(username='@johndoe')

    def test_show_team_url(self):
        self.assertEqual(self.url,'/dashboard/show_team')

    def test_get_show_team(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_team.html')

    def test_team_members_passed_in(self):
        #check if a list of users and the team is provided and that they are all valid teams and users
        response = self.client.get(self.url, follow=True)
        #user_list = response.context['users'] comment out for now
        team = response.context['team']
        self.assertNotEqual(team, None)
        self.assertEqual(team.team_name, 'NewTeam')
        #self.assertEqual(user_list.count(), 1)
        #can't do this test yet
"""
