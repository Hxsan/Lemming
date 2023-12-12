"""Tests of the dashboard view."""
from django.test import TestCase
from tasks.models import User
from django.urls import reverse

class DashboardViewTestCase(TestCase):
    """Tests of the dashboard view."""

    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        self.url = reverse("dashboard")
        self.user = User.objects.get(username='@johndoe')
        self.client.login(username='@johndoe', password='Password123') #be logged in first

    def test_view_team_button_is_disabled_when_there_is_no_team(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'view-team-button', html=True)
