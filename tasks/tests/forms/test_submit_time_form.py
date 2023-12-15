"""Unit tests of the submit time form."""
from django import forms
from django.test import TestCase
from django.urls import reverse
from tasks.forms import SubmitTimeForm
from tasks.models import User, Task, Team, TimeSpent, TimeLog
from datetime import date, datetime, timedelta
from django.utils import timezone

class SubmitTimeFormTestCase(TestCase):
     
    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name='Team 1',
            admin_user=self.user,
        )
        self.team.members.set([self.user])
        self.user.teams.set([self.team])
        self.task = Task.objects.create(
            title='Task 1',
            description='This is a task',
            due_date=date.today(),
            priority='medium',
            created_by=self.team,
        )
        self.form_input = {
            'hours': 1,
            'minutes': 1,
            'seconds': 1
        }
        self.url = reverse('submit_time', kwargs={'team_id': self.team.id, 'task_id':self.task.id})
    
    def test_valid_submit_time_form(self):
        form = SubmitTimeForm(data=self.form_input)
        self.assertTrue(form.is_valid())
    
    def test_negative_values_for_fields_are_invalid(self):
        self.form_input['hours'] = -1
        hours_form = SubmitTimeForm(data=self.form_input)
        self.assertFalse(hours_form.is_valid())
        self.form_input['hours'] = 1
        self.form_input['minutes'] = -1
        mins_form = SubmitTimeForm(data=self.form_input)
        self.assertFalse(mins_form.is_valid())
        self.form_input['minutes'] = 1
        self.form_input['seconds'] = -1
        secs_form = SubmitTimeForm(data=self.form_input)
        self.assertFalse(secs_form.is_valid())
    
    def test_blank_fields_are_valid(self):
        self.form_input['hours'] = ''
        hours_form = SubmitTimeForm(data=self.form_input)
        self.assertTrue(hours_form.is_valid())
        self.form_input['hours'] = 1
        self.form_input['minutes'] = ''
        mins_form = SubmitTimeForm(data=self.form_input)
        self.assertTrue(mins_form.is_valid())
        self.form_input['minutes'] = 1
        self.form_input['seconds'] = ''
        secs_form = SubmitTimeForm(data=self.form_input)
        self.assertTrue(secs_form.is_valid())

    def test_all_fields_can_be_blank_simultaneously(self):
        form = SubmitTimeForm(data={})
        self.assertTrue(form.is_valid())

    def test_blank_fields_are_automatically_saved_as_0(self):
        form = SubmitTimeForm(data={})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_hours, 0)
        self.assertEqual(form.cleaned_minutes, 0)
        self.assertEqual(form.cleaned_seconds, 0)
    
    def test_submit_time_form_saves_new_time_log(self):
        form = SubmitTimeForm(data=self.form_input)

        user_time_before_count = TimeSpent.objects.count()
        time_log_before_count = TimeLog.objects.count()

        # is_valid() used to call clean() method indirectly
        self.assertTrue(form.is_valid())
        form.save(user=self.user, task=self.task)

        user_time_after_count = TimeSpent.objects.count()
        time_log_after_count = TimeLog.objects.count()

        self.assertEqual(time_log_after_count, time_log_before_count+1)
        self.assertEqual(user_time_after_count, user_time_before_count+1)

        # Both models should save the exact same data for the first instance 
        user_time = TimeSpent.objects.get(pk=1)
        log_instance = TimeLog.objects.get(pk=1)
        self.assertTrue(user_time.user == log_instance.user == self.user)
        self.assertTrue(user_time.task == log_instance.task == self.task)
        self.assertTrue(user_time.time_spent == log_instance.logged_time == 3661)

        # Convert log_instance.timestamp into a timezone-naive datetime (doesn't take into account timezones)
        # This is so almostEqual doesn't run into an error
        log_naive_timestamp = log_instance.timestamp.replace(tzinfo=None)

        # Timestamp will never be equal to the millisecond
        self.assertAlmostEqual(log_naive_timestamp, datetime.now(), delta=timedelta(seconds=1))
    
    def test_successive_forms_accumulates_TimeSpent_instance(self):
        before_count = TimeSpent.objects.count()

        # Submit two forms successively
        form1 = SubmitTimeForm(data=self.form_input)
        self.assertTrue(form1.is_valid())
        form1.save(user=self.user, task=self.task)
        form2 = SubmitTimeForm(data=self.form_input)
        self.assertTrue(form1.is_valid())
        form1.save(user=self.user, task=self.task)

        after_count = TimeSpent.objects.count()

        # Only 1 instance should be saved
        self.assertEqual(after_count, before_count+1)

        user_time = TimeSpent.objects.get(pk=1)
        # Time spent should be 2 hours 2 minutes 2 seconds (7322 seconds)
        self.assertEqual(user_time.time_spent, 7322)

    def test_successive_forms_creates_different_TimeLog_instances(self):
        before_count = TimeLog.objects.count()

        # Submit two forms successively
        form1 = SubmitTimeForm(data=self.form_input)
        self.assertTrue(form1.is_valid())
        form1.save(user=self.user, task=self.task)
        form2 = SubmitTimeForm(data=self.form_input)
        self.assertTrue(form1.is_valid())
        form1.save(user=self.user, task=self.task)

        after_count = TimeLog.objects.count()

        # 2 seperate instances should be saved
        self.assertEqual(after_count, before_count+2)

        log_instance1 = TimeLog.objects.get(pk=1)
        log_instance2 = TimeLog.objects.get(pk=2)

        # Each logged time should be 1 hour 1 minute 1 second (3661 seconds)
        self.assertTrue(log_instance1.logged_time == log_instance2.logged_time == 3661)
