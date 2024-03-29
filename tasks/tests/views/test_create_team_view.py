"""Tests of the create team view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team
from tasks.forms import CreateTeamForm

class CreateTeamViewTestCase(TestCase):
    """Tests of the create team view."""

    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        self.url = reverse("create_team")
        self.client.login(username='@johndoe', password='Password123') #be logged in first
        self.form_input = {
            'team_name': 'NewTeam'
        }

    def test_sign_up_url(self):
        self.assertEqual(self.url, '/dashboard/create_team')

    def test_get_sign_up(self):
        response = self.client.get(self.url) #get response from sign up view
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_team.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, CreateTeamForm))
        self.assertFalse(form.is_bound)

    def test_unsuccessful_sign_up(self):
        self.form_input['team_name'] = '' #set blank
        before_count = Team.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True) #get response from sign up view
        after_count = Team.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_team.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, CreateTeamForm))
        self.assertTrue(form.is_bound)

    def test_valid_team_created(self):
        user = User.objects.get(username= "@johndoe")
        before_count = Team.objects.count()
        #check he has no team
        self.assertEqual(user.teams.count(), 0)
        #create a team for this guy
        response = self.client.post(self.url , self.form_input, follow = True)
        team = Team.objects.get(team_name = "NewTeam")
        after_count = Team.objects.count()
        self.assertEqual(before_count + 1, after_count)
        response_url = reverse('show_team', kwargs={'team_id': team.id})
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'show_team.html')
        #check user team is set
        user.refresh_from_db() #refresh to check changes
        self.assertEqual(user.teams.count(), 1)
        self.assertEqual(user.teams.all()[0].team_name, 'NewTeam')
        self.assertEqual(team.admin_user, user)
        self.assertTrue(team.members.contains(user))
        self.assertEqual(team.team_name, 'NewTeam')