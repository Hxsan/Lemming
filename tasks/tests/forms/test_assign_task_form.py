"""Unit tests of the assign task form."""
from django import forms
from django.test import TestCase
from django.urls import reverse
from tasks.forms import AssignTaskForm
from tasks.models import User, Task, Team

class AssignTaskFormTestCase(TestCase):
     
    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
        self.third_user = User.objects.get(username='@petrapickles')
        self.team = Team.objects.create(
            team_name='Team 1',
            admin_user=self.user,
        )
        self.team.members.set([self.user, self.second_user, self.third_user])
        self.user.teams.set([self.team])
        self.second_user.teams.set([self.team])
        self.third_user.teams.set([self.team])
        self.task = Task.objects.create(
            title='Task 1',
            description='This is a task',
            due_date='2024-02-01',
            created_by=self.team,
        )
        self.url = reverse('view_task', kwargs={'team_id': self.team.pk, 'task_id': self.task.pk})
        self.form_input = {
            'usernames' : ['@janedoe'],
            'assign_submit': '',
        }
    
    def test_valid_assign_task_form(self):
        form = AssignTaskForm(self.team, self.task, data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_assign_task_form_has_necessary_fields(self):
        form = AssignTaskForm(self.team, self.task)
        self.assertIn('usernames', form.fields)
    
    def test_assign_task_must_save_correctly(self):
        self.client.login(username=self.user.username, password='Password123')
        before_count = self.task.assigned_to.count()
        self.client.post(self.url, self.form_input)
        self.task.refresh_from_db()
        after_count = self.task.assigned_to.count()
        self.assertEqual(after_count, before_count+1)

    def test_assign_task_to_yourself_is_valid(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['usernames'] = ['@johndoe']
        form = AssignTaskForm(self.team, self.task, data=self.form_input)
        self.assertTrue(form.is_valid())
    
    def test_assign_multiple_users_to_task_saves_correctly(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['usernames'] = ['@johndoe', '@janedoe', '@petrapickles']
        before_count = self.task.assigned_to.count()
        self.client.post(self.url, self.form_input)
        after_count = self.task.assigned_to.count()
        self.assertEqual(after_count, before_count+3)