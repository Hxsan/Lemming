# Generated by Django 4.2.6 on 2023-12-14 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0024_delete_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='reminder_days',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
