# Generated by Django 3.0.8 on 2020-07-27 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='installation',
            options={'permissions': (('can_see_advanced_info', 'Can see advanced informations'),)},
        ),
    ]
