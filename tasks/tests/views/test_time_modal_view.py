from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Task, Team
from tasks.forms import SubmitTimeForm
from tasks.templatetags.format_time import format
from datetime import date, timedelta


class TimeModalViewTestCase(TestCase):

    fixtures = ['tasks/tests/fixtures/default_user.json', 'tasks/tests/fixtures/other_users.json']
    
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
        self.team = Team.objects.create(
            team_name='Team 1',
            admin_user=self.user
        )
        self.team.members.set([self.user, self.second_user])
        self.user.teams.set([self.team])
        self.second_user.teams.set([self.team])
        self.task = Task.objects.create(
            title='Task 1',
            description='This is a test task.',
            due_date=date.today(),
            priority='medium',
            created_by=self.team
        )
        self.url = reverse('view_task', kwargs={'team_id': self.team.id, 'task_id':self.task.id})
        self.submit_url = reverse('submit_time', kwargs={'team_id': self.team.id, 'task_id':self.task.id})
        self.reset_url = reverse('reset_time', kwargs={'team_id': self.team.id, 'task_id':self.task.id})
        self.form_input_time = {
            'hours': 1,
            'minutes': 1,
            'seconds': 1,
        }
        self.form_input_assign = {
            'usernames' : [self.user.username, self.second_user.username],
            'assign_submit': '',
        }

        
    def test_track_button_shows_when_user_is_assigned(self):
        self.client.login(username='@johndoe', password='Password123')
        # Send POST request assigning user to task
        response = self.client.post(self.url, self.form_input_assign)
        self.assertContains(response, 'Track time')

    def test_track_button_does_not_show_when_user_is_not_assigned(self):
        self.client.login(username='@johndoe', password='Password123')
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Track time')
    
    def test_valid_data_redirects_successfully(self):
        self.client.login(username='@johndoe', password='Password123')
        response = self.client.post(self.submit_url, self.form_input_time)
        self.assertEqual(response.status_code, 302)
    
    def test_invalid_data_redirects_successfully(self):
        self.client.login(username='@johndoe', password='Password123')
        self.form_input_time['hours'] = -2
        response = self.client.post(self.submit_url, self.form_input_time)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
    
    def test_non_admin_user_can_track_time_if_assigned(self):
        self.client.login(username='@janedoe', password='Password123')
        # If not assigned, non admin user cannot track
        response1 = self.client.get(self.url)
        self.assertNotContains(response1, 'Track time')
        # If assigned, non admin user is able to track
        response2 = self.client.post(self.url, self.form_input_assign)
        self.assertContains(response2, 'Track time')

    def test_total_time_is_calculated_correctly(self):
        self.client.login(username='@johndoe', password='Password123')
        # Submit time for first user
        self.client.post(self.submit_url, self.form_input_time)
        self.client.logout()
        self.client.login(username='@janedoe', password='Password123')
        # Submit time for second user
        self.client.post(self.submit_url, self.form_input_time)
        response = self.client.get(self.url)
        total_time_spent = response.context['total_time_spent']
        self.assertEqual(total_time_spent, 7322) # 7322 seconds = 2h 2m 2s
    
    def test_user_reset_only_removes_user_data(self):
        # Simulate 2 users submitting time
        self.client.login(username='@johndoe', password='Password123')
        self.client.post(self.submit_url, self.form_input_time)
        self.client.logout()
        self.client.login(username='@janedoe', password='Password123')
        self.client.post(self.submit_url, self.form_input_time)
        # Reset time for user @janedoe
        self.client.get(f'{self.reset_url}?action=user')
        response = self.client.get(self.url)
        total_time_spent = response.context['total_time_spent']
        self.assertEqual(total_time_spent, 3661) # 3661 seconds = 1h 1m 1s
    
    def test_total_reset_removes_all_data_for_task(self):
        # Simulate 2 users submitting time
        self.client.login(username='@johndoe', password='Password123')
        self.client.post(self.submit_url, self.form_input_time)
        self.client.logout()
        self.client.login(username='@janedoe', password='Password123')
        self.client.post(self.submit_url, self.form_input_time)
        # Reset total time
        self.client.get(f'{self.reset_url}?action=total')
        response = self.client.get(self.url)
        total_time_spent = response.context['total_time_spent']
        self.assertEqual(total_time_spent, 0)

class FormatTimeTestCase(TestCase):

    def test_no_time_given_returns_message(self):
        self.assertEqual(format(0), 'No time has been spent.')
        self.assertEqual(format(None), 'No time has been spent.')
    
    def test_edge_case_for_a_minute(self):
        self.assertEqual(format(59), '59s ')
        self.assertEqual(format(60), '1m ')
    
    def test_edge_case_for_an_hour(self):
        self.assertEqual(format(3599), '59m 59s ')
        self.assertEqual(format(3600), '1h ')

    def test_edge_case_for_a_day(self):
        self.assertEqual(format(86399), '23h 59m 59s ')
        self.assertEqual(format(86400), '1d ')
    
    def test_random_times_formatted_correctly(self):
        self.assertEqual(format(76543), '21h 15m 43s ')
        self.assertEqual(format(89217), '1d 46m 57s ')
        self.assertEqual(format(67892), '18h 51m 32s ')
    
    """
    def test_redirect_when_this_task_is_deleted_elsewhere(self):
        self.task.delete()
        response = self.client.get(self.url, follow=True)
        response_url = reverse('dashboard')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html') #check redirect back to dashboard
        self.assertContains(response, 'This task was deleted')
    """

