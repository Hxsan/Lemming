"Tests of the show team view."""

from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team
from tasks.forms import CreateTeamForm

class ShowTeamViewTestCase(TestCase):
    """Tests of the show team view."""

    fixtures = ['tasks/tests/fixtures/default_user.json', 'tasks/tests/fixtures/other_users.json']

    def setUp(self):

        #need to have logged in and created team first
        self.client.login(username='@johndoe', password='Password123')
        self.user = User.objects.get(username='@johndoe')
        self.admin_user = self.user
        #create a non-admin user too for safety
        self.non_admin_user = User.objects.get(username='@janedoe')
        #create a team for these people
        self.team = Team.objects.create(team_name='TestTeam', admin_user=self.user)
        self.team.members.add(self.admin_user, self.non_admin_user)
        self.url = reverse('show_team', args=[self.team.id])
        

    def test_show_team_url(self):
        url_with_id = f'/dashboard/show_team/{self.team.id}/'
        self.assertEqual(self.url, url_with_id)

    def test_get_show_team(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'show_team.html')

    def test_all_team_members_showing(self):
        # check that every single team member is displayed
        response = self.client.get(self.url)
        team_members = self.team.members.all()

        for member in team_members:
            self.assertContains(response, member.username)


    def test_team_members_passed_in(self):
        response = self.client.get(self.url, follow=True)
        team = response.context['team']
        team_members = response.context.get("team_members")

        self.assertNotEqual(team, None)
        self.assertNotEqual(team_members, None)
        
        # check if the admin is part of the passed in team
        self.assertIn('@johndoe', [member.username for member in team_members])

        # Check if the non-admin user is part of the passed in team
        self.assertIn('@janedoe', [member.username for member in team_members])

        self.assertEqual(len(team_members), 2)
    
    def test_redirect_when_this_team_is_deleted_elsewhere(self):
        self.team.delete()
        response = self.client.get(self.url, follow=True)
        response_url = reverse('dashboard')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html') #check redirect back to dashboard
        self.assertContains(response, 'This team was deleted')


