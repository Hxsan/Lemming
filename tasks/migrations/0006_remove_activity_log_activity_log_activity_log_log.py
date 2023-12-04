# Generated by Django 4.2.6 on 2023-12-02 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_remove_user_activity_log_activity_log'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity_log',
            name='activity_log',
        ),
        migrations.AddField(
            model_name='activity_log',
            name='log',
            field=models.JSONField(default=list, verbose_name='log'),
        ),
    ]
