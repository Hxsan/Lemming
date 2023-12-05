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
from datetime import datetime, timedelta
from django.http import HttpRequest
import inspect
from django.test import RequestFactory
from tasks.views import view_task
import time

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
        self.task = Task.objects.create(title="Task1", description="This is a task", due_date=datetime.now())
        self.task.task_completed = "False"
        self.form_input = {
            'title': 'Task1',
            'description': 'This is a task',
            'due_date': datetime.now(),
            'edit_submit': 'Save', #these two values to simulate the request information sent
            'task_completed': False,
        }
        self.task.created_by = self.team 
        self.task._user = self.user #custom attr for testing because can't get user from signals in tests
        self.team._user = self.user
        self.url = reverse('view_task', kwargs={'team_id': self.team.id, 'task_id':self.task.id}) #a random url to use for testing
        self.team.members.set([self.user, self.member_with_log])
        self.user.teams.set([self.team])
        self.member_with_log.teams.set([self.team])
        self.activity_log = Activity_Log.objects.get(user=self.user)
        self.format = "%d/%m/%Y, %H:%M:%S" 
        self.disconnect_signals()
        self.activity_log.log = []
        self.activity_log.save()
    
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

    #Return the activity log for the user, or create a new one if they don't have one yet
    def test_get_activity_log_function(self):
        #test it gets correct activity log
        self.assertEqual(Activity_Log.objects.get(user=self.user), get_activity_log(self.user))
        #test it creates new one with a new user
        new_user = User.objects.create(username='@newuser', first_name='New', last_name='user', email='newuser@org.uk', password="Password123")
        self.assertFalse(Activity_Log.objects.filter(user=new_user).exists()) #it doesn't exist
        get_activity_log(new_user)
        self.assertEqual(Activity_Log.objects.get(user=new_user), get_activity_log(new_user)) #now it does

    def test_user_log_in_signal(self):
        user_logged_in.connect(user_has_logged_in)
        self.client.login(username=self.user.username, password='Password123')
        self.activity_log.refresh_from_db()
        current_time = datetime.now()
        #check activity log includes the new entry
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} has logged in')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    def test_user_log_out_signal(self):
        user_logged_out.connect(user_has_logged_out)
        self.client.login(username=self.user.username, password='Password123')
        self.client.logout()
        self.activity_log.refresh_from_db()
        current_time = datetime.now()
        #check activity log includes the new entry
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} has logged out')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    #User Model
    def test_user_sign_up_signal(self):
        post_save.connect(user_save, sender=User)
        current_time = datetime.now()
        new_user = User.objects.create(username='@newuser', first_name='New', last_name='user', email='newuser@org.uk', password="Password123")
        activity_log = Activity_Log.objects.get(user=new_user)
        #check activity log includes the new entry
        self.assertEqual(activity_log.log[0][0], f'{new_user.username} signed up')
        self.assertEqual(datetime.strptime(activity_log.log[0][1], self.format).date(), current_time.date())

    def test_user_edit_signal(self):
        post_save.connect(user_save, sender=User)
        current_time = datetime.now()
        self.user.first_name = "Jon"
        self.user.save()
        self.activity_log.refresh_from_db()
        #check activity log includes the new entry
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} edited their user details')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    #Task Model
    def test_task_create_signal(self):
        pre_save.connect(task_save, sender=Task) 
        current_time = datetime.now()
        #create a new task
        task = Task.objects.create(title="Task1", description="This is a task", due_date=datetime.now())
        task._user = self.user
        Task.objects.filter(pk=task.id).delete() #delete it so we can redo the create signal with _user attached
        task.save()
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} created a new task with title \'{task.title}\'')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())
    
    def test_task_save_signal_title_change(self):
        pre_save.connect(task_save, sender=Task) 
        current_time = datetime.now()
        #Test title change
        old_title = self.task.title
        self.task.title = "NewTitle"
        self.task.save()
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} changed task \'{old_title}\'s title to {self.task.title}')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())
    
    def test_task_save_signal_change_change_description(self):
        pre_save.connect(task_save, sender=Task) 
        current_time = datetime.now()
        self.task.description = "NewDescription"
        self.task.save()
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} changed task \'{self.task.title}\'s description to {self.task.description}')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    def test_task_save_signal_change_due_date(self):
        pre_save.connect(task_save, sender=Task) 
        current_time = datetime.now()
        self.task.due_date = datetime.now() + timedelta(1)
        self.task.save()
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} updated task \'{self.task.title}\'s due date to {self.task.due_date}')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    def test_task_save_signal_change_completion(self):
        pre_save.connect(task_save, sender=Task) 
        current_time = datetime.now()
        self.task.task_completed= "True"
        self.task.save()
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[1][0], f'{self.user.username} marked \'{self.task.title}\' as Complete')
        self.assertEqual(datetime.strptime(self.activity_log.log[1][1], self.format).date(), current_time.date())


    def test_team_save_signal(self):
        pre_save.connect(team_save, sender=Team)
        #create a new team
        current_time = datetime.now()
        self.team = Team.objects.create(team_name='Team 2',admin_user=self.user)
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} created a new team \'{self.team.team_name}\'')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())


    #Team model members m2m field
    def test_team_members_added_signal(self):
        m2m_changed.connect(team_members_changed, sender=Team.members.through)
        current_time = datetime.now()
        self.team.members.add(self.member_without_log)
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} added {self.member_without_log.username} to \'{self.team.team_name}\'')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    def test_team_members_removed_signal(self):
        m2m_changed.connect(team_members_changed, sender=Team.members.through)
        current_time = datetime.now()
        self.team.members.remove(self.member_with_log)
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} removed {self.member_with_log.username} from \'{self.team.team_name}\'')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    #Task model assigned to m2m field
    def test_assign_to_task_signal(self):
        m2m_changed.connect(task_assigned_to_changed, sender=Task.assigned_to.through)
        current_time = datetime.now()
        self.task.assigned_to.add(self.member_with_log)
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} assigned {self.member_with_log.username} to the task \'{self.task.title}\'')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())

    def test_remove_from_task_signal(self):
        m2m_changed.connect(task_assigned_to_changed, sender=Task.assigned_to.through)
        current_time = datetime.now()
        #add and remove
        self.task.assigned_to.add(self.member_with_log)
        self.task.assigned_to.remove(self.member_with_log)
        self.activity_log.refresh_from_db()
        #check for add and remove
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} assigned {self.member_with_log.username} to the task \'{self.task.title}\'')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())
        self.assertEqual(self.activity_log.log[1][0], f'{self.user.username} removed {self.member_with_log.username} from the task \'{self.task.title}\'')
        self.assertEqual(datetime.strptime(self.activity_log.log[1][1], self.format).date(), current_time.date())

    #Delete Task
    def task_deleted_signal(self):
        pre_delete.connect(task_deleted, sender=Task)
        current_time = datetime.now()
        old_title = self.task.title
        Task.objects.filter(pk=self.task.id).delete()
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} deleted task {old_title}')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())


    #Delete Team
    def team_deleted_signal(self):
        pre_delete.connect(team_deleted, sender=Team)
        current_time = datetime.now()
        old_team_name = self.team.team_name
        Team.objects.filter(pk=self.team.id).delete()
        self.activity_log.refresh_from_db()
        self.assertEqual(self.activity_log.log[0][0], f'{self.user.username} deleted team {old_team_name}')
        self.assertEqual(datetime.strptime(self.activity_log.log[0][1], self.format).date(), current_time.date())
