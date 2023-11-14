"""Unit tests for the Team model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import Team, User
from tasks.forms import CreateTeamForm

class TeamModelTestCase(TestCase):
    """Unit tests for the Team model."""

    def test_valid_team(self):
        form = CreateTeamForm(data = {"team_name": "ValidTeam"})
        self.assertTrue(form.is_valid())

    def test_invalid_team(self):
        form = CreateTeamForm(data = {"team_name": ""})
        self.assertFalse(form.is_valid())
