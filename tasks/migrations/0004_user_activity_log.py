# Generated by Django 4.2.6 on 2023-12-02 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_task_task_completed_alter_task_due_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='activity_log',
            field=models.JSONField(null=True, verbose_name='activity_log'),
        ),
    ]