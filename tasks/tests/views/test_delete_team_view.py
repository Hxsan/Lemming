"""Tests of the delete team view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team

class DeleteTeamViewTestCase(TestCase):
    """Tests of the delete team view."""
    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        # create admin and non-admin users and add them to a team
        self.admin_user = User.objects.get(username='@johndoe')
        self.non_admin_user = User.objects.get(username='@janedoe')

        self.client.login(username='@johndoe', password='Password123')
        self.team = Team.objects.create(team_name='Test Team', admin_user=self.admin_user)
        self.team.members.add(self.admin_user, self.non_admin_user)

    def test_delete_team_button_displayed_for_admin(self):
        # send a get request to the show_team view as the admin user
        response = self.client.get(reverse('show_team', args=[self.team.id]))

        # make sure the the delete team button is shown 
        self.assertContains(response, 'Delete Team', html=True)

    def test_delete_team_button_not_displayed_for_non_admin(self):
        # send a get request to the show_team view as a non-admin user
        self.client.login(username='@janedoe', password='Password123')
        response = self.client.get(reverse('show_team', args=[self.team.id]))

        # make sure that the non-admin user can't see the delete team button
        self.assertNotContains(response, 'Delete Team', html=True)
