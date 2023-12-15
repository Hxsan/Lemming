"""Tests of the create task view."""
from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from tasks.forms import CreateTaskForm
from tasks.models import User, Task, Team
from tasks.tests.helpers import reverse_with_next

class CreateTaskViewTestCase(TestCase):
    """Tests of the create task view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
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
            'priority': 'medium',
        }

    def test_create_task_url(self):
        self.assertRegex(self.url, r'^/dashboard/create_task/\d+/$')
        # Checks if the URL matches the regex pattern /dashboard/create_task/NUM/ where NUM is at least 1 digit

    def test_get_create_task(self):
        self.client.login(username=self.user.username, password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_task.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, CreateTaskForm))
        self.assertFalse(form.is_bound)

    def test_get_create_task_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next('log_in', self.url)
        response = self.client.get(self.url)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
    
    def test_create_task_unsuccessful(self):
        self.client.login(username=self.user.username, password='Password123')
        self.form_input['due_date'] = 'WRONG_DATE'
        response = self.client.post(self.url, self.form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_task.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, CreateTaskForm))
        self.assertTrue(form.is_bound)

    def test_create_task_successful(self):
        self.client.login(username=self.user.username, password='Password123')
        response = self.client.post(self.url, self.form_input, follow=True)
        response_url = reverse('dashboard')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        task = Task.objects.get(title='Task 1')
        self.assertEqual(task.description, 'This is a task')
        due_date_string = task.due_date.strftime('%m/%d/%Y')
        self.assertEqual(due_date_string, '01/02/2024')
        self.assertEqual(task.created_by, self.team)
    
    def test_post_create_task_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next('log_in', self.url)
        response = self.client.post(self.url, self.form_input)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
    

