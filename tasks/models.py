from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
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
    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        blank= True,
        null=True,
    )
    is_admin = models.BooleanField(default=False,blank=True)

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

    title = models.CharField(max_length=30, blank=False)
    description = models.CharField(max_length=300, blank=True)
    due_date = models.DateField(blank=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='created_task')
    assigned_to = models.ManyToManyField(User, related_name='assigned_task')
    

class Team(models.Model):
    """Model used to represent a team"""
    team_name = models.CharField(max_length=50, blank=False)

