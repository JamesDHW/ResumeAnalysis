# Generated by Django 3.0.8 on 2020-08-13 12:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resume_analysis_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='organisation',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='account_org', to='resume_analysis_app.Organisation'),
        ),
        migrations.AlterField(
            model_name='jobdescription',
            name='organisation',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='job_org', to='resume_analysis_app.Organisation'),
        ),
    ]