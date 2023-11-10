"""Unit tests of the create task form."""
from django import forms
from django.test import TestCase
from django.urls import reverse
from tasks.forms import CreateTaskForm
from tasks.models import User, Task

class CreateTaskFormTestCase(TestCase):

    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        self.url = reverse('create_task')
        self.user = User.objects.get(username='@johndoe')
        self.form_input = {
            'title' : 'Task 1',
            'description' : 'This is a task',
            'due_date' : '01/02/2024',
            'created_by' : ''
        }
    
    def test_valid_task_form(self):
        form = CreateTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())
    
    def test_task_form_has_necessary_fields(self):
        form = CreateTaskForm()
        self.assertIn('title', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('due_date', form.fields)
        self.assertNotIn('created_by', form.visible_fields())
    
    def test_title_must_not_be_empty(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['title'] = ''
        form = CreateTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
    
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
        form = CreateTaskForm(data=self.form_input)
        before_count = Task.objects.count()
        self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count+1)
        task = Task.objects.get(title='Task 1')
        self.assertEqual(task.description, 'This is a task')
        due_date_string = task.due_date.strftime('%m/%d/%Y')
        self.assertEqual(due_date_string, '01/02/2024')
        self.assertEqual(task.created_by, self.user)


