"""Unit tests for the notification middleware"""

from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Task, Team
from datetime import date, timedelta

class NotificationsTestCase(TestCase):

    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json'
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.second_user = User.objects.get(username='@janedoe')
        self.team = Team.objects.get(team_name='Team 1')
        self.user.teams.set([self.team])
        self.second_user.teams.set([self.team])
        self.task = Task.objects.create(
            title='Task 1',
            description='This is a test task.',
            due_date=date.today(),
            priority='medium',
            created_by=self.team,
            reminder_days=1,
        )

        self.second_task = Task.objects.create(title='Task 2', description='This is a second test task.', due_date=date.today(), priority='medium', created_by=self.team, reminder_days=1)
        self.third_task = Task.objects.create(title='Task 3', description='This is a third test task.', due_date=date.today(), priority='medium', created_by=self.team, reminder_days=1)

        self.url = reverse('dashboard')
        self.client.login(username=self.user.username, password='Password123')
    
    def test_notification_appears_when_reminder_matches_due_date(self):
        # Assign @johndoe to task
        self.task.assigned_to.set([self.user])

        # 1 notification should be present
        self.check_notifications(self.url, 1)

        # Change the due date and reminder to 3 days later
        self.task.due_date = date.today() + timedelta(days=3)
        self.task.reminder_days = 3
        self.task.save()

        # 1 notification should still be present
        self.check_notifications(self.url, 1)
        

    def test_notification_does_not_appear_when_reminder_does_not_match_due_date(self):
        # Assign @johndoe to task
        self.task.assigned_to.set([self.user])

        # Only set the due date to 3 days after
        self.task.due_date = date.today() + timedelta(days=3)
        self.task.save()

        # No notifications should be present
        self.check_notifications(self.url, 0)

    def test_unassigned_users_do_not_get_notifications(self):
        # Switch to @janedoe who is unassigned
        self.client.logout()
        self.client.login(username=self.second_user.username, password='Password123')

        # No notifications should be present
        self.check_notifications(self.url, 0)
    
    def test_multiple_notifications_all_load_correctly(self):
        # Assign @johndoe to all tasks
        self.task.assigned_to.set([self.user])
        self.second_task.assigned_to.set([self.user])
        self.third_task.assigned_to.set([self.user])

        # 3 notification should be present
        self.check_notifications(self.url, 3)

    def test_notifications_are_automatically_sorted_by_priority(self):
        # Assign @johndoe to all tasks
        self.task.assigned_to.set([self.user])
        self.second_task.assigned_to.set([self.user])
        self.third_task.assigned_to.set([self.user])

        # Tasks should first be ordered by their ID if priority matches
        expected_order = [1, 2, 3]
        response = self.client.get(self.url)
        notifications_list = response.wsgi_request.notifications_list
        # Get IDs from notification list to check ordering
        id_list = [pair[1] for pair in notifications_list]
        self.assertListEqual(id_list, expected_order)

        # Change priority of 2nd and 3rd tasks
        self.second_task.priority = 'low'
        self.third_task.priority = 'high'
        self.second_task.save()
        self.third_task.save()

        # New order should be Task 3 first, Task 1 second, then Task 2 third
        expected_order = [3, 1, 2]
        new_response = self.client.get(self.url)
        new_notifications_list = new_response.wsgi_request.notifications_list
        new_id_list = [pair[1] for pair in new_notifications_list]
        self.assertListEqual(new_id_list, expected_order)
    
    def test_notifications_appear_on_every_displayable_url(self):
        # Assign @johndoe to task
        self.task.assigned_to.set([self.user])
        
        # Check if notifications exist for each page
        self.check_notifications(reverse('dashboard'), 1)
        self.check_notifications(reverse('create_team'), 1)
        self.check_notifications(reverse('create_task', kwargs={'pk': self.team.id}), 1)
        self.check_notifications(reverse('show_team', kwargs={'team_id': self.team.id}), 1)
        self.check_notifications(reverse('view_task', kwargs={'team_id': self.team.id, 'task_id': self.task.id}), 1)
        self.check_notifications(reverse('summary_report'), 1)
        self.check_notifications(reverse('activity_log', kwargs={'team_id': self.team.id, 'user_id': self.second_user.id}), 1)

    def test_high_priority_tasks_have_an_extra_notification_in_task_card(self):
        # Assign @johndoe to task
        self.task.assigned_to.set([self.user])

        task_card = self.find_task_card()

        # Check if task card does not have the notification inside it
        self.assertNotIn('notification-container', task_card)

        # Make task high priority
        self.task.priority = 'high'
        self.task.save()

        task_card = self.find_task_card()
        
        # Check if task card now has the notification inside it
        self.assertIn('notification-container', task_card)

        # Change due date
        self.task.due_date = date.today() + timedelta(days=3)
        self.task.save()

        task_card = self.find_task_card()

        # Task card should now not have notification anymore
        self.assertNotIn('notification-container', task_card)
    
    def test_mark_task_as_seen_discards_notification(self):
        # Assign @johndoe to task
        self.task.assigned_to.set([self.user])

        response = self.client.get(self.url)
        notifications_list = response.wsgi_request.notifications_list
        before_count = len(notifications_list)

        self.assertFalse(self.task.seen)

        # Simulate marking the task as seen
        url = f"{reverse('mark_as_seen')}?task_id={self.task.id}"
        self.client.get(url)

        # Making sure this task instance is updated
        self.task.refresh_from_db()

        self.assertTrue(self.task.seen)

        new_response = self.client.get(self.url)
        new_notifications_list = new_response.wsgi_request.notifications_list
        after_count = len(new_notifications_list)

        # Assert count decreased by 1
        self.assertEqual(after_count, before_count - 1)

    def check_notifications(self, url, number):
        response = self.client.get(url)
        notifications_list = response.wsgi_request.notifications_list
        self.assertEqual(len(notifications_list), number)
    
    def find_task_card(self):
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        task_card_index = html.find('<div class="card-body">')
        closing_div_index = html.find('</div>', task_card_index)
        return html[task_card_index:closing_div_index]