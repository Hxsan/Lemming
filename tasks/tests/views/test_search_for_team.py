"""Tests of the search and add to team functionality."""

from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team, Task
from tasks.forms import CreateTeamForm

class SearchTeamViewTestCase(TestCase):
    """Tests of the search team functionality."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]

    def setUp(self):
        self.client.login(username='@johndoe', password='Password123')
        self.client.post(reverse("create_team"), {'team_name':'NewTeam'}, follow = True)
        self.url = "/dashboard/show_team/1/"
        self.user = User.objects.get(username='@johndoe')
        self.team = self.user.teams.all()[0]
    
    def test_user_appears_in_search_when_correct_spelling(self):
        q = "Jane"
        userToReturn = User.objects.get(username = "@janedoe")
        response = self.client.post(self.url, {"q":q, "users":userToReturn, "team": self.team, "team_id" : 1, 'team_members': self.team.members.all(), 'is_admin': True}, follow=True)
        self.assertContains(response, "Jane Doe")

    def test_user_appears_in_search_with_username(self):
        q = "@jan"
        userToReturn = User.objects.get(username = "@janedoe")
        response = self.client.post(self.url, {"q":q, "users":userToReturn, "team": self.team, "team_id" : 1, 'team_members': self.team.members.all(), 'is_admin': True}, follow=True)
        self.assertContains(response, "Jane Doe")

    def test_user_does_not_appear_in_search_when_incorrect_spelling(self):
        q = "jan"
        userToReturn = User.objects.get(username = "@janedoe")
        response = self.client.post(self.url, {"q":q, "users":userToReturn, "team": self.team, "team_id" : 1, 'team_members': self.team.members.all(), 'is_admin': True}, follow=True)
        self.assertNotContains(response, "Jane Doe")

    def test_user_in_team_doesnt_appear_in_search(self):
        q = "John"
        userToReturn = User.objects.get(username = "@johndoe")
        response = self.client.post(self.url, {"q":q, "users":userToReturn, "team": self.team, "team_id" : 1, 'team_members': self.team.members.all(), 'is_admin': True}, follow=True)
        self.assertNotContains(response, "John Doe")

class AddToTeamViewTestCase(TestCase):
    """Tests of the add to team functionality."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]

    def setUp(self):
        self.client.login(username='@johndoe', password='Password123')
        self.client.post(reverse("create_team"), {'team_name':'NewTeam'}, follow = True)
        self.url = "/dashboard/show_team/1/"
        self.user = User.objects.get(username='@johndoe')
        self.team = self.user.teams.all()[0]  

    def test_user_added_to_team(self):
        q = "Jane" 
        userToReturn = User.objects.get(username = "@janedoe")
        response = self.client.post(self.url, {"q":q, "users":userToReturn, "team": self.team, "team_id" : 1, 'team_members': self.team.members.all(), 'is_admin': True, 
                                                                'userToAdd': '@janedoe'}, follow=True)
        self.assertEqual(self.team,userToReturn.teams.all()[0])

    def test_user_displays_on_team_list_once_added(self):
        q = "Jane" 
        userToReturn = User.objects.get(username = "@janedoe")
        response = self.client.post(self.url, {"q":q, "users":userToReturn, "team": self.team, "team_id" : 1, 'team_members': self.team.members.all(), 'is_admin': True, 
                                                                'userToAdd': '@janedoe'}, follow=True)
        self.assertContains(response, "@janedoe")
    
class RemoveTaskViewTestCase(TestCase):
    """Tests for the remove task functionality."""
    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]
    
    def setUp(self):
        self.client.login(username='@johndoe', password='Password123')
        self.client.post(reverse("create_team"), {'team_name':'NewTeam'}, follow = True)
        self.url = "/dashboard/create_task/1/"
        self.user = User.objects.get(username='@johndoe')
        self.team = self.user.teams.all()[0] 
        self.form_input = {
            'title' : 'test',
            'description' : 'test task',
            'due_date' : '02/02/2024'
        }

    def test_task_removes_successfully(self):
        response = self.client.post(self.url, self.form_input, follow=True)
        task = Task.objects.get(title='test')
        self.removeurl = "/dashboard/view-task/1/remove_task/"
        response = self.client.post(self.removeurl)
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(title='test')
        
