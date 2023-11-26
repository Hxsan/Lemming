"""Forms for the tasks app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from .models import User, Task, Team
from datetime import date

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
        fields = ['title', 'description', 'due_date']
        exclude = ['created_by', 'task_completed']
        widgets = { 'description': forms.Textarea(),
                    'due_date': forms.DateInput(attrs={'class': 'form-control', 'type':'date', 'min': date.today})}

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
        exclude = ['team_id']

    def save(self, user):
        super().save(commit=False)
        team = Team.objects.create(
            team_name=self.cleaned_data.get('team_name'), 
            admin_user=user,
        )
        return team

"""Maybe need a form of this type eventually"""    
#But this form isn't the actual form we will use
class EditTaskForm(forms.ModelForm):
    class Meta:
        """Form options."""

        model = Task
        fields = ['title', 'description', 'due_date']
        exclude = ['created_by', 'task_completed']
        widgets = {'title': forms.TextInput(attrs={'class': 'form-control','id':'task_title'}),
                   'description': forms.Textarea(attrs={'class': 'form-control','id':'task_description'}),
                   'due_date': forms.DateInput(attrs={'class': 'form-control', 'type':'date', 'min': date.today})}

    def save(self, old_task):
        task = super().save(commit=False)
        task.id = old_task.id
        task.created_by = old_task.created_by
        task.task_completed = old_task.task_completed
        task.save()
        return task

 
# class AssignTaskForm(forms.ModelForm):
#     class Meta:
#         """Form options."""

#         model = User
#         fields = []
    
#     """Custom form displaying users in a list that can be checkboxed"""
#     # User.objects.all() needs to be changed to User.objects.filter()
#     # The filter being only the selected team's users
#     # Displaying all users is used now because the template isnt made yet.

#     usernames = forms.ModelMultipleChoiceField(
#         queryset=User.objects.all(),
#         to_field_name='username',
#         widget=forms.CheckboxSelectMultiple,
#     )

#     def assign_task(self):
#         """Assign task to users selected"""
#         selected_usernames = self.cleaned_data.get('usernames')
#         list_of_usernames = list(selected_usernames.values_list('username', flat=True))
#         selected_users = User.objects.filter(username__in=list_of_usernames)

#         # This can only be done when the task is passed from views
#         """ 
#         for user in selected_users:
#             selected_task.assigned_to.add(user)
#         """

#         return selected_users
