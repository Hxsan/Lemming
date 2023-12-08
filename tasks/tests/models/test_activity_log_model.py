"""Unit tests for the Activity Log model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import User, Activity_Log
from datetime import datetime

class ActivityLogModelTestCase(TestCase):
    """Unit tests for the Activity Log model."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.log = Activity_Log.objects.create(log=[(('Valid Entry', datetime.now().strftime("%d/%m/%Y, %H:%M:%S")))], user= self.user)

    def test_valid_activity_log(self):
        self._assert_activity_log_is_valid()

    def test_log_cannot_be_blank(self):
        self.log.log=[]
        self._assert_activity_log_is_invalid()

    def test_user_cannot_be_null(self):
        self.log.user = None
        self._assert_activity_log_is_invalid()

    def test_log_default(self):
        self.assertIsInstance(self.log.log, list)

    def _assert_activity_log_is_valid(self):
        try:
            self.log.full_clean()
        except (ValidationError):
            self.fail('Test team should be valid')

    def _assert_activity_log_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.log.full_clean()