"""Tests for Dashboard view"""
from django.test import TestCase # ,RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from tasks.tests.helpers import reverse_with_next
from tasks.models import User, Team, Task
from datetime import date, timedelta

class DashboardViewTestCase(TestCase):
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        #self.factory = RequestFactory()
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name='Team 1',
            admin_user=self.user,
        )
        self.task1 = Task.objects.create(title="Task1", description="This is a task", due_date=date.today() + timedelta(1))
        self.task1.created_by = self.team
        self.task2 = Task.objects.create(title="Task2", description="This is another task", due_date=date.today())
        self.task2.created_by = self.team
        self.task1.save()
        self.task2.save()
        self.team.members.set([self.user])
        self.user.teams.set([self.team])
        self.url = reverse('dashboard')
        self.client.login(username='@johndoe', password='Password123') #be logged in first

    def test_view_team_button_is_disabled_when_there_is_no_team(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'view-team-button', html=True)

    def test_dashboard_view_authenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        redirect_url = reverse_with_next('log_in', self.url)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)

    def test_dashboard_view_teams_empty(self):
        self.team.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['teams']), 0)
        self.assertEqual(response.context['team_tasks'], None)

    def test_dashboard_view_teams_not_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['teams']), 1)
        self.assertNotEqual(len(response.context['team_tasks']), 0)

    def test_dashboard_view_ordering(self):
        response = self.client.get(self.url, {'order': 'due_date'})
        self.assertEqual(response.status_code, 200)
        tasks_for_teams = response.context['team_tasks']
        #Check that there is only 1 team, and the tasks we're getting are for our team
        self.assertEqual(len(tasks_for_teams), 1)
        self.assertEqual(tasks_for_teams[0][0], self.team)
        tasks_for_team_1 = tasks_for_teams[0][1]
        #test that the tasks are in the correct order
        #Task 1's due_date is tomorrow's date, while task 2 is today, so task 2 should be first
        self.assertEqual(tasks_for_team_1[0], self.task2)
        self.assertEqual(tasks_for_team_1[1], self.task1)

    def test_dashboard_view_filtering(self):
        #set task 1 to priority High
        self.task1.priority = "high"
        self.task2.priority = "medium"
        self.task1.save()
        self.task2.save()
        response = self.client.get(self.url, {'filter': 'priorityHigh'})
        self.assertEqual(response.status_code, 200)
        #get tasks
        tasks_for_teams = response.context['team_tasks']
        self.assertEqual(len(tasks_for_teams), 1)
        self.assertEqual(tasks_for_teams[0][0], self.team)
        tasks_for_team_1 = tasks_for_teams[0][1]
        #test that the tasks are filtered correctly
        #Only task 1 should be here, because task 2 is medium priority
        self.assertEqual(tasks_for_team_1[0], self.task1)
        self.assertEqual(len(tasks_for_team_1), 1)

    def test_dashboard_view_searching_with_title(self):
        response = self.client.get(self.url, {'search_query': self.task1.title})
        self.assertEqual(response.status_code, 200)
        #get tasks
        tasks_for_teams = response.context['team_tasks']
        self.assertEqual(len(tasks_for_teams), 1)
        self.assertEqual(tasks_for_teams[0][0], self.team)
        tasks_for_team_1 = tasks_for_teams[0][1]
        #test that it has found task 1 and nothing else
        self.assertEqual(tasks_for_team_1[0], self.task1)
        self.assertEqual(len(tasks_for_team_1), 1)

    def test_dashboard_view_searching_with_description(self):
        response = self.client.get(self.url, {'search_query': self.task1.description})
        self.assertEqual(response.status_code, 200)
        #get tasks
        tasks_for_teams = response.context['team_tasks']
        self.assertEqual(len(tasks_for_teams), 1)
        self.assertEqual(tasks_for_teams[0][0], self.team)
        tasks_for_team_1 = tasks_for_teams[0][1]
        #test that it has found task 1 and nothing else
        self.assertEqual(tasks_for_team_1[0], self.task1)
        self.assertEqual(len(tasks_for_team_1), 1)
