from django.shortcuts import render
from .models import Task

class TaskNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("TaskNotificationMiddleware is called for this request.")
        request.notifications_from_dashboard = self.get_notifications(request.user)
        response = self.get_response(request)
        return response

    def get_notifications(self, user):
        notifications = []
        teams = user.teams.all()

        for team in teams:
            tasks_for_each_team = Task.objects.filter(created_by=team)
            for task in tasks_for_each_team:
                if not task.seen and task.is_high_priority_due_soon():
                    message = f"Reminder: High priority task '{task.title}' is due on {task.due_date}."
                    notifications.append((message, task.id))
                elif not task.seen and task.is_other_priority_due_soon():
                    message = f"Reminder: {task.priority.capitalize()} priority task '{task.title}' is due on {task.due_date}."
                    notifications.append((message, task.id))

        return notifications