# Generated by Django 5.0 on 2023-12-05 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_task_priority_task_reminder_days'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='reminder_days',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
