from django.db.models.signals import pre_save, post_save, pre_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from tasks.models import User, Team, Task, Activity_Log
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
import inspect
from datetime import datetime

#Gets the user that made the request
def get_requested_user():
    #for call in python code 
    for frame_record in inspect.stack():
        #find where we last got a get request
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request'] #get the request variable out of the frame
            return request.user
    else:
        return None

#Return the activity log for the user, or create a new one if they don't have one yet
def get_activity_log(user):
    if Activity_Log.objects.filter(user=user).exists():
        activity_log = Activity_Log.objects.get(user=user)
        return activity_log
    else:
        return Activity_Log.objects.create(log=[], user= user)

"""Basic callbacks"""
@receiver(user_logged_in)
def user_has_logged_in(sender, **kwargs):
    user = kwargs['user']#get_requested_user()
    if user!=None:
        #Here, I should save it in the activity log, get the user and either create a new activity log or get an old one
        activity_log = get_activity_log(user)
        #The below code is to remove the erroneous update callback
        #This is because when a user logs in, it also saves the model (this is from Abstract User)
        if len(activity_log.log)> 0:
            last_time = datetime.strptime(activity_log.log[len(activity_log.log)-1][1], "%d/%m/%Y, %H:%M:%S")
            if (datetime.now() - last_time).total_seconds() < 2:
                activity_log.log.pop(len(activity_log.log)-1) #remove the last entry (the update)
        activity_log.log.append((f'{user.username} has logged in', datetime.now().strftime("%d/%m/%Y, %H:%M:%S")))
        activity_log.save()

@receiver(user_logged_out)
def user_has_logged_out(sender, **kwargs):
    user = kwargs['user']
    if user!=None:
        #Here, I should save it in the activity log, get the user and either create a new activity log or get an old one
        activity_log = get_activity_log(user)
        activity_log.log.append((f'{user.username} has logged out', datetime.now().strftime("%d/%m/%Y, %H:%M:%S")))
        activity_log.save()

"""
Signal callbacks for every model save function
"""
#User Model
@receiver(post_save, sender=User)
def user_save(sender, **kwargs):
    user = kwargs['instance'] #get user instance we have created 
    created = kwargs['created']
    activity_log = get_activity_log(user) 
    current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    #if the user is not logged in, this must mean this user is signing up 
    if created: 
        activity_log.log.append((f'{user.username} signed up', current_time))
    else:
        #User exists, so there are updating their profile
        #don't differentiate about what they're doing (e.g. password, username),
        activity_log.log.append((f'{user.username} edited their user details', current_time))
    activity_log.save()


#Task Model
@receiver(pre_save, sender=Task)
def task_save(sender, **kwargs):
    user = get_requested_user()
    #This line is for tests, as get_requested_user() doesn't work in tests because we aren't doing real requests
    if user is None:
        user = getattr(kwargs['instance'], '_user',None)
    if user!=None:
        task = kwargs['instance']
        #created = kwargs['created'] #if we have created a new record
        #Here, I should save it in the activity log, get the user and either create a new activity log or get an old one
        activity_log = get_activity_log(user)
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        #Check what they are doing, editing or creating
        if not Task.objects.filter(pk=task.id).exists():#created:
            #They created a new task
            activity_log.log.append((f'{user.username} created a new task with title \'{task.title}\'', current_time))
        else:
            #check what they did to the task (doesn't include changes to m2m fields)
            old_task = Task.objects.get(pk=task.id)
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
            if old_task.task_completed!= task.task_completed:
                #changed completion
                completion = 'Complete' if eval(task.task_completed) else 'Incomplete'
                activity_log.log.append((f'{user.username} marked \'{old_task.title}\' as {completion}', current_time))
        activity_log.save()

