"""Tests for Dashboard view"""
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone
from tasks.models import User, Team, Task

class DashboardViewTestCase(TestCase):
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name='Team 1',
            admin_user=self.user,
        )
        self.team.members.set([self.user])
        self.user.teams.set([self.team])
        self.url = reverse('dashboard')
        self.client.login(username='@johndoe', password='Password123') #be logged in first

    def test_view_team_button_is_disabled_when_there_is_no_team(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'view-team-button', html=True)

    def test_dashboard_view_authenticated_user(self):
        request = self.factory.get(self.url)
        request.user = self.user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view_unauthenticated_user(self):
        request = self.factory.get(self.url)
        request.user = AnonymousUser()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view_teams_empty(self):
        self.user.teams.clear()
        request = self.factory.get(self.url)
        request.user = self.user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['teams']), 0)
        self.assertEqual(response.context['team_tasks'], None)

    def test_dashboard_view_teams_not_empty(self):
        request = self.factory.get(self.url)
        request.user = self.user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['teams']), 1)
        self.assertNotEqual(len(response.context['team_tasks']), 0)

    def test_dashboard_view_ordering(self):
        request = self.factory.get(self.url, {'order': 'due_date'})
        request.user = self.user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view_filtering(self):
        request = self.factory.get(self.url, {'filter': 'priorityHigh'})
        request.user = self.user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view_searching(self):
        request = self.factory.get(self.url, {'search_query': 'Task'})
        request.user = self.user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)