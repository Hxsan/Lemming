# Generated by Django 4.2.6 on 2023-12-08 17:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0015_merge_20231208_1711'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='unread_notifications',
        ),
    ]