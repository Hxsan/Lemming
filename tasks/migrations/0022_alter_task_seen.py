# Generated by Django 4.2.6 on 2023-12-11 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0021_task_seen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='seen',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
    ]
