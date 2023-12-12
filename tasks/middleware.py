from django.shortcuts import render
from .models import Task

class TaskNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.notifications_list = self.get_notifications(request.user)
        response = self.get_response(request)
        return response

    def key_for_sorting(self, notification_and_task):
        priority_map = {'high': 1, 'medium': 2, 'low': 3}
        task_id = notification_and_task[1]
        return priority_map[Task.objects.get(pk=task_id).priority]

    def get_notifications(self, user):
        notifications = []
        if user.is_authenticated:
            teams = user.teams.all()
        
            for team in teams:
                tasks_for_each_team = Task.objects.filter(created_by=team)
                for task in tasks_for_each_team:
                    
                    if not task.seen and task.is_high_priority_due_soon() and user in task.assigned_to.all():
                        message = f"<strong>REMINDER:</strong> <span style='color: red;'>High</span> priority task '{task.title}' is due on {task.due_date}."
                        notifications.append((message, task.id))
                    elif not task.seen and task.is_other_priority_due_soon() and user in task.assigned_to.all():
                        if task.priority == "medium":
                            message = f"<strong>REMINDER:</strong> <span style='color: green;'> <strong>Medium</strong> </span> priority task '{task.title}' is due on {task.due_date}."
                        else:
                            message = f"<strong>REMINDER:</strong> <span style='color: yellow;'> <strong>Low</strong> </span> priority task '{task.title}' is due on {task.due_date}."
                        notifications.append((message, task.id))

            notifications = sorted(notifications, key=self.key_for_sorting)

            return notifications
        
        return None