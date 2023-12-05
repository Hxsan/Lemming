"""Unit tests for the """
from django.core.exceptions import ValidationError
from django.core.handlers import base
from django.test import TestCase
from tasks.models import Team, User, Activity_Log, Task
from django.urls import reverse
from tasks.signals import *
from django.db.models.signals import m2m_changed
from django.db.models.signals import pre_save, post_save, pre_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from datetime import datetime
from django.http import HttpRequest
import inspect


#test the generation of each signal and what activity log stuff is there

class SignalsTestCase(TestCase):
    """Unit tests for the """

    fixtures = [
        'tasks/tests/fixtures/default_user.json', 
        'tasks/tests/fixtures/other_users.json',
    ]
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.member_with_log = User.objects.get(username='@janedoe') #we will be getting this user's activity log
        self.member_without_log = User.objects.get(username='@petrapickles') #no log for this user
        #Create team and add members to the team
        self.team = Team.objects.create(team_name='Team 1',admin_user=self.user)
        self.task = Task.objects.create(title="Task1", description="This is a task", due_date=datetime.today())
        self.form_input = {
            'title': 'Task1',
            'description': 'This is a task',
            'due_date': datetime.today(),
            'edit_submit': 'Save', #these two values to simulate the request information sent
            'task_completed': False,
        }
        self.task.created_by = self.team 
        self.url = reverse("view_task", args=[self.team.id, self.task.id]) #a random url to use for testing
        self.team.members.set([self.user, self.member_with_log])
        self.user.teams.set([self.team])
        self.member_with_log.teams.set([self.team])
        self.activity_log = Activity_Log.objects.get(user=self.user)
        self.disconnect_signals()
    
    def disconnect_signals(self):
        #Disconnect all signals for now
        m2m_changed.disconnect(task_assigned_to_changed, sender=Task.assigned_to.through)
        m2m_changed.disconnect(team_members_changed, sender=Team.members.through)
        user_logged_in.disconnect(user_has_logged_in)
        user_logged_out.disconnect(user_has_logged_out)
        post_save.disconnect(user_save, sender=User)
        pre_save.disconnect(team_save, sender=Team)
        pre_save.disconnect(task_save, sender=Task)
        pre_delete.disconnect(task_deleted, sender=Task)
        pre_delete.disconnect(team_deleted, sender=Team)


    #test for each signal and function

    def test_get_requested_user(self):
        self.client.login(username=self.user.username, password='Password123')
        response = self.client.get(reverse('dashboard'))#(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        for frame in inspect.stack():
            print(frame)
        self.assertEqual(get_requested_user(), self.user)

    #Return the activity log for the user, or create a new one if they don't have one yet
    def test_get_activity_log_function(self):
        #test it gets correct activity log
        self.assertEqual(Activity_Log.objects.get(user=self.user), get_activity_log(self.user))
        #test it creates new one with a new user
        new_user = User.objects.create(username='@newuser', first_name='New', last_name='user', email='newuser@org.uk', password="Password123")
        self.assertFalse(Activity_Log.objects.filter(user=new_user).exists()) #it doesn't exist
        get_activity_log(new_user)
        self.assertEqual(Activity_Log.objects.get(user=new_user), get_activity_log(new_user)) #now it does

    """

    def test_user_log_in_signal(self):
        user_logged_in.connect(user_has_logged_in)
        self.client.login(username=self.user.username, password='Password123')
        self.activity_log.refresh_from_db()
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        #check activity log includes the new entry
        self.assertEqual(self.activity_log.log[0], [f'{self.user.username} has logged in', current_time])

    def test_user_log_out_signal(self):
        user_logged_out.connect(user_has_logged_out)
        self.client.login(username=self.user.username, password='Password123')
        self.client.logout()
        self.activity_log.refresh_from_db()
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        #check activity log includes the new entry
        self.assertEqual(self.activity_log.log[1], [f'{self.user.username} has logged out', current_time])

    #User Model
    def test_user_save_signal(self):
        post_save.connect(user_save, sender=User)
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        self.user.first_name = "Jon"
        self.user.save()
        self.activity_log.refresh_from_db()
        #check activity log includes the new entry
        self.assertEqual(self.activity_log.log[1], [f'{self.user.username} edited their user details', current_time])
        """

    #Task Model
    def test_task_save_signal(self):
        self.client.login(username=self.user.username, password='Password123')
        pre_save.connect(task_save, sender=Task)
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        old_title = self.task.title
        self.task.title = "NewTitle"
        self.task.save()
        self.activity_log.refresh_from_db()
        #check for each possibility of task
        #self.assertEqual(self.activity_log.log[1], [f'{self.user.username} changed task \'{old_title}\'s title to {self.task.title}', current_time])
        """
        if old_task.title!=task.title:
            #changed title
            activity_log.log.append((f'{user.username} changed task \'{old_task.title}\'s title to {task.title}', current_time))
        if old_task.description!=task.description:
            #changed description
            activity_log.log.append((f'{user.username} changed task \'{old_task.title}\'s description to {task.description}', current_time))
        if old_task.due_date!=task.due_date:
            #changed due date
            activity_log.log.append((f'{user.username} updated task \'{old_task.title}\'s due date to {task.due_date}', current_time))
        #have to use eval here because models.BooleanField is stored as a string, but it comes out as a boolean
        if old_task.task_completed!=eval(task.task_completed):
            #changed completion
            completion = 'Complete' if eval(task.task_completed) else 'Incomplete'
            activity_log.log.append((f'{user.username} marked \'{old_task.title}\' as {completion}', current_time))
        """
        

    def test_team_save_signal(sender, **kwargs):
        pre_save.connect(team_save, sender=Team)
        pass

    #Team model members m2m field
    def team_members_changed_signal(sender, **kwargs):
        m2m_changed.connect(team_members_changed, sender=Team.members.through)
        pass

    #Task model assigned to m2m field
    def task_assigned_to_changed_signal(sender, **kwargs):
        m2m_changed.connect(task_assigned_to_changed, sender=Task.assigned_to.through)
        pass

    #Delete Task
    def task_deleted_signal(sender, **kwargs):
        pre_delete.connect(task_deleted, sender=Task)
        pass

    #Delete Team
    def team_deleted_signal(sender, **kwargs):
        pre_delete.connect(team_deleted, sender=Team)
        pass

