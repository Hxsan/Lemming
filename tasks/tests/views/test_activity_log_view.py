"""Unit tests for the Activity Log view."""
from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from tasks.forms import CreateTaskForm
from tasks.models import User, Task, Team, Activity_Log

class ActivityLogViewTestCase(TestCase):
    """Unit tests for the Activity Log view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.member_with_log = User.objects.get(username='@janedoe') #we will be getting this user's activity log
        self.member_without_log = User.objects.get(username='@petrapickles') #no log for this user
        #Create team and add members to the team
        self.team = Team.objects.create(team_name='TestTeam',admin_user=self.user)
        self.url = reverse("activity_log", args=[self.team.id, self.member_with_log.id])
        self.team.members.set([self.user, self.member_with_log])
        self.user.teams.set([self.team])
        self.member_with_log.teams.set([self.team])

    #get activity log for the second user
    def test_activity_log_url(self):
        self.assertEqual(self.url, f'/dashboard/show_team/{self.team.id}/user_activity_log/{self.member_with_log.id}')

    def test_get_activity_log_view(self):
        self.client.login(username=self.user.username, password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'activity_log.html')
       

    def test_activity_log_passed_in_correctly(self):
        self.client.login(username=self.user.username, password='Password123')
        activity_log = Activity_Log.objects.get(user = self.member_with_log)
        response = self.client.get(self.url)
        page_obj = response.context['page_obj']
        #check that jane's sign up log is in the page 
        self.assertEqual(page_obj[0], activity_log.log[0])

    def test_render_when_no_log_available(self):
        self.client.login(username=self.user.username, password='Password123')
        #delete log
        Activity_Log.objects.filter(user = self.member_without_log).delete()
        #Now it should redirect
        url_of_no_log = reverse("activity_log", args=[self.team.id, self.member_without_log.id])
        response = self.client.get(url_of_no_log, follow=True)
        redirect_url = reverse('show_team', args=[self.team.id])
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'show_team.html')
    
    def test_redirect_when_this_team_is_deleted_elsewhere(self):
        self.client.login(username=self.user.username, password='Password123')
        self.team.delete()
        response = self.client.get(self.url, follow=True)
        response_url = reverse('dashboard')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html') #check redirect back to dashboard
        self.assertContains(response, 'This team was deleted')

