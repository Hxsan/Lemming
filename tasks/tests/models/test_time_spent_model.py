"""Unit tests for the TimeSpent model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import User, Team, Task, TimeSpent

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
        self.time_spent = TimeSpent.objects.create(
            user=self.user,
            task=self.task,
            time_spent=30
        )
    
    def test_valid_time_spent(self):
        self._assert_time_spent_is_valid()
    
    def test_user_must_not_be_blank(self):
        self.time_spent.user = None
        self._assert_time_spent_is_invalid()
    
    def test_task_must_not_be_blank(self):
        self.time_spent.task = None
        self._assert_time_spent_is_invalid()
    
    def test_time_spent_must_not_be_negative(self):
        self.time_spent.time_spent = -1
        self._assert_time_spent_is_invalid()
    
    def test_time_spent_defaults_to_0_when_unspecified(self):
        second_time_spent = TimeSpent.objects.create(
            user=self.user,
            task=self.task,
        )
        self.assertEqual(second_time_spent.time_spent, 0)


    def _assert_time_spent_is_valid(self):
        try:
            self.time_spent.full_clean()
        except (ValidationError):
            self.fail('Test time spent should be valid')

    def _assert_time_spent_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.time_spent.full_clean()