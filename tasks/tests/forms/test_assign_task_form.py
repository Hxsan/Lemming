"""Unit tests of the assign task form."""
from django import forms
from django.test import TestCase
from django.urls import reverse
from tasks.forms import AssignTaskForm
from tasks.models import User, Task

class AssignTaskFormTestCase(TestCase):
     
    fixtures = ['tasks/tests/fixtures/default_user.json', 'tasks/tests/fixtures/other_users.json']

    def setUp(self):
        self.url = reverse('assign_task')
        self.user = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
        self.third_user = User.objects.get(username='@petrapickles')
        self.task = Task.objects.create(
            title='Task 1',
            description='This is a task',
            due_date='2024-02-01',
            created_by=self.user,
        )
        self.form_input = {
            'usernames' : ['@janedoe'],
        }
    
    def test_valid_assign_task_form(self):
        form = AssignTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_assign_task_form_has_necessary_fields(self):
        form = AssignTaskForm()
        self.assertIn('usernames', form.fields)

    def test_usernames_selected_must_not_be_zero(self):
        self.form_input['usernames'] = ''
        form = AssignTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
    
    def test_assign_task_must_save_correctly(self):
        self.client.login(username=self.user.username, password='Password123')
        before_count = self.task.assigned_to.count()
        self.client.post(self.url, self.form_input)
        self.task.refresh_from_db()
        after_count = self.task.assigned_to.count()
        self.assertEqual(after_count, before_count+1) # Expected to fail, assign task is unfinished

    def test_assign_task_to_yourself_is_valid(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['usernames'] = ['@johndoe']
        form = AssignTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())
    
    def test_assign_multiple_users_to_task_saves_correctly(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['usernames'] = ['@janedoe', '@peterpickles', '@petrapickles']
        before_count = self.task.assigned_to.count()
        self.client.post(self.url, self.form_input)
        self.task.refresh_from_db()
        after_count = self.task.assigned_to.count()
        self.assertEqual(after_count, before_count+3) # Expected to fail, assign task is unfinished