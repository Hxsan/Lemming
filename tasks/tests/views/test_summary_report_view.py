"""Unit tests of the summary report view."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from tasks.models import User, Team, Task, TimeSpent, TimeLog
from tasks.tests.helpers import reverse_with_next
from datetime import date, datetime, timedelta

class SummaryReportViewTestCase(TestCase):

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.get(team_name='Team 1')
        self.user.teams.set([self.team])
        self.task = Task.objects.create(
            title='Task 1',
            description='This is a task',
            due_date=date.today(),
            priority='medium',
        )
        self.client.login(username=self.user.username, password='Password123')
        self.url = reverse('summary_report')

        # Simulate user submitting time to create instances of TimeSpent and TimeLog
        self.client.post(
            reverse('submit_time', kwargs={'team_id': self.team.id, 'task_id':self.task.id}),
            {'hours': 1, 'minutes': 1, 'seconds': 1},
            follow=True, 
        )
    
    def test_get_summary_report(self):
        self.assertEqual(self.url, '/summary_report/')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'summary_report.html')

    def test_get_summary_report_redirects_when_not_logged_in(self):
        self.client.logout()
        redirect_url = reverse_with_next('log_in', self.url)
        response = self.client.get(self.url)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)

    def test_time_submission_passed_to_template_correctly(self):
        response = self.client.get(self.url)
        user_times = response.context['user_times']
        time_logs = response.context['time_logs']
        teams = response.context['teams']
        self.assertIn(self.team, teams)
        self.assertTrue(user_times.count() == time_logs.count() == 1)
        self.assertTrue(user_times[0].time_spent == time_logs[0].logged_time == 3661)

        log_naive_timestamp = time_logs[0].timestamp.replace(tzinfo=None)
        self.assertAlmostEqual(log_naive_timestamp, datetime.now(), delta=timedelta(seconds=1))
    
    def test_second_submission_passed_to_template_correctly(self):
        # Simulate second submission which should interact differently with TimeSpent and TimeLog
        self.client.post(
            reverse('submit_time', kwargs={'team_id': self.team.id, 'task_id':self.task.id}),
            {'hours': 1, 'minutes': 1, 'seconds': 1},
            follow=True, 
        )
        response = self.client.get(self.url)
        user_times = response.context['user_times']
        time_logs = response.context['time_logs']
        self.assertNotEqual(user_times.count(), time_logs.count())
        self.assertEqual(user_times.count(), 1)
        self.assertEqual(time_logs.count(), 2)
        self.assertEqual(user_times[0].time_spent, 7322)
        self.assertTrue(time_logs[0].logged_time == time_logs[1].logged_time == 3661)

        # Check that timestamps have been ordered correctly
        timestamps = [log.timestamp for log in time_logs]
        self.assertEqual(timestamps, sorted(timestamps))