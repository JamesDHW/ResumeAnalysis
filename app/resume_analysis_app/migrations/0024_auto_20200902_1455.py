# Generated by Django 3.0.8 on 2020-09-02 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resume_analysis_app', '0023_account_job_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='logo',
            field=models.FileField(default='logos/_.svg', upload_to='logos'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='website',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='account',
            name='job_start',
            field=models.IntegerField(default=0),
        ),
    ]