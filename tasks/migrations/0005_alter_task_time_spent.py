# Generated by Django 4.2.6 on 2023-12-02 20:05

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_task_time_spent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='time_spent',
            field=models.DurationField(default=datetime.timedelta(0), null=True),
        ),
    ]
