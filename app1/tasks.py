from django_q.tasks import async_task
from django.utils import timezone
from datetime import timedelta
from .models import Task, CustomUser
from django.core.mail import send_mail
from django.conf import settings


def send_task_reminder(task_id):
    try:
        task = Task.objects.get(id=task_id)
        if task.due_date and task.due_date < timezone.now().date() and not task.status:
            subject = f'Overdue Task: {task.title}'
            message = f'''
            Hello {task.assigned_to.full_name},

            This is a reminder that your task "{task.title}" is overdue.

            Project: {task.project.name}
            Due Date: {task.due_date}
            Description: {task.description}

            Please update the task status as soon as possible.

            Best regards,
            Task Management System
            '''

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [task.assigned_to.email],
                fail_silently=False,
            )
    except Task.DoesNotExist:
        pass


def check_overdue_tasks():
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now().date(),
        status=False
    )

    for task in overdue_tasks:
        async_task('app1.tasks.send_task_reminder', str(task.id))


def send_welcome_email(user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        subject = 'Welcome to Task Management System'
        message = f'''
        Hello {user.full_name},

        Welcome to the Task Management System!

        Your account has been successfully created with email: {user.email}

        You can now start managing your projects and tasks.

        Best regards,
        Task Management System
        '''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except CustomUser.DoesNotExist:
        pass


def generate_daily_report(user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        from .models import Projects
        projects = Projects.objects.filter(user=user)

        report_data = {
            'user': user.full_name,
            'date': timezone.now().date(),
            'projects': []
        }

        for project in projects:
            tasks = Task.objects.filter(project=project)
            completed_tasks = tasks.filter(status=True).count()
            pending_tasks = tasks.filter(status=False).count()

            report_data['projects'].append({
                'name': project.name,
                'total_tasks': tasks.count(),
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
            })

        return report_data
    except CustomUser.DoesNotExist:
        return None