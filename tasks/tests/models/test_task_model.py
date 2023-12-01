"""Unit tests for the Task model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import User, Team, Task

class TaskModelTestCase(TestCase):

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
        self.team = Team.objects.get(team_name='Team 1')
        self.task = Task.objects.create(
            title='Task 1',
            description= 'This is a task',
            due_date='2024-02-01',
            created_by=self.team,
            task_completed=False
        )
        self.task.assigned_to.set([self.second_user])
    
    def test_valid_task(self):
        self._assert_task_is_valid()
    
    def test_title_can_be_30_characters_long(self):
        self.task.title = 'x' * 30
        self._assert_task_is_valid()
    
    def test_title_cannot_be_more_than_30_characters_long(self):
        self.task.title = 'x' * 31
        self._assert_task_is_invalid()
    
    def test_title_can_have_non_alphanumericals(self):
        self.task.title = 'Task #1'
        self._assert_task_is_valid()
    
    def test_due_date_cannot_be_blank(self):
        self.task.due_date = ''
        self._assert_task_is_invalid()
    
    def test_task_assignment_can_be_blank(self):
        self.task.assigned_to.set([None])
        self._assert_task_is_valid()
    
    def test_task_assignment_can_have_more_than_one_user(self):
        self.task.assigned_to.set([self.user, self.second_user])
        self._assert_task_is_valid()
    
    def test_task_completion_must_be_True_or_False(self):
        self.task.task_completed = None
        self._assert_task_is_invalid()

    def _assert_task_is_valid(self):
        try:
            self.task.full_clean()
        except (ValidationError):
            self.fail('Test task should be valid')

    def _assert_task_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.task.full_clean()