#eam Model
@receiver(pre_save, sender=Team)
def team_save(sender, **kwargs):
    #We only use this to log creating teams, so the user has to be the admini
    team = kwargs['instance']
    user = team.admin_user 
    if user!=None:
        team = kwargs['instance']
        activity_log = get_activity_log(user)
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        if not Team.objects.filter(pk=team.id).exists():
            #They created a new task
            activity_log.log.append((f'{user.username} created a new team \'{team.team_name}\'', current_time))
        #no checks for edits because apart from many to many fields, you can't change teams
        activity_log.save()

"""Below Signals are for every ManyToMany field change"""
#Team model members m2m field
@receiver(m2m_changed, sender=Team.members.through)
def team_members_changed(sender, **kwargs):
    user = get_requested_user()
    #This line is for tests, as get_requested_user() doesn't work in tests because we aren't doing real requests
    if user is None:
        user = getattr(kwargs['instance'], '_user',None)
    if user!=None:
        activity_log = get_activity_log(user)
        team = kwargs['instance']
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        #check what they did to the team members
        action = kwargs['action']
        if action=="post_add":
            #team members added
            #say what members added 
            member_pk = list(kwargs['pk_set'])[0]
            member = team.members.all().filter(id =member_pk).first()#find most recent member added
            activity_log.log.append((f'{user.username} added {member.username} to \'{team.team_name}\'', current_time))
        elif action=="pre_remove":
            #team members removed
            #find the member removed. Don't know how though. Find different between two teams
            member_pk = list(kwargs['pk_set'])[0]
            member = team.members.all().filter(id =member_pk).first()
            activity_log.log.append((f'{user.username} removed {member.username} from \'{team.team_name}\'', current_time))
        activity_log.save()

#Task model assigned to m2m field
@receiver(m2m_changed, sender=Task.assigned_to.through)
def task_assigned_to_changed(sender, **kwargs):
    user = get_requested_user()
    #This line is for tests, as get_requested_user() doesn't work in tests because we aren't doing real requests
    if user is None:
        user = getattr(kwargs['instance'], '_user',None)
    if user!=None:
        activity_log = get_activity_log(user)
        task = kwargs['instance']
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        action = kwargs['action']
        #Unlike team members, we can add and remove multiple users at once
        if action=="post_add":
            #users assigned to task
            #say what members added 
            member_pks = kwargs['pk_set']
            for pk in member_pks:
                #for each member, show that they have been added/deleted
                member = task.assigned_to.all().filter(id =pk).first()#find most recent member added
                activity_log.log.append((f'{user.username} assigned {member.username} to the task \'{task.title}\'', current_time))
        elif action=="pre_remove":
            #users removed from assignment
            member_pks = kwargs['pk_set']
            for pk in member_pks:
                #for each member, show that they have been added/deleted
                member = task.assigned_to.all().filter(id =pk).first()#find most recent member added
                activity_log.log.append((f'{user.username} removed {member.username} from the task \'{task.title}\'', current_time))
        activity_log.save()

"""Signals for deleting entries"""
#Delete Task
@receiver(pre_delete, sender=Task)
def task_deleted(sender, **kwargs):
    user = get_requested_user()
    #This line is for tests, as get_requested_user() doesn't work in tests because we aren't doing real requests
    if user is None:
        user = getattr(kwargs['instance'], '_user',None)
    if user!=None:
        activity_log = get_activity_log(user)
        task = kwargs['instance']
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        activity_log.log.append((f'{user.username} deleted task {task.title}', current_time))
        activity_log.save()

#Delete Team
@receiver(pre_delete, sender=Team)
def team_deleted(sender, **kwargs):
    user = get_requested_user()
    #This line is for tests, as get_requested_user() doesn't work in tests because we aren't doing real requests
    if user is None:
        user = getattr(kwargs['instance'], '_user',None)
    if user!=None:
        activity_log = get_activity_log(user)
        team = kwargs['instance']
        current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        activity_log.log.append((f'{user.username} deleted team {team.team_name}', current_time))
        activity_log.save()


