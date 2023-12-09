"""Unit tests of the Edit Task form."""
from django import forms
from django.test import TestCase
from tasks.forms import EditTaskForm
from tasks.models import Task
from datetime import date, timedelta

class EditTaskFormTestCase(TestCase):
    """Unit tests of the Edit Task form."""

    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        self.form_input = {
            'title': 'Task1', 
            'description': 'This is a task', 
            'due_date': date.today(),
            'priority': 'medium',
        }
        self.task = Task.objects.create(title="Task1", description="This is a task", due_date=date.today())

    #test for widgets as well
    def test_form_contains_required_fields(self):
        form = EditTaskForm()
        self.assertIn('title', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('due_date', form.fields)
        self.assertIn('priority', form.fields)
        self.assertIn('reminder_days', form.fields)
        description_field = form.fields['description']
        due_date_field = form.fields['due_date']
        self.assertTrue(isinstance(description_field.widget,forms.Textarea))
        self.assertTrue(isinstance(due_date_field.widget,forms.DateInput))
        self.assertTrue(due_date_field.widget.attrs['min'], date.today)

    def test_form_accepts_valid_input(self):
        form = EditTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    #test for model validation on tasks
    def test_form_rejects_blank_title(self):
        self.form_input['title'] = ''
        form = EditTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_accepts_blank_description(self):
        self.form_input['description'] = ''
        form = EditTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_rejects_blank_due_date(self):
        self.form_input['due_date'] = None
        form = EditTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_due_date_field_can_be_today(self):
        self.form_input['due_date'] = date.today()
        form = EditTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())   

    def test_due_date_field_cannot_be_yesterday_or_less(self):
        self.form_input['due_date'] = date.today() - timedelta(1)
        form = EditTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
    
    def test_priority_has_to_be_low_medium_or_high(self):
        self.form_input['priority'] = 'INVALID'
        form = EditTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
    
    def test_reminder_can_be_before_than_due_date(self):
        self.form_input['due_date'] = date.today() + timedelta(7)
        self.form_input['reminder_days'] = 6
        form = EditTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())
    
    def test_reminder_cannot_be_after_than_due_date(self):
        self.form_input['due_date'] = date.today() + timedelta(7)
        self.form_input['reminder_days'] = 8
        form = EditTaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    #Test form saves correctly
    def test_form_saves_correctly(self):
        self.form_input['title'] = "Task1New"
        form = EditTaskForm(self.form_input)
        before_count = Task.objects.count()
        form.save(self.task)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count) #check we haven't created a new task, just updated it
        task = Task.objects.get(title='Task1New')
        self.assertIsNotNone(task)
        #check all other variables are the same
        self.assertEqual(task.description, self.task.description)
        self.assertEqual(task.due_date, self.task.due_date)
        self.assertEqual(task.task_completed, self.task.task_completed)
        self.assertEqual(task.assigned_to, self.task.assigned_to)

    
