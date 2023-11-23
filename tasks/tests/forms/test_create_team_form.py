    
"""Unit tests of the create team form."""
from django import forms
from django.test import TestCase
from tasks.forms import CreateTeamForm
from tasks.models import User,Team
from django.urls import reverse


class CreateTeamFormTestCase(TestCase):
    """Unit tests of the create team form."""
    
    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        self.form_input = {
            'team_name': 'NewTeam'
        }
        self.user = User.objects.get(username='@johndoe')


    def test_valid_create_team_form(self):
        form = CreateTeamForm({'team_name':'NewTeam'})
        self.assertTrue(form.is_valid())

    def test_form_has_necessary_fields(self):
        form = CreateTeamForm()
        self.assertIn('team_name', form.fields)

    def test_form_uses_model_validation(self):
        self.form_input['team_name'] = '' #blank name
        form = CreateTeamForm(self.form_input) 
        self.assertFalse(form.is_valid())

    def test_form_saves_correctly(self):
        form = CreateTeamForm(self.form_input)
        before_count = Team.objects.count()
        form.save(self.user)
        after_count = Team.objects.count()
        self.assertEqual(after_count, before_count + 1)
        team = Team.objects.get(team_name = 'NewTeam')
        self.assertIsNotNone(team)

