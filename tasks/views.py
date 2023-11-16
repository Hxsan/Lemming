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
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, CreateTaskForm, CreateTeamForm
from tasks.helpers import login_prohibited
from tasks.models import User
from tasks.models import Team


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
        # If the user is not associated with any teams, set team_id to None or handle it accordingly
        team_id = 1
    
    return render(request, 'dashboard.html', {'user': current_user, 'team_id': team_id})


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
            user.is_admin = True #make them admin of this team
            user.save()
            return redirect('show_team', team_id=team.id)
    else:
        form = CreateTeamForm()
    return render(request, 'create_team.html', {'form' : form})

#Change this view, this is just a prototype
@login_required
def show_team(request, team_id=1):
    user = get_user(request)
    try:
        team = Team.objects.get(pk=team_id)
    except Team.DoesNotExist:
        admin_user = request.user
        team = Team.objects.create(team_name='Test Team', admin_user=admin_user)
        team.members.add(admin_user)
    
    is_admin = user == team.admin_user

    team_members = team.members.all()

    #get a list of the users in the team, and pass it in
    #also pass in the team itself to get the name
    return render(request, 'show_team.html', {'team' : team, 'team_name': team.team_name, 'team_members':team_members, 'is_admin': is_admin})

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

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the create task form."""
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the created task."""
        if form.is_valid():
            form.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after task creation."""

        messages.add_message(self.request, messages.SUCCESS, "Task created successfully!")
        return reverse('dashboard')