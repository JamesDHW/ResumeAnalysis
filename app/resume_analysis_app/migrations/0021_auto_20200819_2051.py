# Generated by Django 3.0.8 on 2020-08-19 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resume_analysis_app', '0020_auto_20200819_2047'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='needs',
            field=models.TextField(default='{}'),
        ),
        migrations.AddField(
            model_name='account',
            name='values',
            field=models.TextField(default='{}'),
        ),
    ]
