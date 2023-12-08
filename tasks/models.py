from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date, timedelta
from libgravatar import Gravatar

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must consist of @ followed by at least three alphanumericals'
        )]
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    teams = models.ManyToManyField(
        "Team"
    )
    unread_notifications = models.IntegerField(default=1)

    """ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        blank= True,
        null=True,
    )
    """

    class Meta:
        """Model options."""

        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""

        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        
        return self.gravatar(size=60)


class Task(models.Model):
    """Model used for task creation, and assignment on team members"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    reminder_days = models.IntegerField(default=1, null=True, blank=True)
    title = models.CharField(max_length=30, blank=False)
    description = models.CharField(max_length=300, blank=True)
    due_date = models.DateField(blank=False, default=date.today)
    created_by = models.ForeignKey('Team', on_delete=models.CASCADE, null=True)
    assigned_to = models.ManyToManyField(User)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    task_completed = models.BooleanField(default=False)


    def is_high_priority_due_soon(self):
        today = date.today()
        reminder_days = int(self.reminder_days or 0)
        due_remind_date = today + timedelta(days=reminder_days)
        due_tomorrow = today + timedelta(days=1)
        return (self.reminder_days is not None and self.priority == "high" and self.due_date >= today and self.due_date <= due_remind_date and self.task_completed==False
    )

    def is_other_priority_due_soon(self):
        today = date.today()
        reminder_days = int(self.reminder_days or 0)
        due_remind_date = today + timedelta(days=reminder_days)
        due_tomorrow = today + timedelta(days=1)
        return (self.reminder_days is not None and (self.priority == "medium" or self.priority == "low") and self.due_date >= today and self.due_date <= due_remind_date  and self.task_completed==False
    )

        

class Team(models.Model):
    """Model used to represent a team"""
    team_name = models.CharField(max_length=50, blank=False)
    admin_user = models.ForeignKey(User, on_delete = models.CASCADE, blank = False, null = True)
    members = models.ManyToManyField(User, related_name ='membership', blank=True)

    def __str__(self):
        return self.team_name
    

class Notification(models.Model):
    user_notified = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
