# Generated by Django 3.0.8 on 2020-08-15 11:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resume_analysis_app', '0013_jobdescription_aggregate_personality'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='filename',
        ),
        migrations.RemoveField(
            model_name='jobdescription',
            name='current_employees',
        ),
    ]