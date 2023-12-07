from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, CreateTaskForm, CreateTeamForm, EditTaskForm, AssignTaskForm, SubmitTimeForm
from tasks.helpers import login_prohibited
from tasks.models import User, Task, Team, UserTimeSpent, TimeLog

@login_required
def search_users(request):
    """Display a list of searched users."""

    if request.method == "POST":
        q = request.POST["q"]
        results = q.split()
        if len(results) >= 2:
            queried_users = User.objects.filter(first_name__iexact = results[0]).filter(last_name__iexact = results[1])
        else:
            queried_users = User.objects.filter(first_name__iexact = q) | User.objects.filter(last_name__iexact = q)
        if(queried_users.count() == 0):
            return render(request, "search_users.html")
        
        return render(request, "search_users.html",{"q":q, "users":queried_users})
    else:
        return render(request, "search_users.html")

def dashboard(request):
    """Display the current user's dashboard."""
    current_user = request.user


    if not current_user.is_authenticated:

        return render(request, 'home.html', {'user': current_user})

    teams = current_user.teams.all()

    # Check if the user is associated with any teams
    if teams:
        # If the user is associated with teams, use the ID of the first team
        team_id = teams[0].id
    else:
        # If the user is not associated with any teams, set team id to 1
        team_id = 1

    tasks = Task.objects.all()


    # List of pairs matching each team with their created tasks
    team_tasks = []
    for team in teams:
        tasks_for_each_team = Task.objects.filter(created_by=team)
        team_tasks.append((team, tasks_for_each_team))


    return render(request, 'dashboard.html', {'user': current_user, 'teams': teams, 'team_id': team_id, 'team_tasks' : team_tasks})


@login_required
def create_team(request):
    """Page for a user to view their team and create a new team."""
    #current_user = request.user
    if request.method =='POST':
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            user = get_user(request)
            team = form.save(user)
            #add current user to their own team

            #user.team = team 

            team_id=team.id
            user.teams.add(team)
            #user.is_admin = True #make them admin of this team
            user.save()

            team.save()
            team.members.add(user)

            return redirect('show_team', team_id=team.id)
    else:
        form = CreateTeamForm()
    return render(request, 'create_team.html', {'form' : form})

@login_required
def delete_team(request, team_id):
    team = Team.objects.get(pk=team_id)

    team.delete()
    return redirect('dashboard')  
    
@login_required
def show_team(request, team_id):
    user = get_user(request)
    try:

        team = Team.objects.get(pk=team_id)
    except Team.DoesNotExist:
        admin_user = request.user
        team = Team.objects.create(team_name='Test Team', admin_user=admin_user)
        team.members.add(admin_user)
    is_admin = user == team.admin_user
    team_members = team.members.all()

    if request.method == "POST":
        if request.POST.get("userToAdd"):
            userToAddString = request.POST['userToAdd']
            userToAdd = User.objects.get(username = userToAddString)
            team.members.add(userToAdd)
            userToAdd.teams.add(team)
            return render(request, 'show_team.html', {'team' : team, 'team_members':team_members, 'is_admin':is_admin})
        else:
            # User has searched for something on the search bar
            q = request.POST["q"]
            results = q.split()
            if len(results) >= 2:
                queried_users = User.objects.filter(first_name__iexact = results[0]).filter(last_name__iexact = results[1])
            else:
                queried_users = User.objects.filter(first_name__iexact = q) | User.objects.filter(last_name__iexact = q)
            if(queried_users.count() > 0):
                return render(request, "show_team.html",{"q":q, "users":queried_users, "team": team, "team_id" : team_id, 'team_members':team_members, 'is_admin':is_admin})

    #get a list of the users in the team, and pass it in
    #also pass in the team itself to get the name
    return render(request, 'show_team.html', {'team' : team, 'team_members':team_members, 'is_admin':is_admin})

@login_required
def remove_member(request, team_id, member_username):
    user = get_user(request)
    team = get_object_or_404(Team, pk=team_id)

    # make sure that the user is an admin and the member exists in the team
    if user == team.admin_user:
        if member_username:
            member_to_remove = get_object_or_404(User, username=member_username)
            if team.members.filter(username=member_username).exists():
                team.members.remove(member_to_remove)
                member_to_remove.teams.remove(team)
            # remove user from assignment if assigned to any tasks
            updated_tasks = Task.objects.filter(assigned_to=member_to_remove)
            if updated_tasks:
                for task in updated_tasks:
                    task.assigned_to.remove(member_to_remove)

    return redirect('show_team', team_id=team_id)

@login_required
def remove_task(request,task_id):
    # Removal of task should also remove team members assosciated through CASCADE
    Task.objects.filter(pk=task_id).delete()
    return redirect("dashboard")

