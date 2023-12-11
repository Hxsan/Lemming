from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, CreateTaskForm, CreateTeamForm, EditTaskForm, AssignTaskForm
from tasks.helpers import login_prohibited
from tasks.models import User, Task, Team, Notification, Activity_Log
from datetime import datetime, timedelta

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
    if not teams.exists():
        # If the user is not associated with any teams
        return render(request, 'dashboard.html', {'user': current_user, 'teams': teams, 'team_id': 1, 'team_tasks': None})

    # Get the sorting method and order field from the request
    sort_type = request.GET.get('sort', 'default')
    order_type = request.GET.get('order', 'default')
    filter_type = request.GET.get('filter', None)
    search_query = request.GET.get('search_query', '')

    team_tasks = []
    task_fields = [field for field in Task._meta.get_fields() if not field.name.startswith('_')]

    # List to store notifications for all teams
    notifications_from_dashboard = []

    # Checks and retrieves due dates
    due_dates = []

    for team in teams:
        tasks_for_each_team = Task.objects.filter(created_by=team)

        # Due dates and notifications
        due_dates.extend(task for task in tasks_for_each_team if task.due_date)
        notifications_from_dashboard.extend(task for task in tasks_for_each_team if task.is_high_priority_due_soon() or task.is_other_priority_due_soon())

        # Apply sorting based on sort_type and order_type
        if search_query:
            tasks_for_each_team = tasks_for_each_team.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )
        elif order_type != 'default':
            tasks_for_each_team = tasks_for_each_team.order_by(order_type)
        elif sort_type in ['ascending', 'descending']:
            order_prefix = '' if sort_type == 'ascending' else '-'
            tasks_for_each_team = tasks_for_each_team.order_by(order_prefix + 'due_date')

        # Filter conditions
        filter_conditions = {}

        if filter_type in ['priorityLow', 'priorityMedium', 'priorityHigh']:
            filter_conditions['priority'] = filter_type.replace('priority', '').lower()
        elif filter_type in ['CompletedTrue', 'CompletedFalse']:
            filter_conditions['task_completed'] = (filter_type == 'CompletedTrue')

        if filter_conditions:
            tasks_for_each_team = tasks_for_each_team.filter(**filter_conditions)

        # Append tasks for the current team to the team_tasks list
        team_tasks.append((team, tasks_for_each_team))

    return render(request, 'dashboard.html', {'user': current_user,
                                               'teams': teams,
                                               'task_fields': task_fields,
                                               'team_tasks': team_tasks,
                                               'notifications_from_dashboard': notifications_from_dashboard,
                                               'due_dates': due_dates
                                               })

@login_required
def notification_hub(request):
    current_user = request.user
    teams = current_user.teams.all()
    team_tasks = []
    notifications  = []
    for team in teams:
        tasks_for_each_team = Task.objects.filter(created_by=team)
        for task in tasks_for_each_team:
            team_tasks.append(task)

    for task in team_tasks:
        if task.is_high_priority_due_soon():
            message = f"High priority task '{task.title}' is due on '{task.due_date}'."
            notifications.append(message)
            Notification.objects.create(user_notified=current_user, message=message)
            #current_user.unread_notifications +=1
            current_user.save()
        elif task.is_other_priority_due_soon():
            message = f"{task.priority.capitalize()} priority task '{task.title}' is due on '{task.due_date}'."
            notifications.append(message)
            Notification.objects.create(user_notified=current_user, message=message)
            #current_user.unread_notifications +=1
            current_user.save()
        
    context = {
        'notifications': notifications,
        'current_user': current_user,
        'current_tasks': team_tasks
    }

    return render(request, 'notification_hub.html', context)


@login_required
def create_team(request):
    """Page for a user to view their team and create a new team."""
    #current_user = request.user
    if request.method =='POST':
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            user = get_user(request)
            team = form.save(user)
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
    #Paginate the team members
    paginator = Paginator(team.members.all(), 5) 
    if request.method == "POST":
        page_number = request.POST.get("page")
        page_obj = paginator.get_page(page_number)
        if request.POST.get("userToAdd"):
            userToAddString = request.POST['userToAdd']
            userToAdd = User.objects.get(username = userToAddString)
            team.members.add(userToAdd)
            userToAdd.teams.add(team)
            return render(request, 'show_team.html', {'team' : team, 'team_members':team_members, 'is_admin':is_admin, "page_obj": page_obj})
        elif request.POST.get("q"):
            # User has searched for something on the search bar
            q = request.POST["q"]
            results = q.split()
            if q.startswith("@") and len(results) == 1 and len(q.strip()) > 1:
                queried_users = User.objects.filter(username__istartswith = results[0])
            elif len(results) >= 2 and not q.startswith("@"):
                queried_users = User.objects.filter(first_name__iexact = results[0]).filter(last_name__iexact = results[1])
            else:
                queried_users = User.objects.filter(first_name__iexact = q) | User.objects.filter(last_name__iexact = q)
                
            if(queried_users.count() > 0):
                page_number = request.POST.get("page")
                page_obj = paginator.get_page(page_number)
                return render(request, "show_team.html",{"q":q, "users":queried_users, "team": team, "team_id" : team_id, 'team_members': team_members, "page_obj": page_obj, 'is_admin':is_admin})
        else:
            return render(request, 'show_team.html', {'team' : team, "page_obj": page_obj, 'team_members': team_members, 'is_admin':is_admin})

    #get a list of the users in the team, and pass it in
    #also pass in the team itself to get the name
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'show_team.html', {'team' : team, 'team_members': team_members, "page_obj": page_obj, 'is_admin':is_admin})

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
    # Removal of task should also remove team members associated through CASCADE
    Task.objects.filter(pk=task_id).delete()
    return redirect("dashboard")

def mark_as_seen_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    if notification.user_notified == request.user:
        notification.delete()

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

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
            if datetime.now().date() > task.due_date:
                form.fields['due_date'].disabled = True
            #otherwise, we have submitted the whole form, so save it
            #get the value of the complete button 
            if form.is_valid():        
                task.task_completed = request.POST['task_completed']
                form.save(task)
                task.priority = request.POST.get('priority')
                task.reminder_days = request.POST.get('reminder_days')
                task.save()
                form.fields['priority'].initial = request.POST.get('priority')
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
    form = EditTaskForm({'title':task.title, 'description':task.description, 'due_date': task.due_date, 'priority': task.priority, 'reminder_days': task.reminder_days})
    #check if due date has passed, if it has, make due_date not editable
    if datetime.now().date() > task.due_date:
        form.fields['due_date'].disabled = True
        #form.add_prefix('due_date', 'This task is overdue')
        #form.fields['due_date'].help_text = "This task is overdue"
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
        'can_mark_as_complete': task.assigned_to.contains(user) or team.admin_user==user
    }

    return render(request, 'task_information.html', context)

@login_required
def user_activity_log(request, team_id, user_id):
    user = User.objects.get(pk=user_id)
    if Activity_Log.objects.filter(user=user).exists():
        log = Activity_Log.objects.get(user=user)
        log.log.reverse() #reverse to have it in order of most recent
        paginator = Paginator(log.log, 10)  # Show 10 logs per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, "activity_log.html", {"page_obj": page_obj})
    #otherwise, redirect them back to show team
    return redirect('show_team', team_id=team_id)

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