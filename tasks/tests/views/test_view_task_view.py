"""Unit tests of the view task view."""
from django import forms
from django.test import TestCase
from tasks.forms import EditTaskForm, AssignTaskForm
from tasks.models import User,Team, Task
from django.urls import reverse
from datetime import date, timedelta


class ViewTaskViewTestCase(TestCase):
    """Unit tests of the view task view."""

    fixtures = ['tasks/tests/fixtures/default_user.json', 'tasks/tests/fixtures/other_users.json']


    def setUp(self):
        self.form_input = {
            'title': 'Task1',
            'description': 'This is a task',
            'due_date': date.today(),
            'edit_submit': 'Save', #these two values to simulate the request information sent
            'task_completed': False,
        }
        self.task = Task.objects.create(title="Task1", description="This is a task", due_date=date.today())
        self.user = User.objects.get(username="@johndoe")
        self.client.login(username='@johndoe', password='Password123')
        #create a team for this guy
        self.client.post(reverse("create_team"), {'team_name':'NewTeam'}, follow = True)
        self.team = Team.objects.get(team_name="NewTeam")
        self.url = reverse('view_task', kwargs={'team_id': self.team.id, 'task_id':self.task.id})
        #dashboard/view-task/<int:team_id>/<int:task_id>/
    
    def test_view_task_url(self):
        self.assertEqual(self.url, f'/dashboard/view-task/{self.team.id}/{self.task.id}/')

    def test_get_view_task(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_information.html')

    def test_context_variables_passed_in(self):
        response = self.client.get(self.url, follow=True)
        team = response.context['team']
        task = response.context['task']
        form = response.context['form']
        form2 = response.context['form2']
        is_admin = response.context['is_admin']
        can_mark_as_complete = response.context['can_mark_as_complete']
        self.assertEqual(team, self.team)
        self.assertEqual(task, self.task)
        self.assertTrue(is_admin)
        self.assertTrue(can_mark_as_complete)
        self.assertTrue(form.is_bound) #check if data is filled in to begin with
        self.assertIsInstance(form, EditTaskForm)
        self.assertIsInstance(form2, AssignTaskForm)

    def test_form_initial_values(self):
        response = self.client.get(self.url, follow=True)
        form = response.context['form']
        self.assertEqual(self.task.title, form.cleaned_data['title'])
        self.assertEqual(self.task.due_date, form.cleaned_data['due_date'])
        self.assertEqual(self.task.description, form.cleaned_data['description'])

    def test_successful_task_edit(self):
        self.form_input['title'] = 'Task2'
        before_count = Task.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        response_url = reverse('dashboard')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html') #check redirect back to dashboard
        self.assertEqual(before_count, after_count)
        self.task.refresh_from_db()
        self.assertEqual('Task2', self.task.title)     

    def test_unsuccessful_task_edit(self):
        self.form_input['title'] = ''
        before_count = Task.objects.count()
        old_title = self.task.title
        self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(before_count, after_count)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, old_title) #make sure the task is still the same

    def test_mark_as_complete_shows_when_user_is_allowed(self):
        #basically check if mark_as_complete is true and that we are the admin
        response = self.client.get(self.url, follow=True)
        can_mark_as_complete = response.context['can_mark_as_complete']
        is_admin = response.context['is_admin']
        self.assertTrue(can_mark_as_complete)
        self.assertTrue(is_admin)


    def test_mark_as_complete_does_not_show_when_user_not_allowed(self):
        #change admin and check if can mark as complete
        newUser = User.objects.get(username='@janedoe')
        self.team.admin_user = newUser #set new admin, so shouldn't be able to mark as complete anymore
        self.team.save()
        self.team.refresh_from_db()
        response = self.client.get(self.url, follow=True)
        can_mark_as_complete = response.context['can_mark_as_complete']
        is_admin = response.context['is_admin']
        self.assertFalse(can_mark_as_complete)
        self.assertFalse(is_admin)

    def test_mark_as_complete_requires_model_validation(self):
        #test that we cannot post with mark as complete if the form is invalid
        self.form_input['task_completed'] = True
        self.form_input['title']= "" #blank, so bad field
        self.client.post(self.url, self.form_input, follow=True)
        self.task.refresh_from_db()
        self.assertFalse(self.task.task_completed) #make sure the task still is not marked as completed

    def test_successful_mark_as_complete(self):
         #test that we cannot post with mark as complete if the form is invalid
        self.form_input['task_completed'] = True
        self.client.post(self.url, self.form_input, follow=True)
        self.task.refresh_from_db()
        self.assertTrue(self.task.task_completed) #make sure the task still is not marked as completed

    """
    Tests should be here for delete task
    """

    def test_due_date_field_can_be_today(self):
        self.form_input['due_date'] = date.today()
        before_count = Task.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        response_url = reverse('dashboard')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html') #check redirect back to dashboard
        self.assertEqual(before_count, after_count)
        self.task.refresh_from_db()
        self.assertEqual(date.today(), self.task.due_date)     

    def test_due_date_field_cannot_be_yesterday_or_less(self):
        self.form_input['due_date'] = date.today() - timedelta(1)
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(date.today(), self.task.due_date)#didn't change

    #The below functionality is mimicked by adding/removing the relevant key in the request.POST dictionary
    def test_task_edit_not_saved_without_save_button(self):
        self.form_input.pop('edit_submit', None) #remove the edit submit key (which is added when we press save)
        self.form_input['title']= "NewTitle"
        old_title = self.task.title
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, old_title)#didn't change

    """
    Tests here for assigning tasks to users
    """
