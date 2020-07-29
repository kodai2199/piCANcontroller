# Generated by Django 3.0.8 on 2020-07-27 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Installation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('installation_code', models.CharField(help_text='CPx Code', max_length=255)),
                ('imei', models.CharField(help_text='IMEI Code', max_length=255, unique=True)),
                ('inlet_pressure', models.IntegerField(blank=True, help_text='Inlet pressure (Bar)', null=True)),
                ('inlet_temperature', models.IntegerField(blank=True, help_text='Inlet temperature (°C)', null=True)),
                ('outlet_pressure', models.IntegerField(blank=True, help_text='Outlet pressure (Bar)', null=True)),
                ('working_hours_counter', models.IntegerField(blank=True, help_text='Total working hours', null=True)),
                ('working_minutes_counter', models.IntegerField(blank=True, help_text='Working minutes', null=True)),
                ('anti_drip', models.BooleanField(blank=True, help_text='Anti-drip', null=True)),
                ('time_limit', models.BooleanField(blank=True, help_text='Daily time limit reached', null=True)),
                ('start_code', models.CharField(blank=True, help_text='Start code', max_length=255, null=True)),
                ('alarm', models.BooleanField(blank=True, help_text='Alarm state', null=True)),
                ('run', models.BooleanField(blank=True, help_text='Running state', null=True)),
            ],
        ),
    ]