@login_required
def view_task(request, team_id=1, task_id=1):
    team = Team.objects.get(pk=team_id)
    task = Task.objects.get(pk=task_id)
    user =  get_user(request)
    alert_message = remove_message = None
    selected_users = (None, None)
    if request.method == "POST":

        #If we clicked the complete button 
        if "task_completion_value" in request.POST: #so this is for submitting the actual form itself
            if request.POST['task_completion_value'] == "Completed":
                task.task_completed = False #we clicked on Completed, so it must now be incomplete
            else:
                task.task_completed = True #we clicked on mark as done, so it is now done
        elif 'edit_submit' in request.POST:
            form = EditTaskForm(request.POST)
            #otherwise, we have submitted the whole form, so save it
            #get the value of the complete button 
            if form.is_valid():
                task.task_completed = request.POST['task_completed']
                form.save(task)
                return redirect('dashboard')
        elif 'assign_submit' in request.POST:
            form2 = AssignTaskForm(specific_team=team, specific_task=task, data=request.POST)
            if form2.is_valid():
                # This is all code to do with generating messages to be displayed
                selected_users = form2.save(task)
                if selected_users:
                    new_users_list = "<br>".join(f"- {user.username}" for user in selected_users[0])
                    alert_message = f"Successfully assigned:<br>{new_users_list}<br>to this task."
                    removed_users_list = "<br>".join(f"- {user.username}" for user in selected_users[1])
                    remove_message = f"Successfully removed:<br>{removed_users_list}<br>from this task."

    #fill the form with the values from the task itself to begin with
    form = EditTaskForm({'title':task.title, 'description':task.description, 'due_date': task.due_date})
    form2 = AssignTaskForm(specific_team=team, specific_task=task)


    # Checking if a user has been added / removed to a task
    if not selected_users[0]:
        alert_message = None
    if not selected_users[1]:
        remove_message = None

    # Checking if no users have been assigned to a task
    if not form2.get_assigned_users(task):
        alert_message = "This task has no assigned users." 

    

    context = {
        'team': team,
        'task': task,
        'form': form,
        'form2': form2,
        'alert_message': alert_message,
        'remove_message': remove_message,
        'new_users': selected_users[0],
        'removed_users': selected_users[1],
        'is_admin' : team.admin_user==user,
        'can_mark_as_complete': task.assigned_to.contains(user) or team.admin_user==user,
        'is_assigned':  task.assigned_to.contains(user)
    }

    return render(request, 'task_information.html', context)

@login_required
def summary_report(request):
    user = request.user
    teams = user.teams.all()

    user_times = UserTimeSpent.objects.filter(
        user=user,
    )

    time_logs = TimeLog.objects.filter(
        user=user,
    ).order_by('timestamp')

    context = {
        'user_times': user_times,
        'time_logs': time_logs,
        'teams': teams,
    }

    return render(request, 'summary_report.html', context)

@login_required
def submit_time(request, team_id, task_id): 
    task = Task.objects.get(pk=task_id)
    user = request.user
    if request.method == 'POST':
        form = SubmitTimeForm(request.POST)
        if form.is_valid():
            form.save(user, task)
    return redirect('view_task', team_id=team_id, task_id=task_id)

@login_required
def reset_time(request, team_id, task_id):
    action = request.GET.get('action')
    task = Task.objects.get(pk=task_id)
    user = request.user

    # Reset ALL time spent
    if action == 'total':
        all_user_time_spent = UserTimeSpent.objects.filter(task=task)
        for user_time_spent in all_user_time_spent:
            user_time_spent.time_spent = 0
            user_time_spent.save()
        task.time_spent = 0
        # Delete all time logs associated with the task
        TimeLog.objects.filter(task=task).delete() 
        task.save()

    # Reset only the user's time spent
    elif action == 'user':
        user_time_spent = get_object_or_404(
            UserTimeSpent,
            user=user,
            task=task,
        )
        task.time_spent -= user_time_spent.time_spent
        user_time_spent.time_spent = 0
        user_time_spent.save()
        # Delete all time logs associated with the user on the task
        TimeLog.objects.filter(user=user, task=task).delete()
        task.save()

    return redirect('view_task', team_id=team_id, task_id=task_id) 
    
@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')


class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

class CreateTaskView(LoginRequiredMixin, FormView):
    """Display the create task screen and handle creation of tasks."""

    template_name = 'create_task.html'
    form_class = CreateTaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_id = self.kwargs.get('pk')
        context['team_id'] = team_id
        return context

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the create task form."""
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the created task."""
        if form.is_valid():
            team_id = self.kwargs.get('pk')
            task = form.save(team_id=team_id)
            task_id = task.id
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after task creation."""

        return reverse('dashboard')