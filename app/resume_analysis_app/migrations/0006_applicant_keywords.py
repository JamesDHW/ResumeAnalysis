# Generated by Django 3.0.8 on 2020-08-04 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resume_analysis_app', '0005_auto_20200804_1439'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicant',
            name='keywords',
            field=models.TextField(default=''),
        ),
    ]