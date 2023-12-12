"""Unit tests for the TimeLog model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import User, Team, Task, TimeLog
from datetime import datetime, timedelta
from django.utils import timezone

class TimeSpentModelTestCase(TestCase):

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.get(team_name='Team 1')
        self.task = Task.objects.create(
            title='Task 1',
            description= 'This is a task',
            due_date='2024-02-01',
            created_by=self.team,
            task_completed=False
        )
        self.user.teams.set([self.team])
        self.task.assigned_to.set([self.user])
        self.time_log = TimeLog.objects.create(
            user=self.user,
            task=self.task,
            logged_time=30,
        )
    
    def test_valid_time_log(self):
        self._assert_time_log_is_valid()
    
    def test_user_must_not_be_blank(self):
        self.time_log.user = None
        self._assert_time_log_is_invalid()
    
    def test_task_must_not_be_blank(self):
        self.time_log.task = None
        self._assert_time_log_is_invalid()
    
    def test_logged_time_must_not_be_negative(self):
        self.time_log.logged_time = -1
        self._assert_time_log_is_invalid()
    
    def test_timestamp_is_automatically_created(self):
        self.assertIsNotNone(self.time_log.timestamp)
        log_naive_timestamp = self.time_log.timestamp.replace(tzinfo=None)
        self.assertAlmostEqual(log_naive_timestamp, datetime.now(), delta=timedelta(seconds=1))

    def _assert_time_log_is_valid(self):
        try:
            self.time_log.full_clean()
        except (ValidationError):
            self.fail('Test time spent should be valid')

    def _assert_time_log_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.time_log.full_clean()