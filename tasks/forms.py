"""Forms for the tasks app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, Task, Team, TimeSpent, TimeLog
from datetime import date, timedelta, datetime

class LogInForm(forms.Form):
    """Form enabling registered users to log in."""

    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def get_user(self):
        """Returns authenticated user if possible."""

        user = None
        if self.is_valid():
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        return user


class UserForm(forms.ModelForm):
    """Form to update user profiles."""
    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
    
class NewPasswordMixin(forms.Form):
    """Form mixing for new_password and password_confirmation fields."""

    new_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(),
        validators=[RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$',
            message='Password must contain an uppercase character, a lowercase '
                    'character and a number'
            )]
    )
    password_confirmation = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    def clean(self):
        """Form mixing for new_password and password_confirmation fields."""

        super().clean()
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if new_password != password_confirmation:
            self.add_error('password_confirmation', 'Confirmation does not match password.')


class PasswordForm(NewPasswordMixin):
    """Form enabling users to change their password."""

    password = forms.CharField(label='Current password', widget=forms.PasswordInput())

    def __init__(self, user=None, **kwargs):
        """Construct new form instance with a user instance."""
        
        super().__init__(**kwargs)
        self.user = user

    def clean(self):
        """Clean the data and generate messages for any errors."""

        super().clean()
        password = self.cleaned_data.get('password')
        if self.user is not None:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error('password', "Password is invalid")

    def save(self):
        """Save the user's new password."""

        new_password = self.cleaned_data['new_password']
        if self.user is not None:
            self.user.set_password(new_password)
            self.user.save()
        return self.user


class SignUpForm(NewPasswordMixin, forms.ModelForm):
    """Form enabling unregistered users to sign up."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def save(self):
        """Create a new user."""

        super().save(commit=False)
        user = User.objects.create_user(
            self.cleaned_data.get('username'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('new_password'),
        )
        return user


class CreateTaskForm(forms.ModelForm):
    """Form enabling users to create a task."""

    class Meta:
        """Form options."""

        model = Task
        fields = ['title', 'description', 'due_date', 'priority']
        exclude = ['created_by', 'task_completed']
        widgets = { 'description': forms.Textarea(),
                    'due_date': forms.DateInput(attrs={'class': 'form-control', 'type':'date', 'min': date.today}), 
                    'priority': forms.Select(attrs={'class': 'form-control'})}

    def __init__(self, user=None, **kwargs):
        """Construct new form instance with a user instance."""
        super().__init__(**kwargs)
        self.user = user
    
    def save(self, team_id=None):
        """Create a new task."""

        created_task = super().save(commit=False)
        created_task.due_date = self.cleaned_data.get('due_date')
        if team_id is not None:
            created_task.created_by = self.user.teams.get(pk=team_id)

        created_task.save()

        return created_task
        
        
class CreateTeamForm(forms.ModelForm):
    class Meta:
        """Form options."""

        model = Team
        fields = ['team_name']
        #exclude = ['team_id']

    def save(self, user):
        super().save(commit=False)
        team = Team.objects.create(
            team_name=self.cleaned_data.get('team_name'), 
            admin_user=user,
        )
        user.teams.add(team)
        team.members.add(user)
        return team

"""Maybe need a form of this type eventually"""    
#But this form isn't the actual form we will use
class EditTaskForm(forms.ModelForm):

    class Meta:
        """Form options."""
        max_allowed_days = 7
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'reminder_days']
        exclude = ['created_by', 'task_completed']
        widgets = {'title': forms.TextInput(attrs={'class': 'form-control','id':'task_title'}),
                'description': forms.Textarea(attrs={'class': 'form-control','id':'task_description'}),
                'due_date': forms.DateInput(attrs={'class': 'form-control', 'type':'date', 'min': date.today}),
                'priority': forms.Select(attrs={'class': 'form-control'}),
                'reminder_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': max_allowed_days})}
        labels = {
            'reminder_days': 'Remind me of this task(days before)',
        }
        
    
    
    def is_valid(self):
        original_valid = super().is_valid()
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        reminder_days = cleaned_data.get('reminder_days')
        #Only check if task not overdue        
        today = date.today()
        max_allowed_days = (due_date - today).days 
        return original_valid and reminder_days < max_allowed_days+1 and (self.fields['due_date'].disabled or self.cleaned_data['due_date']>(date.today() - timedelta(1))) #ensure due date is later or equal to today
    
    def save(self, old_task):
        task = super().save(commit=False)
        task.id = old_task.id
        task.created_by = old_task.created_by
        task.task_completed = old_task.task_completed

        task.save()
        return task

class AssignTaskForm(forms.Form):
    usernames = forms.ModelMultipleChoiceField(
        queryset=None,
        to_field_name='username',
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, specific_team, specific_task, *args, **kwargs):
        super(AssignTaskForm, self).__init__(*args, **kwargs)
        self.fields['usernames'].queryset = specific_team.members.all()

        assigned_users = specific_task.assigned_to.all()
        self.initial['usernames'] = [user.username for user in assigned_users]

    def get_assigned_users(self, specific_task):
        return specific_task.assigned_to.all()

    def save(self, task):
        original_users = set(task.assigned_to.all())
        #task.assigned_to.clear()
        selected_users = self.cleaned_data['usernames']
        #task.assigned_to.add(*selected_users)

        #remove users not in the final assignment
        for user in task.assigned_to.all():
            if user not in selected_users:
                task.assigned_to.remove(user)

        new_users = set(selected_users) - original_users
        removed_users = original_users - set(selected_users)
        task.assigned_to.add(*new_users) #add the new users

        return (list(new_users), list(removed_users))

class SubmitTimeForm(forms.Form):
    class Meta:
        model = Task
        fields = ['time_spent']

    hours = forms.IntegerField(required=False, min_value=0)
    minutes = forms.IntegerField(required=False, min_value=0)
    seconds = forms.IntegerField(required=False, min_value=0)

    def clean(self):
        cleaned_data = super().clean()
        hours = cleaned_data.get('hours')
        minutes = cleaned_data.get('minutes')
        seconds = cleaned_data.get('seconds')
        self.cleaned_hours = hours if hours is not None and hours else 0
        self.cleaned_minutes = minutes if minutes is not None and minutes else 0
        self.cleaned_seconds = seconds if seconds is not None and seconds else 0


    def save(self, user, task):
        total_seconds = self.cleaned_hours * 3600 + self.cleaned_minutes * 60 + self.cleaned_seconds
        
        # Get or create time spent instance of user on a task
        user_time_spent, created = TimeSpent.objects.get_or_create(
            user=user,
            task=task,
            defaults={'time_spent': total_seconds}
        )

        # Update instance if found in database
        if not created:
            user_time_spent.time_spent += total_seconds
        
        user_time_spent.save()

        # Log the entry with a specific timestamp
        TimeLog.objects.create(
            user=user,
            task=task,
            logged_time=total_seconds,
            timestamp=datetime.now()
        )

        return task