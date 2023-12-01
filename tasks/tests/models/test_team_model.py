"""Unit tests for the Team model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import Team, User

class TeamModelTestCase(TestCase):
    """Unit tests for the Team model."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
    ]
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(team_name = 'ValidTeam', admin_user = self.user)

    def test_valid_team(self):
        self._assert_user_is_valid()
    
    def test_team_name_cannot_be_blank(self):
        self.team.team_name=""
        self._assert_user_is_invalid()

    def test_team_name_can_be_50_characters(self):
        self.team.team_name="x"*50
        self._assert_user_is_valid()

    def test_team_name_cannot_be_over_51_characters(self):
        self.team.team_name="x"*51
        self._assert_user_is_invalid()

    def test_team_admin_user_cannot_be_blank(self):
        self.team.admin_user = None
        self._assert_user_is_invalid()

    def _assert_user_is_valid(self):
        try:
            self.team.full_clean()
        except (ValidationError):
            self.fail('Test team should be valid')

    def _assert_user_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.team.full_clean()
