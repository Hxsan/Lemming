# "Tests of the search and add to team functionality."""

# from django.test import TestCase
# from django.urls import reverse
# from tasks.models import User, Team
# from tasks.forms import CreateTeamForm

# class ShowTeamViewTestCase(TestCase):
#     """Tests of the show team view."""

#     fixtures = [
#         'tasks/tests/fixtures/default_user.json',
#         'tasks/tests/fixtures/other_users.json'
#     ]

#     def setUp(self):
#         self.client.login(username='@johndoe', password='Password123')
#         self.client.post(reverse("create_team"), {'team_name':'NewTeam'}, follow = True)
#         self.url = reverse('show_team')
#         self.user = User.objects.get(username='@johndoe')
    
#     def test_user_appears_in_search(self):
#         q = "Jane"
#         userToReturn = User.objects.get(username = "@janedoe")
#         response = self.client.post(reverse("show_team"), {'q': q })
#         self.assertEqual(response.users , userToReturn)

#     def test_user_does_not_appear_in_search(self):
#         q = "jan"
#         userToReturn = User.objects.get(username = "@jandoe")
#         response = self.client.post(reverse("show_team") {'q' : q})
#         self.assertNotEqual(response.users, userToReturn)

