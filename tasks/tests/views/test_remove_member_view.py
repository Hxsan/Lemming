"""Tests of the remove member view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team, Task

class RemoveMemberViewTests(TestCase):
    """Tests of the remove member view."""
    fixtures = ['tasks/tests/fixtures/default_user.json', 'tasks/tests/fixtures/other_users.json']

    def setUp(self):
        # create objects for tests
        self.admin_user = User.objects.get(username='@johndoe')
        self.non_admin_user = User.objects.get(username='@janedoe')

        self.client.login(username='@johndoe', password='Password123')
        self.team = Team.objects.create(team_name='Test Team', admin_user=self.admin_user)
        self.team.members.add(self.admin_user, self.non_admin_user)

    def test_remove_member(self):
        # try to remove a member that isnt the admin
        member_to_remove = self.non_admin_user

        # assign task to member
        task = Task.objects.create(title='Test Task')
        task.assigned_to.add(member_to_remove)

        response = self.client.post(
            reverse('remove_member', args=[self.team.id, member_to_remove.username])
        )
        # making sure that it redirects to show_team view
        self.assertRedirects(response, reverse('show_team', args=[self.team.id]))

        # Check that the member is removed from the team
        self.assertNotIn(member_to_remove, self.team.members.all())

        # Check that the member is removed from the assigned tasks
        task.refresh_from_db()
        self.assertNotIn(member_to_remove, task.assigned_to.all())

    def test_remove_button_shown_for_admin(self):
        # Make a get request to the show_team view as the admin
        response = self.client.get(reverse('show_team', args=[self.team.id]))
        # Check that the "Remove" button is present in the HTML
        self.assertContains(response, 'Remove Member', html=True)

    def test_remove_button_not_shown_for_non_admin(self):
        # Make a get request to show_team as a non-admin member
        self.client.login(username='@janedoe', password='Password123')
        response = self.client.get(reverse('show_team', args=[self.team.id]))

        # making sure the html doesnt show the remove buuton for non-admin member
        self.assertNotContains(response, 'Remove Member', html=True)
