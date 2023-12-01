"""Unit tests of the create task form."""
from django import forms
from django.test import TestCase
from django.urls import reverse
from tasks.forms import CreateTaskForm
from tasks.models import User, Task, Team

class CreateTaskFormTestCase(TestCase):

    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name='Team 1',
            admin_user=self.user,
        )
        self.team.members.set([self.user])
        self.user.teams.set([self.team])
        self.url = reverse('create_task', kwargs={'pk': self.team.pk})
        self.form_input = {
            'title' : 'Task 1',
            'description' : 'This is a task',
            'due_date' : '01/02/2024',
        }
    
    def test_valid_task_form(self):
        self.client.login(username=self.user.username, password='Password123')
        form = CreateTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())
    
    def test_task_form_has_necessary_fields(self):
        form = CreateTaskForm()
        self.assertIn('title', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('due_date', form.fields)
        self.assertNotIn('created_by', form.visible_fields())
        self.assertNotIn('assigned_to', form.visible_fields())
        self.assertNotIn('task_completed', form.visible_fields())
    
    def test_title_must_not_be_empty(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['title'] = ''
        form = CreateTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
    
    def test_description_can_be_blank(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['description'] = ''
        form = CreateTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_due_date_must_be_in_correct_format(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['due_date'] = ''
        empty_form = CreateTaskForm(data=self.form_input)
        self.assertFalse(empty_form.is_valid())
        self.form_input['due_date'] = 'WRONG_DATE'
        wrong_form = CreateTaskForm(data=self.form_input)
        self.assertFalse(empty_form.is_valid())
    
    def test_task_must_save_correctly(self):
        self.client.login(username=self.user.username, password='Password123')
        before_count = Task.objects.count()
        self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count+1)
        task = Task.objects.get(title='Task 1')
        self.assertEqual(task.description, 'This is a task')
        due_date_string = task.due_date.strftime('%m/%d/%Y')
        self.assertEqual(due_date_string, '01/02/2024')
        self.assertEqual(task.created_by, self.team)

    def test_user_can_create_multiple_tasks(self):
        self.client.login(username=self.user.username, password='Password123')
        before_count = Task.objects.count()
        self.client.post(self.url, self.form_input, follow=True)
        self.form_input = {
            'title' : 'Task 2',
            'description' : 'This is a second task',
            'due_date' : '03/04/2024',
        }
        self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count+2)
        task1 = Task.objects.get(title='Task 1')
        task2 = Task.objects.get(title='Task 2')
        self.assertEqual(task1.created_by, self.team)
        self.assertEqual(task2.created_by, self.team)


